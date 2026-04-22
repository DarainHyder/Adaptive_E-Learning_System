"""
Multi-Agent System for Adaptive E-Learning
"""

from agents.base_agent import BaseAgent
from agents.teaching_agent import TeachingAgent
from agents.assessment_agent import AssessmentAgent
from agents.knowledge_agent import KnowledgeAgent
from agents.tutor_agent import TutorAgent
from agents.recommendation_agent import RecommendationAgent
from agents.coordinator_agent import CoordinatorAgent

__all__ = [
    'BaseAgent',
    'TeachingAgent',
    'AssessmentAgent',
    'KnowledgeAgent',
    'TutorAgent',
    'RecommendationAgent',
    'CoordinatorAgent'
]