import math
from datetime import datetime

class KnowledgeRuleEngine:
    """
    Expert system for knowledge tracking decisions.
    """
    
    def calculate_forgetting(self, last_practice_date, current_knowledge):
        """
        Apply Ebbinghaus forgetting curve.
        """
        if not last_practice_date:
            return current_knowledge
            
        days_elapsed = (datetime.utcnow() - last_practice_date).days
        
        if days_elapsed <= 0:
            return current_knowledge
            
        # R = e^(-t/S)
        # Stability (S) increases with knowledge strength
        stability = max(1, current_knowledge * 30) 
        retention = math.exp(-days_elapsed / stability)
        
        return current_knowledge * retention

    def predict_growth(self, current_knowledge, is_correct, difficulty):
        """
        Predict new knowledge level after an interaction.
        """
        learning_rate = 0.1
        difficulty_weight = 1.0
        
        if difficulty == "advanced":
            difficulty_weight = 1.2
        elif difficulty == "beginner":
            difficulty_weight = 0.8
            
        if is_correct:
            # Logarithmic growth: harder to improve as you get closer to 1.0
            growth = learning_rate * difficulty_weight * (1 - current_knowledge)
            return min(1.0, current_knowledge + growth)
        else:
            # Penalty is smaller than growth
            penalty = learning_rate * 0.5 * current_knowledge
            return max(0.0, current_knowledge - penalty)
