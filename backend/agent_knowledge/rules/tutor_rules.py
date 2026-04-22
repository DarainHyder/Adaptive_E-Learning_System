import json
import os
import random

class TutorRuleEngine:
    """
    Expert system for tutoring decisions.
    Selects hint strategies and templates based on student state.
    """
    
    def __init__(self, knowledge_base_path=None):
        if knowledge_base_path is None:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            knowledge_base_path = os.path.join(base_dir, 'knowledge_bases', 'hint_strategies.json')
            
        self.strategies = []
        self.quotes = []
        self._load_knowledge_base(knowledge_base_path)
        
    def _load_knowledge_base(self, path):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                self.strategies = data.get('hint_strategies', [])
                self.quotes = data.get('motivational_quotes', [])
        except Exception as e:
            print(f"Error loading tutor knowledge base: {e}")

    def select_hint_strategy(self, attempts, frustration_level):
        """
        Select best hint strategy.
        """
        # Linear progression logic based on attempts
        if attempts == 1:
            # First attempt: Socratic or subtle
            return self._find_strategy("socratic_questioning")
        elif attempts == 2:
            # Second attempt: Conceptual
            return self._find_strategy("conceptual_reminder")
        elif attempts >= 3:
            # High attempts: Direct help
            return self._find_strategy("direct_correction")
            
        # Fallback
        return self.strategies[0] if self.strategies else None

    def _find_strategy(self, name):
        for s in self.strategies:
            if s['name'] == name:
                return s
        return None

    def get_motivational_quote(self):
        if self.quotes:
            return random.choice(self.quotes)
        return "Keep trying!"
