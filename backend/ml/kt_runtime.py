"""
CPU inference for the transformer knowledge-tracing model (trained in training/train_kt.py
and exported to ONNX). Given a learner's interaction history it predicts, for every topic
and difficulty, the probability that the *next* answer will be correct.

Uses onnxruntime only (no torch) so the deployed image stays small. If the model or
onnxruntime is unavailable, `available` is False and callers fall back to BKT.
"""
import json
import logging
import os
import threading

import numpy as np

log = logging.getLogger(__name__)

# Hours since previous interaction -> bucket id (0 is reserved for BOS / unknown)
GAP_EDGES_HOURS = [1, 24, 72, 168, 720]


def gap_bucket(hours):
    if hours is None:
        return 0
    for i, edge in enumerate(GAP_EDGES_HOURS):
        if hours < edge:
            return i + 1
    return len(GAP_EDGES_HOURS) + 1


class KTRuntime:
    def __init__(self, artifacts_dir):
        self.artifacts_dir = artifacts_dir
        self._session = None
        self._meta = None
        self._lock = threading.Lock()
        self._loaded = False

    def _load(self):
        with self._lock:
            if self._loaded:
                return
            self._loaded = True
            model_path = os.path.join(self.artifacts_dir, 'kt_model.onnx')
            meta_path = os.path.join(self.artifacts_dir, 'kt_meta.json')
            if not (os.path.exists(model_path) and os.path.exists(meta_path)):
                log.info('KT model artifacts not found; using BKT only')
                return
            try:
                import onnxruntime as ort
                opts = ort.SessionOptions()
                opts.intra_op_num_threads = 1
                opts.inter_op_num_threads = 1
                self._session = ort.InferenceSession(model_path, opts, providers=['CPUExecutionProvider'])
                with open(meta_path) as f:
                    self._meta = json.load(f)
                log.info('Loaded KT model (%s topics, val AUC %.3f)', len(self._meta['topics']),
                         self._meta.get('metrics', {}).get('val_auc', float('nan')))
            except Exception as exc:  # pragma: no cover - defensive
                log.warning('Failed to load KT model: %s', exc)
                self._session = None

    @property
    def available(self):
        self._load()
        return self._session is not None

    @property
    def meta(self):
        self._load()
        return self._meta or {}

    def predict(self, history):
        """
        history: list of dicts {slug, difficulty, correct, timestamp(datetime)} ordered by time.
        returns: {slug: {difficulty: p_correct}} or None if model unavailable.
        """
        if not self.available:
            return None
        meta = self._meta
        topic_index = {s: i for i, s in enumerate(meta['topics'])}
        diff_index = {d: i for i, d in enumerate(meta['difficulties'])}
        max_len = meta['max_len'] - 1  # leave room for BOS

        events = [h for h in history if h['slug'] in topic_index][-max_len:]
        n_topics = len(meta['topics'])
        topics, diffs, resp, gaps = [n_topics], [0], [2], [0]  # BOS token
        prev_ts = None
        for e in events:
            topics.append(topic_index[e['slug']])
            diffs.append(diff_index.get(e['difficulty'], 1))
            resp.append(1 if e['correct'] else 0)
            hours = None if prev_ts is None else (e['timestamp'] - prev_ts).total_seconds() / 3600
            gaps.append(gap_bucket(hours))
            prev_ts = e['timestamp']

        feeds = {
            'topic': np.asarray([topics], dtype=np.int64),
            'difficulty': np.asarray([diffs], dtype=np.int64),
            'response': np.asarray([resp], dtype=np.int64),
            'gap': np.asarray([gaps], dtype=np.int64),
        }
        probs = self._session.run(['probs'], feeds)[0][0]  # [n_topics, n_diff]
        return {
            slug: {d: float(probs[ti, di]) for d, di in diff_index.items()}
            for slug, ti in topic_index.items()
        }
