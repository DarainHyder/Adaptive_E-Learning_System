"""Thread-safe per-agent telemetry shown on the dashboard's agent panel."""
import functools
import threading
import time
from collections import deque
from datetime import datetime

AGENTS = ('coordinator', 'knowledge', 'teaching', 'assessment', 'tutor', 'recommendation')


class AgentMetrics:
    def __init__(self):
        self._lock = threading.Lock()
        self._data = {a: {'runs': 0, 'errors': 0, 'total_ms': 0, 'state': 'idle', 'last_run_at': None}
                      for a in AGENTS}
        self._log = deque(maxlen=200)

    def start(self, agent):
        with self._lock:
            self._data[agent]['state'] = 'acting'

    def finish(self, agent, ms, ok=True, note=None):
        with self._lock:
            d = self._data[agent]
            d['runs'] += 1
            d['total_ms'] += ms
            d['errors'] += 0 if ok else 1
            d['state'] = 'completed' if ok else 'error'
            d['last_run_at'] = datetime.utcnow().isoformat(timespec='seconds')
            self._log.append({'agent': agent, 'ms': ms, 'ok': ok, 'note': note, 'at': d['last_run_at']})

    def snapshot(self):
        with self._lock:
            agents = {}
            for name, d in self._data.items():
                agents[name] = {
                    'agent': name,
                    'state': d['state'] if d['runs'] else 'idle',
                    'runs': d['runs'],
                    'errors': d['errors'],
                    'avg_latency_ms': round(d['total_ms'] / d['runs']) if d['runs'] else 0,
                    'last_run_at': d['last_run_at'],
                    'memory_size': sum(1 for e in self._log if e['agent'] == name),
                }
            return agents, list(self._log)[-20:]


METRICS = AgentMetrics()


def tracked(agent, trace=True):
    """Decorator for LangGraph node functions: records latency/errors and (optionally) appends to state.trace."""
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(state, *args, **kwargs):
            METRICS.start(agent)
            t0 = time.perf_counter()
            try:
                update = fn(state, *args, **kwargs) or {}
            except Exception:
                METRICS.finish(agent, int((time.perf_counter() - t0) * 1000), ok=False)
                raise
            ms = int((time.perf_counter() - t0) * 1000)
            METRICS.finish(agent, ms, note=fn.__name__)
            if not trace:
                return update
            update.setdefault('trace', [])
            update['trace'] = list(update['trace']) + [{'agent': agent, 'step': fn.__name__, 'ms': ms}]
            return update
        return wrapper
    return deco
