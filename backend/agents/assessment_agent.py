"""
AssessmentAgent
  decide (plan_quiz):   choose quiz length and difficulty mix so predicted success ~= target
                        ("desirable difficulty"), using the KT model's per-difficulty predictions
  act (assemble_quiz):  draw questions from the bank (no LLM), preferring unseen, well-calibrated items
  generate_questions:   only when the bank runs short: ONE structured LLM call, validated + deduplicated,
                        then loop back to assemble (a LangGraph cycle, max 2 rounds)
  finalize_quiz:        top-up from already-seen items if still short, then build the payload
"""
import math
import random

from langchain_core.messages import HumanMessage, SystemMessage

from models import QuestionBank, Topic, db
from services import content

from .metrics import tracked
from .schemas import Quiz

MAX_GENERATION_ROUNDS = 2
EXTRA_QUESTIONS = 3  # grow the bank a little beyond the immediate shortfall


def allocate(weights, n):
    """Largest-remainder allocation of n slots proportional to weights."""
    total = sum(weights.values()) or 1.0
    raw = {k: n * w / total for k, w in weights.items()}
    alloc = {k: int(math.floor(v)) for k, v in raw.items()}
    for k in sorted(raw, key=lambda k: raw[k] - alloc[k], reverse=True)[: n - sum(alloc.values())]:
        alloc[k] += 1
    return alloc


def make_nodes(ctx):
    cfg = ctx.config

    @tracked('assessment')
    def plan_quiz(state):
        tp = state['profile']['topics'].get(state['topic_id'], {})
        pred = tp.get('predicted_success') or {'beginner': 0.7, 'intermediate': 0.55, 'advanced': 0.4}
        practice = tp.get('practice_count', 0)
        n = cfg.QUIZ_SIZE_MIN if practice < 5 else (cfg.QUIZ_SIZE_MAX if tp.get('effective_mastery', 0) > 0.7 else 5)
        target = cfg.TARGET_SUCCESS_RATE
        # Relative weighting: the difficulty whose predicted success is closest to the target dominates,
        # even when every level is far from it (e.g. a brand-new learner).
        closest = min(abs(p - target) for p in pred.values())
        weights = {d: math.exp(-(abs(p - target) - closest) / 0.07) for d, p in pred.items()}
        mix = allocate(weights, n)
        expected = sum(pred[d] * c for d, c in mix.items()) / n
        return {'quiz_plan': {'num_questions': n, 'difficulty_mix': mix, 'target_success': target,
                              'expected_success': round(expected, 3), 'predicted_success': pred},
                'generation_rounds': state.get('generation_rounds', 0)}

    @tracked('assessment')
    def assemble_quiz(state):
        plan = state['quiz_plan']
        rows, shortfall = content.pick_questions(state['user_id'], state['topic_id'], plan['difficulty_mix'],
                                                 target_p=plan['target_success'])
        return {'quiz': {'question_ids': [q.id for q in rows], 'shortfall': shortfall}}

    def _generation_prompt(topic, shortfall, profile):
        existing = [q.question for q in QuestionBank.query.filter_by(topic_id=topic.id).limit(40)]
        weak = [w['name'] for w in profile.get('weak_topics', [])][:3]
        templates = '\n'.join(f"- {t['id']} ({t['cognitive_level']}): {t['pattern'].splitlines()[0]}"
                              for t in ctx.question_templates)
        wanted = ', '.join(f'{c} {d}' for d, c in shortfall.items())
        total = sum(shortfall.values()) + EXTRA_QUESTIONS
        return [
            SystemMessage('You are an assessment designer who writes unambiguous multiple-choice questions '
                          'with exactly one correct answer and plausible distractors based on common misconceptions.'),
            HumanMessage(
                f"Write {total} multiple-choice questions on '{topic.name}': {topic.description}\n"
                f"Difficulty counts needed: {wanted} (put the {EXTRA_QUESTIONS} extra at intermediate).\n"
                f"Cover these concepts, spreading questions across them: {', '.join(topic.key_concepts or [])}.\n"
                f"Vary question types using these templates:\n{templates}\n"
                f"The learner is currently weak in: {', '.join(weak) or 'n/a'}.\n"
                f"Do NOT repeat or paraphrase any of these existing questions:\n"
                + '\n'.join(f'- {q}' for q in existing[:30])
                + '\nRandomise which letter is correct. Keep code snippets short and put them inside the question text.'
            ),
        ]

    @tracked('assessment')
    def generate_questions(state):
        topic = db.session.get(Topic, state['topic_id'])
        rounds = state.get('generation_rounds', 0) + 1
        result = ctx.llm.structured(Quiz, _generation_prompt(topic, state['quiz']['shortfall'], state['profile']))
        if result is None:
            return {'generation_rounds': MAX_GENERATION_ROUNDS, 'errors': ['question_generation_failed']}
        added = content.add_questions(topic.id, [q.model_dump() for q in result.questions], source='llm')
        return {'generation_rounds': rounds if added else MAX_GENERATION_ROUNDS}

    @tracked('assessment')
    def finalize_quiz(state):
        plan, quiz = state['quiz_plan'], state['quiz']
        ids = list(quiz['question_ids'])
        missing = plan['num_questions'] - len(ids)
        if missing > 0:
            ids += [q.id for q in content.fill_from_any(state['user_id'], state['topic_id'], set(ids), missing)]
        rows = {q.id: q for q in QuestionBank.query.filter(QuestionBank.id.in_(ids)).all()} if ids else {}
        ordered = [rows[i] for i in ids if i in rows]
        order = {'beginner': 0, 'intermediate': 1, 'advanced': 2}
        ordered.sort(key=lambda q: (order.get(q.difficulty, 1), random.random()))  # warm-up first
        for q in ordered:
            q.times_served = (q.times_served or 0) + 1
        return {'quiz': {'questions': [q.to_public_dict() for q in ordered],
                         'metadata': {**plan, 'from_bank': len(quiz['question_ids']),
                                      'generation_rounds': state.get('generation_rounds', 0)}}}

    def route_after_assemble(state):
        short = state['quiz'].get('shortfall')
        if short and ctx.llm.available and state.get('generation_rounds', 0) < MAX_GENERATION_ROUNDS:
            return 'generate_questions'
        return 'finalize_quiz'

    nodes = {'plan_quiz': plan_quiz, 'assemble_quiz': assemble_quiz,
             'generate_questions': generate_questions, 'finalize_quiz': finalize_quiz}
    return nodes, route_after_assemble
