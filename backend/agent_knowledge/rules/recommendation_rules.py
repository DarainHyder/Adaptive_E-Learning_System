class RecommendationRuleEngine:
    """
    Expert system for recommendation decisions.
    """
    
    def score_topic(self, topic, user_knowledge_map):
        """
        Score a topic for recommendation suitability.
        Returns a score (higher is better).
        """
        score = 0
        current_knowledge = user_knowledge_map.get(topic.id, 0)
        
        # Rule 1: Don't recommend mastered topics (unless for review)
        if current_knowledge > 0.85:
            return -1
            
        # Rule 2: Prerequisites must be met
        if not self._check_prerequisites(topic, user_knowledge_map):
            return -10 # Blocked
            
        # Rule 3: Prioritize active topics
        if 0 < current_knowledge < 0.7:
            score += 5
            
        # Rule 4: Beginner topics get boost if nothing started
        if current_knowledge == 0 and topic.difficulty == "beginner":
            score += 3
            
        return score

    def _check_prerequisites(self, topic, knowledge_map):
        if not topic.prerequisites:
            return True
            
        if isinstance(topic.prerequisites, str):
            prereq_ids = [int(p) for p in topic.prerequisites.split(',') if p.strip()]
        else:
             prereq_ids = []
             
        for pid in prereq_ids:
            if knowledge_map.get(pid, 0) < 0.6:
                return False
        return True
