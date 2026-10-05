from datetime import datetime, timedelta

from agents.assessment_agent import allocate
from ml import memory
from ml.bkt import BKTModel
from services.sandbox import run_code


def test_bkt_moves_in_the_right_direction():
    bkt = BKTModel()
    p = 0.3
    assert bkt.update(p, True, 'x') > p
    assert bkt.update(p, False, 'x') < bkt.update(p, True, 'x')
    # A correct answer on an advanced question is stronger evidence than on a beginner one.
    assert bkt.update(p, True, 'x', 'advanced') > bkt.update(p, True, 'x', 'beginner')
    assert bkt.p_correct(0.9, 'x', 'beginner') > bkt.p_correct(0.9, 'x', 'advanced')


def test_forgetting_curve():
    now = datetime.utcnow()
    fresh = memory.recall_probability(now, 5, 5, 0.8, now)
    old = memory.recall_probability(now - timedelta(days=30), 5, 5, 0.8, now)
    weak = memory.recall_probability(now - timedelta(days=30), 1, 1, 0.3, now)
    assert fresh == 1.0 and 0 < weak < old < 1
    assert memory.effective_mastery(0.8, 0.0) > 0  # forgotten material is not zero


def test_allocate():
    assert allocate({'a': 1, 'b': 1, 'c': 2}, 4) == {'a': 1, 'b': 1, 'c': 2}
    assert sum(allocate({'a': 0.3, 'b': 0.3, 'c': 0.4}, 5).values()) == 5


def test_kt_runtime_predicts(app):
    kt = app.extensions['elearn'].knowledge.kt
    if not kt.available:  # artifacts are optional
        return
    now = datetime.utcnow()
    hist_good = [{'slug': 'python-basics', 'difficulty': 'intermediate', 'correct': True,
                  'timestamp': now + timedelta(minutes=i)} for i in range(8)]
    hist_bad = [dict(h, correct=False) for h in hist_good]
    good, bad = kt.predict(hist_good), kt.predict(hist_bad)
    assert good['python-basics']['intermediate'] > bad['python-basics']['intermediate']
    assert good['python-basics']['beginner'] > good['python-basics']['advanced']


def test_sandbox():
    assert run_code('print(2 + 2)')['output'] == '4\n'
    assert run_code('import math\nprint(math.sqrt(16))')['success']
    assert not run_code('import subprocess')['success']
    assert not run_code('open("/etc/passwd").read()')['success']
    assert not run_code("[].__class__.__base__.__subclasses__()")['success']
    assert 'timed out' in run_code('while True:\n    pass', timeout_s=1)['output'] or \
           'killed' in run_code('while True:\n    pass', timeout_s=1)['output']
    assert 'ZeroDivisionError' in run_code('1/0')['output']
