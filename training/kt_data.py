"""
Datasets for knowledge tracing.

1. ASSISTments 2009 / 2015 (real student data, standard DKVMN train/test splits), used to
   benchmark the architecture against published baselines.
2. A curriculum-aligned learner simulator that generates interaction logs over the app's own
   20-topic prerequisite graph, so the deployed model speaks the app's topic vocabulary.
3. Real app logs exported from the backend database (QuizAttempt), appended to (2) when
   available so the deployed model improves as people use the app.

Every dataset is returned as a list of sequences; a sequence is a dict of equal-length
int arrays: topic, difficulty, response (0/1), gap (time-gap bucket).
"""
import json
import os
import sqlite3
import urllib.request
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(ROOT, 'training', 'data_cache')
CURRICULUM_PATH = os.path.join(ROOT, 'backend', 'curriculum', 'curriculum.json')
DIFFICULTIES = ['beginner', 'intermediate', 'advanced']
GAP_EDGES_HOURS = [1, 24, 72, 168, 720]  # must match backend/ml/kt_runtime.py
N_GAP_BUCKETS = len(GAP_EDGES_HOURS) + 2

DKVMN_URL = 'https://raw.githubusercontent.com/jennyzhang0215/DKVMN/master/data/{name}/{file}'
ASSIST_FILES = {
    'assist2009': ('assist2009_updated', 'assist2009_updated_train{}.csv', 'assist2009_updated_test.csv', 110),
    'assist2015': ('assist2015', 'assist2015_train{}.csv', 'assist2015_test.csv', 100),
}


def gap_bucket(hours):
    if hours is None:
        return 0
    for i, edge in enumerate(GAP_EDGES_HOURS):
        if hours < edge:
            return i + 1
    return len(GAP_EDGES_HOURS) + 1


# ---------------------------------------------------------------- ASSISTments

def _download(name, file):
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, file)
    if not os.path.exists(path):
        urllib.request.urlretrieve(DKVMN_URL.format(name=name, file=file), path)
    return path


def _read_dkvmn(path):
    """DKVMN format: 3 lines per student: length, skill ids (1-based), responses."""
    seqs = []
    with open(path) as f:
        lines = [l.strip().rstrip(',') for l in f if l.strip()]
    for i in range(0, len(lines) - 2, 3):
        q = np.array([int(x) for x in lines[i + 1].split(',') if x != ''], dtype=np.int64) - 1
        r = np.array([int(x) for x in lines[i + 2].split(',') if x != ''], dtype=np.int64)
        n = min(len(q), len(r))
        if n < 2:
            continue
        seqs.append({'topic': q[:n], 'difficulty': np.zeros(n, np.int64), 'response': r[:n],
                     'gap': np.zeros(n, np.int64)})
    return seqs


def load_assist(dataset, fold=1):
    name, train_tpl, test_file, n_skills = ASSIST_FILES[dataset]
    train = _read_dkvmn(_download(name, train_tpl.format(fold)))
    valid = _read_dkvmn(_download(name, train_tpl.replace('train', 'valid').format(fold)))
    test = _read_dkvmn(_download(name, test_file))
    return {'train': train, 'valid': valid, 'test': test, 'n_topics': n_skills, 'n_diff': 1,
            'topics': [str(i) for i in range(n_skills)], 'difficulties': ['all']}


# ---------------------------------------------------------------- Simulator

def load_curriculum():
    with open(CURRICULUM_PATH) as f:
        topics = json.load(f)['topics']
    slugs = [t['slug'] for t in topics]
    idx = {s: i for i, s in enumerate(slugs)}
    prereqs = [[idx[p] for p in t['prerequisites']] for t in topics]
    level = np.array([DIFFICULTIES.index(t['difficulty']) for t in topics])
    cats = sorted({t['category'] for t in topics})
    cat = np.array([cats.index(t['category']) for t in topics])
    return slugs, prereqs, level, cat, len(cats)


def _sigmoid(x):
    return 1 / (1 + np.exp(-x))


GUESS = np.array([0.30, 0.22, 0.15])
SLIP = np.array([0.05, 0.08, 0.13])


def simulate_student(seed, curriculum):
    """
    Generative learner model:
      - latent general ability theta, learning speed, per-category aptitude
      - latent mastery per topic, gated by prerequisite readiness
      - IRT-style response probability with difficulty-dependent guess/slip
      - learning is strongest in the zone of proximal development (p ~ 0.5-0.85)
      - exponential forgetting between sessions with stability that grows with success
    """
    slugs, prereqs, level, cat, n_cats = curriculum
    rng = np.random.default_rng(seed)
    K = len(slugs)
    theta = rng.normal()
    speed = np.exp(rng.normal(0, 0.35))
    apt = rng.normal(0, 0.5, n_cats)[cat]
    exposed = rng.random(K) < 0.35
    m = np.where(exposed, 0.6 * _sigmoid(1.2 * (theta + apt) - 1.0 - level) * rng.random(K), 0.0)
    stab = np.ones(K)
    last_seen = np.full(K, -np.inf)
    practiced = np.zeros(K, bool)

    t_hours = 0.0
    topics, diffs, resps, gaps, p_true = [], [], [], [], []
    prev_t = None
    n_sessions = 2 + rng.poisson(9)
    for _ in range(n_sessions):
        # time passes between sessions
        gap_days = rng.exponential(2.5) if rng.random() > 0.1 else rng.uniform(10, 60)
        t_hours += gap_days * 24

        readiness = np.array([m[p].mean() if p else 1.0 for p in prereqs])
        u = rng.random()
        if u < 0.65:  # curriculum-following
            open_ = (readiness >= 0.5) & (m < 0.85)
            cand = np.flatnonzero(open_) if open_.any() else np.arange(K)
            w = np.exp(-0.35 * cand + 0.8 * (m[cand] > 0))
            k = rng.choice(cand, p=w / w.sum())
        elif u < 0.85 and practiced.any():  # review something already studied
            k = rng.choice(np.flatnonzero(practiced))
        else:  # explore / jump ahead
            k = rng.integers(K)
        practiced[k] = True

        # forgetting since last time this topic was practiced
        if np.isfinite(last_seen[k]):
            days = (t_hours - last_seen[k]) / 24
            m[k] *= 0.35 + 0.65 * np.exp(-days / stab[k])

        n_q = rng.integers(3, 11)
        n_correct = 0
        for _q in range(n_q):
            # app-like adaptive difficulty with noise
            target = 0 if m[k] < 0.35 else (1 if m[k] < 0.7 else 2)
            d = int(np.clip(target + rng.choice([-1, 0, 0, 0, 1]), 0, 2))
            z = 4.0 * m[k] - 2.0 + 0.6 * theta + 0.4 * apt[k] - 0.9 * (d - 1) - 0.8 * (1 - readiness[k])
            p = GUESS[d] + (1 - GUESS[d] - SLIP[d]) * _sigmoid(1.7 * z)
            correct = rng.random() < p
            n_correct += correct

            zpd = 0.4 + 0.6 * np.exp(-((p - 0.7) / 0.25) ** 2)
            gain = speed * 0.09 * (0.3 + 0.7 * readiness[k]) * zpd * (1.15 if correct else 0.85) * (0.9 + 0.15 * d)
            m[k] = min(1.0, m[k] + gain * (1 - m[k]))

            hours = None if prev_t is None else t_hours - prev_t
            topics.append(k); diffs.append(d); resps.append(int(correct)); gaps.append(gap_bucket(hours))
            p_true.append(p)
            prev_t = t_hours
            t_hours += rng.uniform(0.5, 3) / 60  # minutes between questions

        stab[k] *= 1.6 if n_correct / n_q > 0.6 else 1.1
        last_seen[k] = t_hours

    return {'topic': np.array(topics, np.int64), 'difficulty': np.array(diffs, np.int64),
            'response': np.array(resps, np.int64), 'gap': np.array(gaps, np.int64),
            'p_true': np.array(p_true, np.float32)}  # ground-truth P(correct), for the oracle AUC only


def _sim_chunk(args):
    seeds, curriculum = args
    return [simulate_student(s, curriculum) for s in seeds]


def simulate_curriculum(n_students=60000, seed=0, workers=None):
    curriculum = load_curriculum()
    seeds = list(range(seed, seed + n_students))
    workers = workers or max(1, (os.cpu_count() or 2) - 2)
    chunks = [(seeds[i::workers], curriculum) for i in range(workers)]
    with ProcessPoolExecutor(workers) as ex:
        out = [s for part in ex.map(_sim_chunk, chunks) for s in part]
    return out, curriculum[0]


# ---------------------------------------------------------------- App logs

def export_app_logs(db_path, slugs):
    """Read QuizAttempt rows from the backend SQLite DB into sequences."""
    if not os.path.exists(db_path):
        return []
    idx = {s: i for i, s in enumerate(slugs)}
    con = sqlite3.connect(db_path)
    rows = con.execute(
        'SELECT q.user_id, t.slug, q.difficulty, q.is_correct, q.created_at '
        'FROM quiz_attempt q JOIN topic t ON t.id = q.topic_id ORDER BY q.user_id, q.created_at'
    ).fetchall()
    con.close()
    seqs, cur_user, cur, prev = [], None, None, None
    for user_id, slug, diff, correct, created in rows:
        if slug not in idx:
            continue
        if user_id != cur_user:
            if cur and len(cur['topic']) >= 2:
                seqs.append({k: np.array(v, np.int64) for k, v in cur.items()})
            cur_user, cur, prev = user_id, {'topic': [], 'difficulty': [], 'response': [], 'gap': []}, None
        ts = datetime.fromisoformat(str(created))
        hours = None if prev is None else (ts - prev).total_seconds() / 3600
        cur['topic'].append(idx[slug])
        cur['difficulty'].append(DIFFICULTIES.index(diff) if diff in DIFFICULTIES else 1)
        cur['response'].append(int(bool(correct)))
        cur['gap'].append(gap_bucket(hours))
        prev = ts
    if cur and len(cur['topic']) >= 2:
        seqs.append({k: np.array(v, np.int64) for k, v in cur.items()})
    return seqs


# ---------------------------------------------------------------- Batching

def window(seqs, max_len):
    """Split long sequences into chunks of max_len-1 interactions (a BOS token is prepended later)."""
    out = []
    step = max_len - 1
    for s in seqs:
        n = len(s['topic'])
        for i in range(0, n, step):
            chunk = {k: v[i:i + step] for k, v in s.items()}
            if len(chunk['topic']) >= 2 or (i == 0 and len(chunk['topic']) >= 1):
                out.append(chunk)
    return out


def to_padded(seqs, n_topics, max_len):
    """Prepend BOS (topic=n_topics, response=2) and right-pad into [N, max_len] arrays."""
    N = len(seqs)
    T = np.full((N, max_len), n_topics, np.int64)
    D = np.zeros((N, max_len), np.int64)
    R = np.full((N, max_len), 2, np.int64)
    G = np.zeros((N, max_len), np.int64)
    L = np.zeros(N, np.int64)
    for i, s in enumerate(seqs):
        n = min(len(s['topic']), max_len - 1)
        T[i, 1:n + 1] = s['topic'][:n]
        D[i, 1:n + 1] = s['difficulty'][:n]
        R[i, 1:n + 1] = s['response'][:n]
        G[i, 1:n + 1] = s['gap'][:n]
        L[i] = n + 1
    return T, D, R, G, L
