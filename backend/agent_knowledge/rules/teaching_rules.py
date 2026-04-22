import json
import os
import random

class TeachingRuleEngine:
    """
    Expert system for making teaching decisions based on student profile and pedagogical rules.
    Minimizes reliability on LLM by using pre-defined strategies and templates.
    """
    
    def __init__(self, knowledge_base_path=None):
        if knowledge_base_path is None:
            # Default to the standard location
            base_dir = os.path.dirname(os.path.dirname(__file__))
            knowledge_base_path = os.path.join(base_dir, 'knowledge_bases', 'teaching_strategies.json')
            
        self.strategies = []
        self.templates = {}
        self._load_knowledge_base(knowledge_base_path)
        
    def _load_knowledge_base(self, path):
        """Load strategies and templates from JSON file"""
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                self.strategies = data.get('strategies', [])
                self.templates = data.get('lesson_templates', {})
        except Exception as e:
            print(f"Error loading teaching knowledge base: {e}")
            # Fallback strategies if file missing
            self.strategies = [
                {"name": "standard", "effectiveness_score": 0.5}
            ]

    def select_teaching_strategy(self, student_profile):
        """
        Select the best teaching strategy based on student profile.
        
        Args:
            student_profile (dict): Contains knowledge_level, learning_style, etc.
            
        Returns:
            dict: The selected strategy object
        """
        knowledge_level = student_profile.get('knowledge_level', 0.0)
        learning_styles = student_profile.get('learning_style', [])
        is_struggling = student_profile.get('recent_performance', 1.0) < 0.6
        
        # Scaffolding Rule: Low knowledge or struggling -> Scaffolding
        if knowledge_level < 0.4 or is_struggling:
            return self._find_strategy("scaffolding")
            
        # Prioritize Learning Style
        if "visual" in learning_styles or "kinesthetic" in learning_styles:
             # Check for practical application or visual strategies
             if knowledge_level > 0.3:
                 return self._find_strategy("practical_application")
        
        # Advanced/Inquiry Rule: High knowledge -> Inquiry based
        if knowledge_level > 0.7:
            return self._find_strategy("inquiry_based")
            
        # Default: Direct Instruction or similar
        return self._find_strategy("direct_instruction") or self.strategies[0]

    def _find_strategy(self, name):
        """Find strategy by name"""
        for s in self.strategies:
            if s['name'] == name:
                return s
        return None

    def generate_lesson_structure(self, topic, strategy):
        """
        Generate a lesson structure using templates instead of LLM.
        
        Args:
            topic (object): The topic object (from DB)
            strategy (dict): The selected strategy
            
        Returns:
            dict: Structured lesson plan ready for content population
        """
        # Select template based on strategy or complexity
        template_name = "standard"
        if strategy['name'] == "scaffolding":
            template_name = "standard" # Could be more granular
        elif strategy['name'] == "micro_learning" or topic.difficulty == "beginner":
             if topic.description and len(topic.description) < 50:
                 template_name = "micro_learning"
        elif strategy['name'] == "inquiry_based":
             template_name = "deep_dive"
             
        template = self.templates.get(template_name, self.templates.get("standard"))
        
        # Construct the structure
        structure = {
            "title": f"Lesson: {topic.name}",
            "strategy_used": strategy['name'],
            "sections": [],
            "metadata": {
                "estimated_time": f"{template['word_count_target'] / 100} mins",
                "difficulty": topic.difficulty
            }
        }
        
        # Map template sections to strategy specific approaches
        strategy_structure = strategy.get('lesson_structure', {})
        
        for section in template['sections']:
            # Find specific instruction from strategy if available
            section_key = section.lower().replace(" ", "_")
            instruction = strategy_structure.get(section_key, f"Standard {section} content")
            
            structure['sections'].append({
                "title": section,
                "type": section_key,
                "instruction_for_llm": instruction
            })
            
        return structure
