"""
TeachingAgent
  decide: pick a pedagogical strategy = expert rules (prior) + Thompson-sampling bandit (learned)
  act:    produce a structured lesson (LLM structured output), reusing cached variants to save calls
"""
import random

from langchain_core.messages import HumanMessage, SystemMessage

from models import Topic, db
from services import content
from services.sandbox import ALLOWED_IMPORTS

from .metrics import tracked
from .schemas import Lesson

SYSTEM = (
    'You are an expert instructor who writes concise, accurate, engaging lessons for an adaptive '
    'e-learning platform. Adapt depth and pacing to the learner profile you are given. '
    'Use Markdown inside section bodies. Code must be correct and runnable.'
)


def complexity_for(knowledge):
    if knowledge < 0.3:
        return 'beginner'
    if knowledge < 0.7:
        return 'intermediate'
    return 'advanced'


def make_nodes(ctx):
    @tracked('teaching')
    def select_strategy(state):
        topic_id = state['topic_id']
        tp = state['profile']['topics'].get(topic_id, {})
        knowledge = tp.get('effective_mastery', 0.0)
        style = state.get('request', {}).get('learning_style', 'mixed')
        accuracy = tp.get('accuracy')
        rule = ctx.teaching_rules.select_teaching_strategy({
            'knowledge_level': knowledge,
            'learning_style': style,
            'recent_performance': accuracy if accuracy is not None else 1.0,
        }) or ctx.teaching_rules.strategies[0]
        name, bucket, samples = ctx.bandit.select(knowledge, rule_choice=rule['name'])
        chosen = ctx.teaching_rules._find_strategy(name) or rule
        return {'strategy': {
            'name': name,
            'description': chosen.get('description', ''),
            'lesson_structure': chosen.get('lesson_structure', {}),
            'rule_choice': rule['name'],
            'bucket': bucket,
            'bandit_samples': {k: round(v, 3) for k, v in samples.items()},
            'complexity': complexity_for(knowledge),
            'knowledge_level': knowledge,
        }}

    def _prompt(topic, strategy, profile, request):
        tp = profile['topics'].get(topic.id, {})
        weak_prereqs = [profile['topics'][p]['name'] for p in topic.prerequisite_ids
                        if p in profile['topics'] and profile['topics'][p]['effective_mastery'] < 0.5]
        structure = ctx.teaching_rules.generate_lesson_structure(topic, {'name': strategy['name'],
                                                                         'lesson_structure': strategy['lesson_structure']})
        plan = '\n'.join(f"- {s['title']}: {s['instruction_for_llm'].replace('_', ' ')}" for s in structure['sections'])
        goals = ', '.join(request.get('goals') or []) or 'not specified'
        return [
            SystemMessage(SYSTEM),
            HumanMessage(
                f"Write a lesson on **{topic.name}** ({topic.category}).\n"
                f"Topic description: {topic.description}\n"
                f"Key concepts to cover: {', '.join(topic.key_concepts or [])}\n\n"
                f"Learner profile:\n"
                f"- current mastery: {tp.get('effective_mastery', 0):.0%} (target level: {strategy['complexity']})\n"
                f"- predicted success on intermediate questions: {tp.get('predicted_success', {}).get('intermediate', 0.5):.0%}\n"
                f"- learning style: {request.get('learning_style', 'mixed')}; goals: {goals}\n"
                f"- prerequisites still weak: {', '.join(weak_prereqs) or 'none'} (briefly recap these first if any)\n\n"
                f"Pedagogical strategy: {strategy['name']} - {strategy['description']}\n"
                f"Follow this section plan:\n{plan}\n\n"
                f"Requirements: 3-6 sections; 1-3 code examples; 3-5 key takeaways; one practice challenge whose "
                f"starter code runs in plain Python and only imports from: {', '.join(sorted(ALLOWED_IMPORTS))}. "
                f"If the topic is not Python-specific, make the challenge a Python simulation of the idea. "
                f"Target length ~{structure['metadata']['estimated_time'].split()[0]} minutes of reading."
            ),
        ]

    @tracked('teaching')
    def teach(state):
        topic = db.session.get(Topic, state['topic_id'])
        strategy = state['strategy']
        request = state.get('request', {})
        key = content.lesson_cache_key(topic.id, strategy['complexity'], strategy['name'])
        cached = content.cached_lessons(key)
        limit = ctx.config.LESSON_CACHE_VARIANTS

        if cached and (len(cached) >= limit or not ctx.llm.available) and not request.get('fresh'):
            row = random.choice(cached)
            row.usage_count = (row.usage_count or 0) + 1
            return {'lesson': {'lesson': row.meta_data, 'markdown': row.content, 'source': 'cache'}}

        result = ctx.llm.structured(Lesson, _prompt(topic, strategy, state['profile'], request))
        if result is not None:
            lesson = result.model_dump()
            md = content.lesson_to_markdown(lesson)
            content.store_lesson(key, topic.id, strategy['complexity'], lesson, md)
            return {'lesson': {'lesson': lesson, 'markdown': md, 'source': 'llm'}}

        if cached:
            row = random.choice(cached)
            return {'lesson': {'lesson': row.meta_data, 'markdown': row.content, 'source': 'cache'}}
        lesson = content.offline_lesson(topic, strategy['complexity'], strategy['name'])
        return {'lesson': {'lesson': lesson, 'markdown': content.lesson_to_markdown(lesson), 'source': 'offline'},
                'errors': ['llm_unavailable'] if ctx.llm.available else []}

    return {'select_strategy': select_strategy, 'teach': teach}
