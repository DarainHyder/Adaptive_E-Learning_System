import json
import os
import random

class AssessmentRuleEngine:
    """
    Expert system for assessment decisions.
    Selects questions and formats quizzes based on rules and templates.
    """
    
    def __init__(self, knowledge_base_path=None):
        if knowledge_base_path is None:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            knowledge_base_path = os.path.join(base_dir, 'knowledge_bases', 'question_templates.json')
            
        self.question_templates = []
        self.rubrics = {}
        self._load_knowledge_base(knowledge_base_path)
        
    def _load_knowledge_base(self, path):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                self.question_templates = data.get('question_templates', [])
                self.rubrics = data.get('assessment_rubrics', {})
        except Exception as e:
            print(f"Error loading assessment knowledge base: {e}")

    def select_question_types(self, knowledge_level, topic_difficulty):
        """
        Determine the mix of question types/difficulties.
        """
        mix = {"beginner": 0, "intermediate": 0, "advanced": 0}
        
        if knowledge_level < 0.3:
            mix["beginner"] = 3
            mix["intermediate"] = 1
        elif knowledge_level < 0.7:
            mix["beginner"] = 1
            mix["intermediate"] = 2
            mix["advanced"] = 1
        else:
            mix["intermediate"] = 2
            mix["advanced"] = 3
            
        return mix

    def get_template_for_topic(self, topic_name, difficulty):
        """
        Find a question template suitable for the topic and difficulty.
        """
        candidates = []
        for t in self.question_templates:
            # Check if template is applicable to this topic (simple keyword match for now)
            # In a real system, this would be a more robust tag matching
            is_applicable = "all" in t['applicable_topics']
            if not is_applicable:
                for keyword in t['applicable_topics']:
                    if keyword in topic_name.lower():
                        is_applicable = True
                        break
            
            if is_applicable:
                candidates.append(t)
                
        if not candidates:
            return None
            
        return random.choice(candidates)

    def formulate_question_prompt(self, template, topic_name, difficulty):
        """
        Use a template to create a specific prompt for the LLM to fill.
        This reduces the LLM's work to just filling blanks/generating code.
        """
        modifier = template['difficulty_modifiers'].get(difficulty, "Standard")
        
        prompt = f"""
        Generate a specific question about "{topic_name}" using this pattern:
        "{template['pattern']}"
        
        Constraint: {modifier}
        Cognitive Level: {template['cognitive_level']}
        
        Return the Code Snippet (if applicable), Options, Correct Answer, and Explanation.
        """
        return prompt
