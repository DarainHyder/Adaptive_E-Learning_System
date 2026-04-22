"""
Tutor Agent - Autonomous assistance and motivation
"""
import json
from .base_agent import BaseAgent
from llm_service import LLMService
from agent_knowledge.rules.tutor_rules import TutorRuleEngine
from datetime import datetime

class TutorAgent(BaseAgent):
    """
    Autonomous agent responsible for:
    - Providing hints
    - Answering questions
    - Motivational support
    - Adaptive guidance
    """
    
    def __init__(self):
        super().__init__("TUA-001", "TutorAgent")
        self.llm_service = LLMService()
        self.rule_engine = TutorRuleEngine()
        self.hints_provided = 0
        self.questions_answered = 0
        self.motivation_level = "neutral"
        self.strategy = None # To store the selected strategy
        
    def perceive(self, student_state, context=None):
        """
        Perceive student's help needs
        
        Args:
            student_state: object with student's current state (e.g., frustration_level)
            context: dict with additional context (e.g., 'attempts')
        """
        self.update_state("perceiving")
        self.log(f"Perceiving student state. Frustration: {getattr(student_state, 'frustration_level', 'N/A')}")
        
        # Context might contain recent quiz attempts, time taken, etc.
        self.frustration_level = getattr(student_state, 'frustration_level', 'low')
        # Simulate attempts count or get from context
        self.attempts = context.get('attempts', 1) if context else 1
        
        return self
    
    def decide(self):
        """
        Autonomous decisions:
        - How much help to provide?
        - What teaching approach?
        - Level of motivation needed?
        """
        self.update_state("deciding")
        
        # Determine hint strategy
        self.strategy = self.rule_engine.select_hint_strategy(
            self.attempts, self.frustration_level
        )
        
        self.log(f"Decided strategy: {self.strategy['name'] if self.strategy else 'default'}")
        
        return self
    
    def act(self, prompt=None):
        """
        Execute: Provide intelligent hint or answer based on the decided strategy
        """
        self.update_state("acting")
        self.log(f"Providing help with strategy: {self.strategy['name'] if self.strategy else 'default'}")
        
        try:
            
            self.update_state("completed")
            
            return {
                "hint": response,
                "hint_level": self.hint_level,
                "motivation": self.motivation_level,
                "agent": self.name,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.log(f"Error generating hint: {str(e)}", "error")
            self.update_state("error")
            return {
                "hint": "Think about what you've learned. Break the problem into smaller steps!",
                "agent": self.name
            }
    
    def provide_motivation(self, user_performance):
        """
        Autonomous motivational message based on performance
        """
        self.update_state("motivating")
        
        score = user_performance.get('score', 0)
        improvement = user_performance.get('improvement', 0)
        
        if score >= 0.8:
            message = "🌟 Excellent work! You're mastering this topic. Ready for a challenge?"
        elif score >= 0.6:
            message = "👍 Good progress! Keep practicing and you'll get there."
        elif improvement > 0.1:
            message = "📈 Great improvement! Your hard work is paying off."
        else:
            message = "💪 Don't give up! Every expert was once a beginner. Take it one step at a time."
        
        self.log(f"Motivation provided for score {score}")
        
        return {
            "message": message,
            "agent": self.name,
            "tone": "encouraging"
        }
    
    def get_statistics(self):
        """Return agent statistics"""
        return {
            "agent": self.name,
            "hints_provided": self.hints_provided,
            "questions_answered": self.questions_answered,
            "current_motivation_level": self.motivation_level,
            "state": self.state,
            "memory_size": len(self.memory)
        }