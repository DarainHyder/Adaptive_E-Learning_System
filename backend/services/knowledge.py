"""
Learner modelling: combines
  - BKT (online, interpretable mastery per topic, persisted in KnowledgeState),
  - the forgetting model (effective mastery + spaced-repetition review queue, computed at read time),
  - the transformer KT model (predicted P(correct) for every topic x difficulty, from full history).
"""
import os
from datetime import datetime

from config import Config
from ml import memory
from ml.bkt import BKTModel
from ml.kt_runtime import KTRuntime
from models import KnowledgeState, QuizAttempt, Topic, db

HISTORY_LIMIT = 400


class KnowledgeService:
    def __init__(self, artifacts_dir=None):
        artifacts_dir = artifacts_dir or Config.ML_ARTIFACTS_DIR
        self.bkt = BKTModel(os.path.join(artifacts_dir, 'bkt_params.json'))
        self.kt = KTRuntime(artifacts_dir)

    # ------------------------------------------------------------------ writes

    def get_or_create_state(self, user_id, topic):
        state = KnowledgeState.query.filter_by(user_id=user_id, topic_id=topic.id).first()
        if state is None:
            state = KnowledgeState(user_id=user_id, topic_id=topic.id,
                                   knowledge_level=self.bkt.prior(topic.slug), confidence=0.0,
                                   practice_count=0, correct_count=0)
            db.session.add(state)
            db.session.flush()
        return state

    def record_answer(self, user_id, topic, is_correct, difficulty):
        state = self.get_or_create_state(user_id, topic)
        now = datetime.utcnow()
        # Apply forgetting since last practice before the Bayesian update (not persisted between reads).
        if state.practice_count:
            recall = memory.recall_probability(state.last_practiced, state.practice_count,
                                               state.correct_count, state.knowledge_level, now)
            prior = memory.effective_mastery(state.knowledge_level, recall)
        else:
            prior = state.knowledge_level if state.knowledge_level is not None else self.bkt.prior(topic.slug)
        state.knowledge_level = self.bkt.update(prior, is_correct, topic.slug, difficulty)
        state.practice_count = (state.practice_count or 0) + 1
        state.correct_count = (state.correct_count or 0) + (1 if is_correct else 0)
        state.confidence = round(1 - 0.85 ** state.practice_count, 4)
        state.last_practiced = now
        return state

    # ------------------------------------------------------------------ reads

    def history(self, user_id, topics_by_id):
        rows = (QuizAttempt.query.filter_by(user_id=user_id)
                .order_by(QuizAttempt.created_at.desc()).limit(HISTORY_LIMIT).all())
        rows.reverse()
        return [{'slug': topics_by_id[r.topic_id].slug, 'difficulty': r.difficulty or 'intermediate',
                 'correct': bool(r.is_correct), 'timestamp': r.created_at}
                for r in rows if r.topic_id in topics_by_id]

    def profile(self, user_id, topics=None):
        topics = topics or Topic.query.order_by(Topic.position, Topic.id).all()
        by_id = {t.id: t for t in topics}
        states = {s.topic_id: s for s in KnowledgeState.query.filter_by(user_id=user_id).all()}
        predictions = self.kt.predict(self.history(user_id, by_id)) if self.kt.available else None
        now = datetime.utcnow()

        per_topic = {}
        for t in topics:
            s = states.get(t.id)
            mastery = s.knowledge_level if s else 0.0
            practice = s.practice_count if s else 0
            correct = (s.correct_count or 0) if s else 0
            recall = memory.recall_probability(s.last_practiced, practice, correct, mastery, now) if s else 1.0
            eff = memory.effective_mastery(mastery, recall) if practice else mastery
            if predictions and t.slug in predictions:
                pred = predictions[t.slug]
            else:
                pred = {d: self.bkt.p_correct(eff if practice else self.bkt.prior(t.slug), t.slug, d)
                        for d in Config.DIFFICULTY_LEVELS}
            per_topic[t.id] = {
                'topic_id': t.id,
                'slug': t.slug,
                'name': t.name,
                'mastery': round(mastery, 4),
                'effective_mastery': round(eff, 4),
                'recall': round(recall, 4),
                'confidence': round(s.confidence or 0.0, 4) if s else 0.0,
                'practice_count': practice,
                'accuracy': round(correct / practice, 3) if practice else None,
                'last_practiced': s.last_practiced.isoformat() if s and s.last_practiced else None,
                'due_for_review': bool(practice and mastery > 0.4 and recall < memory.REVIEW_RECALL_THRESHOLD),
                'days_until_review': round(memory.days_until_review(practice, correct, mastery), 1) if practice else None,
                'predicted_success': {d: round(p, 4) for d, p in pred.items()},
            }

        for t in topics:
            prereq_masteries = [per_topic[p]['effective_mastery'] for p in t.prerequisite_ids if p in per_topic]
            readiness = min(1.0, min(prereq_masteries) / Config.PREREQ_READY_THRESHOLD) if prereq_masteries else 1.0
            per_topic[t.id]['readiness'] = round(readiness, 3)

        started = [v for v in per_topic.values() if v['practice_count']]
        review_queue = sorted((v for v in started if v['due_for_review']), key=lambda v: v['recall'])
        return {
            'user_id': user_id,
            'model': 'transformer-kt + bkt' if predictions else 'bkt',
            'topics': per_topic,
            'average_knowledge': round(sum(v['effective_mastery'] for v in started) / len(started), 4) if started else 0.0,
            'weak_topics': [v for v in sorted(started, key=lambda v: v['effective_mastery'])
                            if v['effective_mastery'] < 0.5][:5],
            'strong_topics': [v for v in sorted(started, key=lambda v: -v['effective_mastery'])
                              if v['effective_mastery'] >= Config.MASTERY_THRESHOLD][:5],
            'review_queue': review_queue,
            'topics_started': len(started),
        }
