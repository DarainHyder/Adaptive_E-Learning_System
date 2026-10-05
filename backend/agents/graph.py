"""
CoordinatorAgent as a LangGraph StateGraph.

                         ┌──────────────► recommend ──(full session)──┐
 START ─► profile_learner┼──────────────► provide_hint ─► END         │
       (KnowledgeAgent)  ├─► select_strategy ─► teach ─(full)─┐       │
                         │      ▲  (TeachingAgent)            │       │
                         │      └─────────────────────────────┼───────┘
                         └─► plan_quiz ─► assemble_quiz ──► finalize_quiz ─► END
                                (AssessmentAgent)  │  ▲
                                                   ▼  │ (bank short & LLM available, ≤2 rounds)
                                             generate_questions
"""
import time

from langgraph.graph import END, START, StateGraph

from . import assessment_agent, knowledge_agent, recommendation_agent, teaching_agent, tutor_agent
from .metrics import METRICS
from .state import LearningState

TASK_ENTRY = {
    'generate_lesson': 'select_strategy',
    'generate_quiz': 'plan_quiz',
    'provide_hint': 'provide_hint',
    'recommend_topic': 'recommend',
    'full_learning_session': 'recommend',
}


def build_graph(ctx):
    g = StateGraph(LearningState)
    nodes = {}
    nodes.update(knowledge_agent.make_nodes(ctx))
    nodes.update(teaching_agent.make_nodes(ctx))
    assessment_nodes, route_after_assemble = assessment_agent.make_nodes(ctx)
    nodes.update(assessment_nodes)
    nodes.update(tutor_agent.make_nodes(ctx))
    nodes.update(recommendation_agent.make_nodes(ctx))
    for name, fn in nodes.items():
        g.add_node(name, fn)

    g.add_edge(START, 'profile_learner')
    g.add_conditional_edges('profile_learner', lambda s: TASK_ENTRY.get(s['task'], END),
                            list(set(TASK_ENTRY.values())) + [END])
    g.add_conditional_edges('recommend',
                            lambda s: 'select_strategy' if s['task'] == 'full_learning_session' and s.get('topic_id') else END,
                            ['select_strategy', END])
    g.add_edge('select_strategy', 'teach')
    g.add_conditional_edges('teach', lambda s: 'plan_quiz' if s['task'] == 'full_learning_session' else END,
                            ['plan_quiz', END])
    g.add_edge('plan_quiz', 'assemble_quiz')
    g.add_conditional_edges('assemble_quiz', route_after_assemble, ['generate_questions', 'finalize_quiz'])
    g.add_edge('generate_questions', 'assemble_quiz')
    g.add_edge('finalize_quiz', END)
    g.add_edge('provide_hint', END)
    return g.compile()


class Coordinator:
    """Thin facade used by the Flask routes."""

    def __init__(self, ctx):
        self.ctx = ctx
        self.graph = build_graph(ctx)

    def run(self, task, user_id, topic_id=None, **request):
        if task not in TASK_ENTRY:
            raise ValueError(f'Unknown task: {task}')
        METRICS.start('coordinator')
        t0 = time.perf_counter()
        ok = True
        try:
            return self.graph.invoke({'task': task, 'user_id': user_id, 'topic_id': topic_id,
                                      'request': request, 'trace': [], 'errors': []})
        except Exception:
            ok = False
            raise
        finally:
            METRICS.finish('coordinator', int((time.perf_counter() - t0) * 1000), ok=ok, note=task)

    def mermaid(self):
        return self.graph.get_graph().draw_mermaid()
