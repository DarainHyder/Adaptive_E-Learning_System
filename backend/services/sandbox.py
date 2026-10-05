"""
Run learner code in a separate, resource-limited Python process.

v1 called exec() inside the web server process with a keyword blocklist, which is trivially
escapable (e.g. via ().__class__.__mro__) and could hang or crash the server. Now:
  - AST policy check: only allow-listed imports, no dunder attribute access, no
    exec/eval/open/compile/__import__ calls
  - separate process: `python -I -S` (isolated mode, no site-packages), empty environment,
    temp working directory
  - kernel-enforced limits: CPU seconds, address space, file size, no forking
  - wall-clock timeout and output truncation
This is defence in depth for an educational playground, not a hardened multi-tenant sandbox;
for hostile workloads, run it inside a container/gVisor/nsjail.
"""
import ast
import os
import subprocess
import sys
import tempfile

ALLOWED_IMPORTS = {
    'math', 'random', 'statistics', 'collections', 'itertools', 'functools', 'operator', 'string',
    're', 'json', 'datetime', 'time', 'heapq', 'bisect', 'dataclasses', 'typing', 'enum',
    'decimal', 'fractions', 'copy', 'pprint', 'textwrap', 'abc',
}
BLOCKED_CALLS = {'exec', 'eval', 'compile', 'open', '__import__', 'globals', 'locals', 'vars',
                 'getattr', 'setattr', 'delattr', 'breakpoint', 'memoryview'}


class PolicyError(Exception):
    pass


def check_policy(code):
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise PolicyError(f'SyntaxError: {exc.msg} (line {exc.lineno})')
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split('.')[0] not in ALLOWED_IMPORTS:
                    raise PolicyError(f"Import of '{alias.name}' is not allowed in the playground")
        elif isinstance(node, ast.ImportFrom):
            if (node.module or '').split('.')[0] not in ALLOWED_IMPORTS:
                raise PolicyError(f"Import from '{node.module}' is not allowed in the playground")
        elif isinstance(node, ast.Attribute) and node.attr.startswith('__'):
            raise PolicyError('Access to dunder attributes is not allowed in the playground')
        elif isinstance(node, ast.Name) and node.id in BLOCKED_CALLS:
            raise PolicyError(f"'{node.id}' is not allowed in the playground")


def _limits(cpu_s, mem_mb):
    def apply():  # runs in the child before exec
        import resource
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_s, cpu_s))
        mem = mem_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
        resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_NOFILE, (32, 32))
        try:
            resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))
        except (ValueError, OSError):
            pass
        os.setsid()
    return apply


def run_code(code, timeout_s=5, memory_mb=256, max_output=10_000, stdin=''):
    """Returns dict(success, output, error)."""
    if len(code) > 20_000:
        return {'success': False, 'output': 'Error: code is too long (20k characters max)', 'error': True}
    try:
        check_policy(code)
    except PolicyError as exc:
        return {'success': False, 'output': f'Error: {exc}', 'error': True}

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, 'main.py')
        with open(path, 'w') as f:
            f.write(code)
        preexec = _limits(timeout_s, memory_mb) if os.name == 'posix' else None
        try:
            proc = subprocess.run(
                [sys.executable, '-I', '-S', path], input=stdin, capture_output=True, text=True,
                timeout=timeout_s + 1, cwd=tmp, env={'PYTHONIOENCODING': 'utf-8'}, preexec_fn=preexec,
            )
        except subprocess.TimeoutExpired:
            return {'success': False, 'output': f'Error: execution timed out after {timeout_s}s', 'error': True}

    out = proc.stdout
    if len(out) > max_output:
        out = out[:max_output] + '\n... (output truncated)'
    if proc.returncode != 0:
        err = proc.stderr.strip().splitlines()
        # show only the last traceback lines, and hide the temp file path
        msg = '\n'.join(err[-3:]).replace(path, 'main.py') if err else f'Process exited with code {proc.returncode}'
        if proc.returncode < 0:
            msg = 'Error: process was killed (CPU or memory limit exceeded)'
        return {'success': False, 'output': (out + '\n' + msg).strip(), 'error': True}
    return {'success': True, 'output': out if out else 'Code executed successfully (no output)', 'error': False}
