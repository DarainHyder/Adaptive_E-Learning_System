"""
TutorAgent
  provide_hint: hint ladder (socratic -> conceptual -> direct) chosen by expert rules from the
                attempt count, phrased by the LLM with the learner's code, output and mastery as context.
"""
from langchain_core.messages import HumanMessage, SystemMessage

from models import Topic, db

from .metrics import tracked
from .schemas import Hint

LEVEL_INSTRUCTIONS = {
    'subtle': 'Do NOT give the solution. Ask one guiding question and point at where to look.',
    'moderate': 'Explain the underlying concept and outline the approach, but do not write the full solution.',
    'detailed': 'Point out the specific mistake and show the minimal fix with a short code fragment.',
}


def make_nodes(ctx):
    @tracked('tutor')
    def provide_hint(state):
        req = state.get('request', {})
        attempts = max(1, int(req.get('attempt_count') or 1))
        strategy = ctx.tutor_rules.select_hint_strategy(attempts, req.get('frustration_level', 'normal')) or {}
        level = strategy.get('hint_level', 'moderate')
        topic = db.session.get(Topic, state['topic_id']) if state.get('topic_id') else None
        tp = state['profile']['topics'].get(state.get('topic_id'), {}) if topic else {}

        messages = [
            SystemMessage('You are a patient, encouraging programming tutor. Keep hints to 2-4 sentences.'),
            HumanMessage(
                f"Topic: {topic.name if topic else 'general programming'} "
                f"(learner mastery {tp.get('effective_mastery', 0):.0%}).\n"
                f"Exercise / question: {req.get('question') or 'free practice'}\n"
                f"Learner's code:\n```python\n{(req.get('challenge') or '')[:4000]}\n```\n"
                f"Last output or error: {(req.get('last_output') or 'n/a')[:1500]}\n"
                f"Attempt number: {attempts}. Hint strategy: {strategy.get('name', 'conceptual_reminder')}.\n"
                f"{LEVEL_INSTRUCTIONS[level]}"
            ),
        ]
        result = ctx.llm.structured(Hint, messages)
        if result is not None:
            text = result.hint + (f"\n\n{result.guiding_question}" if result.guiding_question else '')
            source = 'llm'
        else:
            lesson_hints = req.get('practice_hints') or []
            if lesson_hints:
                text = lesson_hints[min(attempts, len(lesson_hints)) - 1]
            else:
                concept = (topic.key_concepts or [topic.name])[0] if topic else 'the core idea'
                text = {'subtle': f'What should the program print first? Trace your code line by line and check how it uses {concept}.',
                        'moderate': f'Revisit {concept}: write down the steps in plain words, then translate each step into one line of code.',
                        'detailed': 'Run a tiny version of the problem, print every intermediate value, and compare it with the expected output to locate the first line that differs.'}[level]
            source = 'rules'
        return {'hint': {'hint': text, 'hint_level': level, 'strategy': strategy.get('name'),
                         'motivation': ctx.tutor_rules.get_motivational_quote(),
                         'agent': 'TutorAgent', 'source': source}}

    return {'provide_hint': provide_hint}
