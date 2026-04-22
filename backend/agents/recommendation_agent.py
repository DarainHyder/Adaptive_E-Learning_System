"""
Recommendation Agent - Autonomous learning path optimization
"""
import json
from .base_agent import BaseAgent
from llm_service import LLMService
from agent_knowledge.rules.recommendation_rules import RecommendationRuleEngine
from agent_communication.message_bus import AgentMessageBus
from models import Topic, KnowledgeState
from datetime import datetime

class RecommendationAgent(BaseAgent):
    """
    Autonomous agent responsible for:
    - Suggesting next topics
    - Optimizing learning paths
    - Balancing difficulty
    - Considering prerequisites
    """
    
    def __init__(self):
        super().__init__("RA-001", "RecommendationAgent")
        self.llm_service = LLMService()
        self.rule_engine = RecommendationRuleEngine()
        self.message_bus = AgentMessageBus()
    
    def perceive(self, student_state):
        self.update_state("perceiving")
        self.user_id = getattr(student_state, 'user_id', None)
        self.current_topic_id = getattr(student_state, 'current_topic_id', None)
        self.goals = getattr(student_state, 'goals', [])
        
        # Get all topics and knowledge states
        self.all_topics = Topic.query.all()
        if self.user_id:
            self.knowledge_states = {
                ks.topic_id: ks.knowledge_level
                for ks in KnowledgeState.query.filter_by(user_id=self.user_id).all()
            }
        else:
             self.knowledge_states = {}
        
        self.log(f"Analyzing {len(self.all_topics)} topics, "
                f"{len(self.knowledge_states)} known states")
        
        return self
    
    def decide(self):
        """
        Autonomous decisions:
        - What topic to recommend next?
        - Short-term vs long-term path?
        - Review vs new content?
        """
        self.update_state("deciding")
        
        # Decision 1: Calculate scores for all topics
        topic_scores = []
        
        for topic in self.all_topics:
            if topic.id == self.current_topic_id:
                continue  # Skip current topic
            
            score = self._calculate_topic_score(topic)
            topic_scores.append((topic, score))
        
        # Sort by score
        topic_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Decision 2: Choose recommendation strategy
        if len(self.knowledge_states) < 3:
            # New learner - suggest foundation topics
            self.strategy = "foundation_building"
            self.recommendations = [t for t, s in topic_scores 
                                   if t.difficulty == 'beginner'][:3]
        else:
            # Experienced learner - balanced approach
            self.strategy = "balanced_growth"
            self.recommendations = [t for t, s in topic_scores[:5]]
        
        self.log(f"Strategy: {self.strategy}, {len(self.recommendations)} recommendations")
        
        return self
    
    def _calculate_topic_score(self, topic):
        """
        Autonomous scoring algorithm for topic recommendation
        """
        score = 0
        knowledge_level = self.knowledge_states.get(topic.id, 0)
        
        # Factor 1: Unstarted topics (high priority for beginners)
        if knowledge_level == 0:
            score += 5
        # Factor 2: In-progress topics
        elif 0 < knowledge_level < 0.7:
            score += 3
        # Factor 3: Mastered topics (low priority)
        elif knowledge_level >= 0.8:
            score += 0.5
        
        # Factor 4: Prerequisites
        if topic.prerequisites:
            prereq_ids = [int(x.strip()) for x in topic.prerequisites.split(',') if x.strip()]
            prereqs_met = all(
                self.knowledge_states.get(pid, 0) > 0.6
                for pid in prereq_ids
            )
            
            if prereqs_met:
                score += 3  # Ready to learn
            else:
                score -= 2  # Not ready yet
        else:
            score += 2  # No prerequisites - easier to start
        
        # Factor 5: Difficulty match
        avg_knowledge = sum(self.knowledge_states.values()) / len(self.knowledge_states) if self.knowledge_states else 0
        
        if topic.difficulty == 'beginner' and avg_knowledge < 0.3:
            score += 2
        elif topic.difficulty == 'intermediate' and 0.3 <= avg_knowledge < 0.7:
            score += 2
        elif topic.difficulty == 'advanced' and avg_knowledge >= 0.7:
            score += 2
        
        # Factor 6: Goals alignment
        if self.goals:
            for goal in self.goals:
                if goal.lower() in topic.name.lower() or goal.lower() in topic.category.lower():
                    score += 4
        
        return score
    
    def act(self):
        """
        Execute: Provide recommendations
        """
        self.update_state("acting")
        self.log("Generating personalized recommendations...")
        
        if not self.recommendations:
            self.log("No suitable recommendations found", "warning")
            self.update_state("completed")
            return {
                "recommendations": [],
                "message": "Great progress! Review previous topics or explore new categories.",
                "agent": self.name
            }
        
        # Build detailed recommendations
        detailed_recommendations = []
        
        for topic in self.recommendations:
            knowledge_level = self.knowledge_states.get(topic.id, 0)
            
            # Generate reason for recommendation
            if knowledge_level == 0:
                reason = "Ready to explore this new topic"
            elif knowledge_level < 0.5:
                reason = "Continue building on your progress"
            elif knowledge_level < 0.8:
                reason = "Almost there! Finish mastering this"
            else:
                reason = "Review to maintain mastery"
            
            detailed_recommendations.append({
                'topic_id': topic.id,
                'name': topic.name,
                'category': topic.category,
                'difficulty': topic.difficulty,
                'current_knowledge': knowledge_level,
                'reason': reason,
                'priority': 'high' if knowledge_level == 0 or 0.3 < knowledge_level < 0.7 else 'medium'
            })
        
        self.recommendations_made += 1
        self.log(f"Recommendations generated (Total: {self.recommendations_made})")
        
        # Store in memory
        self.memory.append({
            "action": "recommendations_generated",
            "count": len(detailed_recommendations),
            "strategy": self.strategy,
            "user_id": self.user_id
        })
        
        self.update_state("completed")
        
        return {
            "recommendations": detailed_recommendations,
            "strategy": self.strategy,
            "next_best": detailed_recommendations[0] if detailed_recommendations else None,
            "agent": self.name,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def create_learning_path(self, target_topic_id):
        """
        Autonomous creation of optimal learning path to target topic
        """
        self.update_state("planning")
        self.log(f"Creating learning path to topic {target_topic_id}")
        
        target_topic = Topic.query.get(target_topic_id)
        
        if not target_topic:
            return {"error": "Topic not found"}
        
        path = []
        queue = [target_topic]
        visited = set()
        
        while queue:
            topic = queue.pop(0)
            
            if topic.id in visited:
                continue
            
            visited.add(topic.id)
            knowledge_level = self.knowledge_states.get(topic.id, 0)
            
            # Add to path if not mastered
            if knowledge_level < 0.8:
                path.insert(0, {
                    'topic_id': topic.id,
                    'name': topic.name,
                    'current_knowledge': knowledge_level,
                    'estimated_hours': self._estimate_learning_time(topic, knowledge_level)
                })
            
            # Add prerequisites to queue
            if topic.prerequisites:
                prereq_ids = [int(x.strip()) for x in topic.prerequisites.split(',') if x.strip()]
                for pid in prereq_ids:
                    prereq_topic = Topic.query.get(pid)
                    if prereq_topic and prereq_topic.id not in visited:
                        queue.append(prereq_topic)
        
        self.learning_paths_created += 1
        self.log(f"Learning path created with {len(path)} steps")
        
        return {
            "path": path,
            "total_topics": len(path),
            "estimated_total_hours": sum(t['estimated_hours'] for t in path),
            "agent": self.name
        }
    
    def _estimate_learning_time(self, topic, current_knowledge):
        """Estimate hours needed based on difficulty and current knowledge"""
        base_hours = {
            'beginner': 3,
            'intermediate': 5,
            'advanced': 8
        }
        
        hours = base_hours.get(topic.difficulty, 5)
        remaining = 1 - current_knowledge
        
        return round(hours * remaining, 1)
    
    def get_statistics(self):
        """Return agent statistics"""
        return {
            "agent": self.name,
            "recommendations_made": self.recommendations_made,
            "learning_paths_created": self.learning_paths_created,
            "current_strategy": self.strategy if hasattr(self, 'strategy') else None,
            "state": self.state,
            "memory_size": len(self.memory)
        }