"""
Per-topic Bayesian Knowledge Tracing fitted by exhaustive grid search on GPU.

For every topic all candidate parameter combinations are evaluated in parallel
([combos x sequences] tensors), maximising the log-likelihood of observed responses.
Difficulty scaling of guess/slip/learn matches backend/ml/bkt.py exactly, so the fitted
parameters can be used directly at runtime.
"""
import itertools

import numpy as np
import torch

# Must stay in sync with backend/ml/bkt.py
GUESS_SCALE = [1.3, 1.0, 0.7]
SLIP_SCALE = [0.7, 1.0, 1.4]
LEARN_SCALE = [0.8, 1.0, 1.2]

GRID = {
    'p_init': [0.02, 0.05, 0.1, 0.2, 0.3, 0.45, 0.6, 0.8],
    'p_learn': [0.02, 0.05, 0.08, 0.12, 0.18, 0.25, 0.35, 0.5],
    'p_guess': [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35],
    'p_slip': [0.03, 0.06, 0.1, 0.14, 0.18, 0.24, 0.3],
}


def _per_topic(seqs, n_topics, max_steps=150, max_seqs=30000, seed=0):
    """Group each learner's interactions by topic -> padded [S, T] tensors per topic."""
    rng = np.random.default_rng(seed)
    buckets = [[] for _ in range(n_topics)]
    for s in seqs:
        for k in np.unique(s['topic']):
            m = s['topic'] == k
            buckets[k].append((s['response'][m][:max_steps], s['difficulty'][m][:max_steps]))
    out = []
    for k, b in enumerate(buckets):
        if len(b) > max_seqs:
            b = [b[i] for i in rng.choice(len(b), max_seqs, replace=False)]
        if not b:
            out.append(None)
            continue
        T = max(len(r) for r, _ in b)
        R = np.zeros((len(b), T), np.float32)
        D = np.ones((len(b), T), np.int64)
        M = np.zeros((len(b), T), np.float32)
        for i, (r, d) in enumerate(b):
            R[i, :len(r)] = r
            D[i, :len(d)] = d
            M[i, :len(r)] = 1
        out.append((R, D, M))
    return out


def _forward(params, R, D, M, scaled, keep_preds=False):
    """params: [C,4]; R,D,M: [S,T]. Returns per-step p(correct) [C,S,T] and log-lik [C]."""
    dev = params.device
    gs = torch.tensor(GUESS_SCALE, device=dev)[D] if scaled else torch.ones_like(R)
    ss = torch.tensor(SLIP_SCALE, device=dev)[D] if scaled else torch.ones_like(R)
    ls = torch.tensor(LEARN_SCALE, device=dev)[D] if scaled else torch.ones_like(R)
    C, (S, T) = params.shape[0], R.shape
    L = params[:, 0:1].expand(C, S).clone()
    ll = torch.zeros(C, device=dev)
    preds = torch.empty(C, S, T, device=dev) if keep_preds else None
    for t in range(T):
        g = (params[:, 2:3] * gs[None, :, t]).clamp(max=0.45)
        s = (params[:, 3:4] * ss[None, :, t]).clamp(max=0.35)
        tr = (params[:, 1:2] * ls[None, :, t]).clamp(max=0.6)
        p = (L * (1 - s) + (1 - L) * g).clamp(1e-6, 1 - 1e-6)
        if keep_preds:
            preds[:, :, t] = p
        r, m = R[None, :, t], M[None, :, t]
        ll += (m * (r * p.log() + (1 - r) * (1 - p).log())).sum(1)
        post = torch.where(r > 0, L * (1 - s) / p, L * s / (1 - p))
        new_L = (post + (1 - post) * tr).clamp(1e-5, 1 - 1e-5)
        L = torch.where(m > 0, new_L, L)
    return preds, ll


def fit(train_seqs, n_topics, device='cuda', scaled=True):
    combos = torch.tensor(list(itertools.product(*GRID.values())), dtype=torch.float32, device=device)
    combos = combos[combos[:, 2] + combos[:, 3] < 0.6]  # identifiability: guess + slip < 0.6
    params = {}
    for k, data in enumerate(_per_topic(train_seqs, n_topics)):
        if data is None:
            continue
        R, D, M = (torch.as_tensor(x, device=device) for x in data)
        best_ll, best = -float('inf'), None
        for chunk in combos.split(max(1, int(4e8 // (R.shape[0] + 1)))):
            _, ll = _forward(chunk, R, D, M, scaled)
            i = int(ll.argmax())
            if ll[i] > best_ll:
                best_ll, best = float(ll[i]), chunk[i].tolist()
        params[k] = dict(zip(GRID.keys(), [round(v, 4) for v in best]))
    return params


def predict(seqs, params, n_topics, device='cuda', scaled=True):
    """Returns (y_true, y_score) over all interactions, BKT run independently per topic."""
    ys, ps = [], []
    for k, data in enumerate(_per_topic(seqs, n_topics, max_steps=10_000, max_seqs=10 ** 9)):
        if data is None or k not in params:
            continue
        R, D, M = (torch.as_tensor(x, device=device) for x in data)
        p = torch.tensor([list(params[k].values())], device=device)
        preds, _ = _forward(p, R, D, M, scaled, keep_preds=True)
        m = M > 0
        ys.append(R[m].cpu().numpy())
        ps.append(preds[0][m].cpu().numpy())
    return np.concatenate(ys), np.concatenate(ps)
