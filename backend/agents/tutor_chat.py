"""
Conversational AI tutor with persistent memory.

A LangGraph MessagesState graph checkpointed to SQLite: one thread per (user, topic), so the
conversation survives restarts and is personalised with the learner model on every turn.
"""
import logging
import os
import sqlite3

from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage, SystemMessage
from langgraph.graph import START, MessagesState, StateGraph

from models import Topic, db

from .metrics import tracked

log = logging.getLogger(__name__)
HISTORY_WINDOW = 16
MAX_STORED_MESSAGES = 60


class TutorChat:
    def __init__(self, ctx, db_path):
        self.ctx = ctx
        os.makedirs(os.path.dirname(db_path) or '.', exist_ok=True)
        try:
            from langgraph.checkpoint.sqlite import SqliteSaver
            self.checkpointer = SqliteSaver(sqlite3.connect(db_path, check_same_thread=False))
        except ImportError:  # pragma: no cover
            from langgraph.checkpoint.memory import InMemorySaver
            log.warning('langgraph-checkpoint-sqlite not installed; tutor memory is in-memory only')
            self.checkpointer = InMemorySaver()
        self.graph = self._build()

    def _system_prompt(self, user_id, topic_id):
        profile = self.ctx.knowledge.profile(user_id)
        topic = db.session.get(Topic, topic_id) if topic_id else None
        weak = ', '.join(w['name'] for w in profile['weak_topics']) or 'none yet'
        due = ', '.join(r['name'] for r in profile['review_queue'][:3]) or 'none'
        focus = ''
        if topic:
            tp = profile['topics'].get(topic.id, {})
            focus = (f"The learner is currently studying '{topic.name}' ({topic.description}); "
                     f"their mastery is {tp.get('effective_mastery', 0):.0%}. Key concepts: "
                     f"{', '.join(topic.key_concepts or [])}.\n")
        return (
            'You are an expert, friendly AI tutor on an adaptive learning platform. Teach Socratically: '
            'check understanding, give small worked examples, and prefer guiding questions over full '
            'solutions for exercises. Use Markdown and ```python code fences. Keep answers focused '
            '(under ~250 words unless asked for more).\n'
            f"{focus}Learner's weak topics: {weak}. Topics due for review: {due}. "
            f"Overall average mastery: {profile['average_knowledge']:.0%}."
        )

    def _build(self):
        ctx = self.ctx

        @tracked('tutor', trace=False)
        def respond(state, config):
            cfg = config['configurable']
            history = state['messages'][-HISTORY_WINDOW:]
            reply = ctx.llm.chat([SystemMessage(self._system_prompt(cfg['user_id'], cfg.get('topic_id')))] + history)
            if reply is None:
                topic = db.session.get(Topic, cfg['topic_id']) if cfg.get('topic_id') else None
                concepts = ', '.join((topic.key_concepts or [])[:3]) if topic else ''
                reply = ('I am running in offline mode right now (no LLM configured), so I cannot answer '
                         'free-form questions. ' + (f'For **{topic.name}**, focus on: {concepts}. ' if topic else '')
                         + 'Try the lesson, the practice playground and the adaptive quiz meanwhile!')
            update = [AIMessage(reply)]
            overflow = len(state['messages']) + 1 - MAX_STORED_MESSAGES
            if overflow > 0:  # keep the checkpoint small
                update += [RemoveMessage(id=m.id) for m in state['messages'][:overflow]]
            return {'messages': update}

        g = StateGraph(MessagesState)
        g.add_node('respond', respond)
        g.add_edge(START, 'respond')
        return g.compile(checkpointer=self.checkpointer)

    @staticmethod
    def _config(user_id, topic_id):
        return {'configurable': {'thread_id': f'user-{user_id}:topic-{topic_id or "general"}',
                                 'user_id': user_id, 'topic_id': topic_id}}

    def send(self, user_id, topic_id, message):
        out = self.graph.invoke({'messages': [HumanMessage(message)]}, self._config(user_id, topic_id))
        return out['messages'][-1].content

    def history(self, user_id, topic_id):
        snap = self.graph.get_state(self._config(user_id, topic_id))
        msgs = snap.values.get('messages', []) if snap and snap.values else []
        return [{'role': 'user' if isinstance(m, HumanMessage) else 'assistant', 'content': m.content}
                for m in msgs if isinstance(m, (HumanMessage, AIMessage))]

    def clear(self, user_id, topic_id):
        thread = self._config(user_id, topic_id)['configurable']['thread_id']
        try:
            self.checkpointer.delete_thread(thread)
        except Exception as exc:  # pragma: no cover
            log.warning('Could not clear tutor thread %s: %s', thread, exc)
