"""Shared LangGraph state and the dependency container passed to every agent node."""
import operator
from dataclasses import dataclass, field
from typing import Annotated, Any, Optional, TypedDict


class LearningState(TypedDict, total=False):
    # inputs
    task: str                    # generate_lesson | generate_quiz | provide_hint | recommend_topic | full_learning_session
    user_id: int
    topic_id: Optional[int]
    request: dict                # task-specific inputs (question, code, attempt_count, fresh, goals ...)
    # written by agents
    profile: dict                # KnowledgeAgent: learner model
    strategy: dict               # TeachingAgent (decide): chosen strategy + bandit context
    lesson: dict                 # TeachingAgent (act)
    quiz_plan: dict              # AssessmentAgent (decide)
    quiz: dict                   # AssessmentAgent (act)
    generation_rounds: int       # AssessmentAgent generate/validate loop counter
    hint: dict                   # TutorAgent
    recommendations: dict        # RecommendationAgent
    trace: Annotated[list, operator.add]
    errors: Annotated[list, operator.add]


@dataclass
class AgentContext:
    llm: Any                     # services.llm.LLMService
    knowledge: Any               # services.knowledge.KnowledgeService
    bandit: Any                  # ml.bandit.StrategyBandit
    teaching_rules: Any
    tutor_rules: Any
    question_templates: list = field(default_factory=list)
    config: Any = None
