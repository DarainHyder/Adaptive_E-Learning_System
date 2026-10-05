"""
Bayesian Knowledge Tracing (Corbett & Anderson, 1995) with difficulty-aware guess/slip.

Each topic has four parameters:
  p_init  - P(L0): probability the skill is already known
  p_learn - P(T):  probability of learning on each practice opportunity
  p_guess - P(G):  probability of answering correctly while unmastered
  p_slip  - P(S):  probability of answering incorrectly while mastered

Per-topic parameters are fitted offline (training/fit_bkt.py) and loaded from
ml/artifacts/bkt_params.json. Missing topics fall back to DEFAULT_PARAMS.
"""
import json
import os
from dataclasses import dataclass, asdict

DEFAULT_PARAMS = {'p_init': 0.10, 'p_learn': 0.15, 'p_guess': 0.22, 'p_slip': 0.10}

# Easier questions are easier to guess and harder to slip on; harder ones the opposite.
GUESS_SCALE = {'beginner': 1.3, 'intermediate': 1.0, 'advanced': 0.7}
SLIP_SCALE = {'beginner': 0.7, 'intermediate': 1.0, 'advanced': 1.4}
LEARN_SCALE = {'beginner': 0.8, 'intermediate': 1.0, 'advanced': 1.2}


@dataclass
class BKTParams:
    p_init: float
    p_learn: float
    p_guess: float
    p_slip: float

    def for_difficulty(self, difficulty):
        return BKTParams(
            p_init=self.p_init,
            p_learn=min(0.6, self.p_learn * LEARN_SCALE.get(difficulty, 1.0)),
            p_guess=min(0.45, self.p_guess * GUESS_SCALE.get(difficulty, 1.0)),
            p_slip=min(0.35, self.p_slip * SLIP_SCALE.get(difficulty, 1.0)),
        )


class BKTModel:
    def __init__(self, params_path=None):
        self.params = {}
        if params_path and os.path.exists(params_path):
            with open(params_path) as f:
                raw = json.load(f)
            self.params = {slug: BKTParams(**p) for slug, p in raw.get('topics', raw).items()}

    def get(self, slug):
        return self.params.get(slug) or BKTParams(**DEFAULT_PARAMS)

    def prior(self, slug):
        return self.get(slug).p_init

    def update(self, p_mastery, is_correct, slug, difficulty='intermediate'):
        """One observation -> posterior P(mastered) after the learning transition."""
        p = self.get(slug).for_difficulty(difficulty)
        if is_correct:
            num = p_mastery * (1 - p.p_slip)
            den = num + (1 - p_mastery) * p.p_guess
        else:
            num = p_mastery * p.p_slip
            den = num + (1 - p_mastery) * (1 - p.p_guess)
        posterior = num / den if den > 0 else p_mastery
        return min(0.999, posterior + (1 - posterior) * p.p_learn)

    def p_correct(self, p_mastery, slug, difficulty='intermediate'):
        """Predicted probability of a correct answer at the given difficulty."""
        p = self.get(slug).for_difficulty(difficulty)
        return p_mastery * (1 - p.p_slip) + (1 - p_mastery) * p.p_guess

    def to_json(self):
        return {slug: asdict(p) for slug, p in self.params.items()}
