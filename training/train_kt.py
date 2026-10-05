"""
Train and evaluate knowledge-tracing models on GPU.

  # Benchmark the architecture on real student data (ASSISTments, DKVMN splits)
  python training/train_kt.py --dataset assist2009 --model all
  python training/train_kt.py --dataset assist2015 --model all

  # Train the production model on the app curriculum (+ real app logs) and export to ONNX
  python training/train_kt.py --dataset curriculum --model all --export --app-db data/database.db

Results are written to training/results/<dataset>.json; exported artifacts go to
backend/ml/artifacts/ (kt_model.onnx, kt_meta.json, bkt_params.json).
"""
import argparse
import json
import math
import os
import sys
import time
from datetime import datetime

import numpy as np
import torch
import torch.nn.functional as F
from sklearn.metrics import accuracy_score, roc_auc_score

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fit_bkt  # noqa: E402
import kt_data  # noqa: E402
from kt_model import DKT, ExportWrapper, KTTransformer  # noqa: E402

ROOT = kt_data.ROOT
ARTIFACTS = os.path.join(ROOT, 'backend', 'ml', 'artifacts')
RESULTS = os.path.join(ROOT, 'training', 'results')


def set_seed(seed):
    np.random.seed(seed)
    torch.manual_seed(seed)


def tensors(seqs, n_topics, max_len, device):
    T, D, R, G, L = kt_data.to_padded(kt_data.window(seqs, max_len), n_topics, max_len)
    return [torch.as_tensor(x, device=device) for x in (T, D, R, G, L)]


def batches(data, batch_size, shuffle):
    T, D, R, G, L = data
    idx = torch.randperm(len(L), device=L.device) if shuffle else torch.arange(len(L), device=L.device)
    for i in range(0, len(L), batch_size):
        b = idx[i:i + batch_size]
        n = int(L[b].max())
        yield T[b, :n], D[b, :n], R[b, :n], G[b, :n], L[b]


@torch.no_grad()
def evaluate(model, data, batch_size=1024):
    model.eval()
    ys, ps = [], []
    for t, d, r, g, lens in batches(data, batch_size, False):
        with torch.autocast('cuda', dtype=torch.bfloat16):
            logits = model(t, d, r, g)
        mask = torch.arange(t.shape[1] - 1, device=t.device)[None] < (lens[:, None] - 1)
        ys.append(r[:, 1:][mask].float().cpu())
        ps.append(torch.sigmoid(logits.float())[mask].cpu())
    y, p = torch.cat(ys).numpy(), torch.cat(ps).numpy()
    return {'auc': float(roc_auc_score(y, p)), 'acc': float(accuracy_score(y, p > 0.5)), 'n': int(len(y))}


def train_model(kind, meta, train, valid, args):
    cls = KTTransformer if kind == 'transformer' else DKT
    model = cls(meta['n_topics'], meta['n_diff'], kt_data.N_GAP_BUCKETS, max_len=args.max_len,
                d=args.d, layers=args.layers, heads=args.heads, dropout=args.dropout).cuda()
    n_params = sum(p.numel() for p in model.parameters())
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    steps_per_epoch = math.ceil(len(train[4]) / args.batch)
    total = steps_per_epoch * args.epochs
    warmup = max(1, int(0.05 * total))
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: min(1.0, (s + 1) / warmup) * 0.5 * (1 + math.cos(math.pi * min(1.0, s / total))))

    best, best_state, patience, history = -1.0, None, 0, []
    print(f'[{kind}] params={n_params:,} train_seqs={len(train[4]):,} steps/epoch={steps_per_epoch}')
    for epoch in range(args.epochs):
        model.train()
        t0, tot_loss, nb = time.time(), 0.0, 0
        for t, d, r, g, lens in batches(train, args.batch, True):
            with torch.autocast('cuda', dtype=torch.bfloat16):
                logits = model(t, d, r, g)
            mask = torch.arange(t.shape[1] - 1, device=t.device)[None] < (lens[:, None] - 1)
            loss = F.binary_cross_entropy_with_logits(logits.float()[mask], r[:, 1:][mask].float())
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            tot_loss += loss.item()
            nb += 1
        v = evaluate(model, valid)
        history.append({'epoch': epoch + 1, 'loss': tot_loss / nb, 'val_auc': v['auc']})
        print(f'[{kind}] epoch {epoch + 1:2d} loss {tot_loss / nb:.4f} val_auc {v["auc"]:.4f} '
              f'val_acc {v["acc"]:.4f} ({time.time() - t0:.1f}s)')
        if v['auc'] > best + 1e-4:
            best, patience = v['auc'], 0
            best_state = {k: x.detach().clone() for k, x in model.state_dict().items()}
        else:
            patience += 1
            if patience >= args.patience:
                print(f'[{kind}] early stop')
                break
    model.load_state_dict(best_state)
    return model, {'params': n_params, 'best_val_auc': best, 'history': history}


def legacy_v1_baseline(seqs):
    """The original app's heuristic tracker (knowledge += 0.15*w*(1-k) ...), scored by AUC."""
    w = [0.7, 1.0, 1.3]
    ys, ps = [], []
    for s in seqs:
        k = {}
        for t, d, r in zip(s['topic'], s['difficulty'], s['response']):
            cur = k.get(t, 0.0)
            ys.append(r); ps.append(cur)
            wd = w[d] if len(w) > d else 1.0
            cur = min(1.0, cur + 0.15 * wd * (1 - cur)) if r else max(0.0, cur - 0.15 * wd * cur * 0.3)
            k[t] = cur
    return {'auc': float(roc_auc_score(ys, ps)), 'n': len(ys)}


def export_onnx(model, meta, args, metrics):
    os.makedirs(ARTIFACTS, exist_ok=True)
    wrapper = ExportWrapper(model).eval().float().cpu()
    L = 12
    example = (torch.full((1, L), 1, dtype=torch.long), torch.ones((1, L), dtype=torch.long),
               torch.ones((1, L), dtype=torch.long), torch.ones((1, L), dtype=torch.long))
    path = os.path.join(ARTIFACTS, 'kt_model.onnx')
    names = ['topic', 'difficulty', 'response', 'gap']
    torch.onnx.export(wrapper, example, path, input_names=names, output_names=['probs'],
                      dynamic_axes={n: {1: 'seq'} for n in names}, opset_version=18, dynamo=False)

    import onnxruntime as ort
    sess = ort.InferenceSession(path, providers=['CPUExecutionProvider'])
    ref = wrapper(*example).detach().numpy()
    out = sess.run(['probs'], {n: x.numpy() for n, x in zip(names, example)})[0]
    max_err = float(np.abs(ref - out).max())
    print(f'ONNX export ok: {os.path.getsize(path) / 1e6:.2f} MB, max |torch - onnx| = {max_err:.2e}')

    with open(os.path.join(ARTIFACTS, 'kt_meta.json'), 'w') as f:
        json.dump({'topics': meta['topics'], 'difficulties': meta['difficulties'], 'max_len': args.max_len,
                   'gap_edges_hours': kt_data.GAP_EDGES_HOURS, 'architecture': 'KTTransformer',
                   'd_model': args.d, 'layers': args.layers, 'heads': args.heads,
                   'trained_at': datetime.utcnow().isoformat(timespec='seconds'), 'metrics': metrics},
                  f, indent=2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dataset', default='curriculum', choices=['assist2009', 'assist2015', 'curriculum'])
    ap.add_argument('--model', default='all', choices=['transformer', 'dkt', 'all'])
    ap.add_argument('--students', type=int, default=60000)
    ap.add_argument('--app-db', default=None, help='backend SQLite DB to add real interaction logs')
    ap.add_argument('--epochs', type=int, default=30)
    ap.add_argument('--batch', type=int, default=128)
    ap.add_argument('--lr', type=float, default=1e-3)
    ap.add_argument('--weight-decay', type=float, default=0.05)
    ap.add_argument('--d', type=int, default=256)
    ap.add_argument('--layers', type=int, default=4)
    ap.add_argument('--heads', type=int, default=8)
    ap.add_argument('--dropout', type=float, default=0.2)
    ap.add_argument('--max-len', type=int, default=200)
    ap.add_argument('--patience', type=int, default=4)
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--export', action='store_true')
    ap.add_argument('--skip-bkt', action='store_true')
    ap.add_argument('--tag', default='', help='suffix for the results file (sweeps)')
    args = ap.parse_args()

    set_seed(args.seed)
    torch.backends.cuda.matmul.allow_tf32 = True
    print('GPU:', torch.cuda.get_device_name(0))

    t0 = time.time()
    if args.dataset == 'curriculum':
        seqs, slugs = kt_data.simulate_curriculum(args.students, seed=args.seed)
        rng = np.random.default_rng(args.seed)
        order = rng.permutation(len(seqs))
        n_val = n_test = len(seqs) // 10
        test = [seqs[i] for i in order[:n_test]]
        valid = [seqs[i] for i in order[n_test:n_test + n_val]]
        train_s = [seqs[i] for i in order[n_test + n_val:]]
        app_logs = kt_data.export_app_logs(args.app_db, slugs) if args.app_db else []
        train_s += app_logs
        meta = {'n_topics': len(slugs), 'n_diff': 3, 'topics': slugs, 'difficulties': kt_data.DIFFICULTIES}
        print(f'simulated {len(seqs):,} learners, {sum(len(s["topic"]) for s in seqs):,} interactions '
              f'(+{len(app_logs)} real app sequences) in {time.time() - t0:.1f}s')
    else:
        d = kt_data.load_assist(args.dataset)
        train_s, valid, test = d['train'], d['valid'], d['test']
        meta = {k: d[k] for k in ('n_topics', 'n_diff', 'topics', 'difficulties')}
        print(f'{args.dataset}: train {len(train_s)} valid {len(valid)} test {len(test)} learners')

    dev = 'cuda'
    train = tensors(train_s, meta['n_topics'], args.max_len, dev)
    val = tensors(valid, meta['n_topics'], args.max_len, dev)
    tst = tensors(test, meta['n_topics'], args.max_len, dev)

    results = {'dataset': args.dataset, 'config': vars(args), 'models': {}}

    bkt_params = None
    if not args.skip_bkt:
        print('fitting BKT baseline ...')
        tb = time.time()
        scaled = args.dataset == 'curriculum'
        bkt_params = fit_bkt.fit(train_s, meta['n_topics'], scaled=scaled)
        y, p = fit_bkt.predict(test, bkt_params, meta['n_topics'], scaled=scaled)
        results['models']['bkt'] = {'test_auc': float(roc_auc_score(y, p)), 'test_acc': float(accuracy_score(y, p > 0.5)),
                                    'fit_seconds': round(time.time() - tb, 1)}
        print(f'BKT test AUC {results["models"]["bkt"]["test_auc"]:.4f}')
    if args.dataset == 'curriculum':
        y = np.concatenate([s['response'] for s in test])
        p = np.concatenate([s['p_true'] for s in test])
        results['oracle_auc'] = float(roc_auc_score(y, p))
        print(f'oracle AUC (true simulator probabilities = upper bound) {results["oracle_auc"]:.4f}')
        results['models']['legacy_v1_heuristic'] = {'test_auc': legacy_v1_baseline(test)['auc']}
        print(f'legacy v1 heuristic AUC {results["models"]["legacy_v1_heuristic"]["test_auc"]:.4f}')

    kinds = ['dkt', 'transformer'] if args.model == 'all' else [args.model]
    trained = {}
    for kind in kinds:
        tm = time.time()
        model, info = train_model(kind, meta, train, val, args)
        test_m = evaluate(model, tst)
        results['models'][kind] = {'test_auc': test_m['auc'], 'test_acc': test_m['acc'],
                                   'train_seconds': round(time.time() - tm, 1), **info}
        trained[kind] = model
        print(f'[{kind}] TEST AUC {test_m["auc"]:.4f} ACC {test_m["acc"]:.4f}')

    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, f'{args.dataset}{args.tag}.json'), 'w') as f:
        json.dump(results, f, indent=2)

    print('\n=== summary ===')
    for name, m in results['models'].items():
        print(f'{name:22s} test AUC {m["test_auc"]:.4f}')

    if args.export and args.dataset == 'curriculum' and 'transformer' in trained:
        tm = results['models']['transformer']
        export_onnx(trained['transformer'], meta, args,
                    {'val_auc': tm['best_val_auc'], 'test_auc': tm['test_auc'],
                     'bkt_test_auc': results['models'].get('bkt', {}).get('test_auc'),
                     'dkt_test_auc': results['models'].get('dkt', {}).get('test_auc'),
                     'oracle_auc': results.get('oracle_auc')})
        if bkt_params:
            with open(os.path.join(ARTIFACTS, 'bkt_params.json'), 'w') as f:
                json.dump({'topics': {meta['topics'][k]: v for k, v in bkt_params.items()}}, f, indent=2)
        print('artifacts written to', ARTIFACTS)


if __name__ == '__main__':
    main()
