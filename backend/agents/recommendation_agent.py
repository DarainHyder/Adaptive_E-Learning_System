"""
RecommendationAgent: ranks what to study next from the learner model.

score = readiness gate (prerequisite mastery)        -> don't recommend what can't be learned yet
      + learning potential (1 - effective mastery)
      + "zone of proximal development" bonus (predicted success 50-85%)
      + spaced-repetition urgency (recall below threshold)
      + momentum (already in progress) + goal match + curriculum order tie-break
"""
from models import Topic

from .metrics import tracked


def score_topics(profile, topics, goals=(), exclude_id=None):
    ranked = []
    for t in topics:
        if t.id == exclude_id:
            continue
        p = profile['topics'][t.id]
        eff, ready = p['effective_mastery'], p['readiness']
        pred = p['predicted_success'].get('intermediate', 0.5)
        mastered = eff >= 0.85 and not p['due_for_review']
        score = 0.0
        score += 3.0 * ready - (3.0 if ready < 1.0 else 0.0)
        score += 2.0 * (1 - eff)
        score += 1.0 if 0.5 <= pred <= 0.85 else 0.0
        if p['due_for_review']:
            score += 2.5 * (1 - p['recall'])
        if 0 < p['practice_count'] and eff < 0.85:
            score += 1.0
        if any(g.lower() in (t.name + ' ' + t.category).lower() for g in goals if g):
            score += 2.0
        score -= 0.04 * (t.position or 0)
        if mastered:
            score -= 4.0

        if p['due_for_review']:
            reason = f"Review due: estimated recall has dropped to {p['recall']:.0%}"
        elif ready < 1.0:
            reason = 'Build prerequisites first'
        elif p['practice_count'] == 0:
            reason = 'You are ready for this new topic'
        elif eff < 0.5:
            reason = 'Continue building on your progress'
        elif eff < 0.85:
            reason = 'Almost there, finish mastering this'
        else:
            reason = 'Mastered: optional refresher'
        ranked.append({
            'topic_id': t.id, 'name': t.name, 'category': t.category, 'difficulty': t.difficulty,
            'description': t.description, 'current_knowledge': round(eff, 3), 'readiness': ready,
            'predicted_success': round(pred, 3), 'score': round(score, 3), 'reason': reason,
            'priority': 'high' if score >= 4 else ('medium' if score >= 2 else 'low'),
        })
    ranked.sort(key=lambda r: r['score'], reverse=True)
    return ranked


def learning_path(profile, topics, target_id, threshold=0.6):
    """Prerequisite-ordered path (DFS topological order) of unmastered topics leading to target."""
    by_id = {t.id: t for t in topics}
    path, seen = [], set()

    def visit(tid):
        if tid in seen or tid not in by_id:
            return
        seen.add(tid)
        for p in by_id[tid].prerequisite_ids:
            visit(p)
        eff = profile['topics'][tid]['effective_mastery']
        if eff < threshold or tid == target_id:
            t = by_id[tid]
            hours = {'beginner': 3, 'intermediate': 5, 'advanced': 8}.get(t.difficulty, 5) * (1 - eff)
            path.append({'topic_id': tid, 'name': t.name, 'difficulty': t.difficulty,
                         'current_knowledge': round(eff, 3), 'estimated_hours': round(hours, 1)})

    visit(target_id)
    return {'target_topic_id': target_id, 'path': path, 'total_topics': len(path),
            'estimated_total_hours': round(sum(p['estimated_hours'] for p in path), 1)}


def make_nodes(ctx):
    @tracked('recommendation')
    def recommend(state):
        req = state.get('request', {})
        topics = Topic.query.order_by(Topic.position, Topic.id).all()
        ranked = score_topics(state['profile'], topics, goals=req.get('goals') or [],
                              exclude_id=req.get('current_topic_id'))
        strategy = 'foundation_building' if state['profile']['topics_started'] < 3 else 'balanced_growth'
        update = {'recommendations': {'recommendations': ranked[:5], 'next_best': ranked[0] if ranked else None,
                                      'strategy': strategy, 'agent': 'RecommendationAgent'}}
        if state.get('task') == 'full_learning_session' and not state.get('topic_id') and ranked:
            update['topic_id'] = ranked[0]['topic_id']
        return update

    return {'recommend': recommend}
