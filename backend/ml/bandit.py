"""
Contextual Thompson-sampling bandit for teaching-strategy selection.

Arms are teaching strategies (scaffolding, direct_instruction, ...). Context is a coarse
learner bucket (knowledge low/mid/high). Each (bucket, arm) keeps a Beta(alpha, beta)
posterior over "the learner answers the follow-up quiz correctly".

Priors come from the expert knowledge base (effectiveness_score) plus a bonus for the
strategy the pedagogical rules prefer, so cold-start behaviour matches the rule engine
and real learner outcomes progressively take over.
"""
import random

from models import AgentKnowledge, db

PRIOR_STRENGTH = 4.0
RULE_BONUS = 2.0
AGENT_TYPE = 'teaching'
KNOWLEDGE_TYPE = 'bandit_arm'


def context_bucket(knowledge_level):
    if knowledge_level < 0.35:
        return 'low'
    if knowledge_level < 0.7:
        return 'mid'
    return 'high'


class StrategyBandit:
    def __init__(self, strategies, rng=None):
        self.strategies = {s['name']: s for s in strategies}
        self.rng = rng or random.Random()

    def _arm(self, bucket, name, rule_choice=None):
        key = f'{bucket}:{name}'
        row = AgentKnowledge.query.filter_by(agent_type=AGENT_TYPE, knowledge_type=KNOWLEDGE_TYPE, key=key).first()
        if row is None:
            eff = float(self.strategies.get(name, {}).get('effectiveness_score', 0.5))
            alpha = 1 + PRIOR_STRENGTH * eff + (RULE_BONUS if name == rule_choice else 0.0)
            beta = 1 + PRIOR_STRENGTH * (1 - eff)
            row = AgentKnowledge(agent_type=AGENT_TYPE, knowledge_type=KNOWLEDGE_TYPE, key=key,
                                 content={'strategy': name, 'bucket': bucket, 'alpha': alpha, 'beta': beta},
                                 effectiveness_score=alpha / (alpha + beta), usage_count=0)
            db.session.add(row)
        return row

    def select(self, knowledge_level, rule_choice=None):
        bucket = context_bucket(knowledge_level)
        samples = {}
        for name in self.strategies:
            c = self._arm(bucket, name, rule_choice).content
            samples[name] = self.rng.betavariate(c['alpha'], c['beta'])
        db.session.commit()
        best = max(samples, key=samples.get)
        return best, bucket, samples

    def update(self, bucket, name, reward, weight=1.0):
        """reward in [0, 1] (fractional Beta update); weight < 1 for partial evidence."""
        row = self._arm(bucket, name)
        c = dict(row.content)
        c['alpha'] += weight * reward
        c['beta'] += weight * (1 - reward)
        row.content = c
        row.usage_count = (row.usage_count or 0) + 1
        row.effectiveness_score = c['alpha'] / (c['alpha'] + c['beta'])
        db.session.commit()

    def summary(self):
        rows = AgentKnowledge.query.filter_by(agent_type=AGENT_TYPE, knowledge_type=KNOWLEDGE_TYPE).all()
        return [{'bucket': r.content['bucket'], 'strategy': r.content['strategy'],
                 'expected_success': round(r.effectiveness_score, 3), 'pulls': r.usage_count} for r in rows]
