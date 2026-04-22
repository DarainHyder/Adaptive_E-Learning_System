import math
from datetime import datetime, timedelta
from models import db, KnowledgeState, QuizAttempt
from config import Config

class KnowledgeTracker:
    def __init__(self):
        self.learning_rate = Config.LEARNING_RATE
        self.forgetting_rate = Config.FORGETTING_RATE
    
    def get_or_create_knowledge_state(self, user_id, topic_id):
        """Get or create knowledge state for a user-topic pair"""
        state = KnowledgeState.query.filter_by(
            user_id=user_id, 
            topic_id=topic_id
        ).first()
        
        if not state:
            state = KnowledgeState(
                user_id=user_id,
                topic_id=topic_id,
                knowledge_level=Config.INITIAL_KNOWLEDGE,
                confidence=0.0
            )
            db.session.add(state)
            db.session.commit()
        
        return state
    
    def update_knowledge(self, user_id, topic_id, is_correct, difficulty, time_taken=None):
        """Update knowledge state based on quiz performance"""
        state = self.get_or_create_knowledge_state(user_id, topic_id)
        
        # Apply forgetting curve based on time since last practice (only if knowledge > 0)
        if state.knowledge_level > 0:
            time_diff = (datetime.utcnow() - state.last_practiced).days
            if time_diff > 0:
                forgetting_factor = math.exp(-self.forgetting_rate * time_diff)
                state.knowledge_level *= forgetting_factor
        
        # Update based on current performance
        difficulty_weight = self._get_difficulty_weight(difficulty)
        
        if is_correct:
            # Increase knowledge level
            delta = self.learning_rate * difficulty_weight * (1 - state.knowledge_level)
            state.knowledge_level = min(1.0, state.knowledge_level + delta)
            state.confidence = min(1.0, state.confidence + 0.1)
        else:
            # Decrease knowledge level slightly (only if there was knowledge to begin with)
            if state.knowledge_level > 0:
                delta = self.learning_rate * difficulty_weight * state.knowledge_level * 0.3
                state.knowledge_level = max(0.0, state.knowledge_level - delta)
            state.confidence = max(0.0, state.confidence - 0.1)
        
        # Update metadata
        state.last_practiced = datetime.utcnow()
        state.practice_count += 1
        
        db.session.commit()
        
        return state
    
    def _get_difficulty_weight(self, difficulty):
        """Get weight based on difficulty level"""
        weights = {
            'beginner': 0.7,
            'intermediate': 1.0,
            'advanced': 1.3
        }
        return weights.get(difficulty, 1.0)
    
    def get_recommended_difficulty(self, user_id, topic_id):
        """Recommend difficulty level based on knowledge state"""
        state = self.get_or_create_knowledge_state(user_id, topic_id)
        
        if state.knowledge_level < 0.3:
            return 'beginner'
        elif state.knowledge_level < 0.7:
            return 'intermediate'
        else:
            return 'advanced'
    
    def get_next_topic(self, user_id, current_topic_id=None):
        """Recommend next topic to learn based on knowledge states"""
        from models import Topic
        
        # Get all topics
        all_topics = Topic.query.all()
        
        # Get user's knowledge states
        knowledge_states = KnowledgeState.query.filter_by(user_id=user_id).all()
        knowledge_map = {ks.topic_id: ks.knowledge_level for ks in knowledge_states}
        
        # Score topics based on various factors
        topic_scores = []
        for topic in all_topics:
            if topic.id == current_topic_id:
                continue
            
            score = 0
            knowledge_level = knowledge_map.get(topic.id, 0)
            
            # Prefer topics that haven't been started or are in progress
            if knowledge_level == 0:
                score += 3  # Prioritize unstarted topics
            elif 0 < knowledge_level < 0.7:
                score += 2  # Then in-progress topics
            elif knowledge_level >= 0.7:
                score += 0.5  # Lower priority for mastered topics
            
            # Check prerequisites
            if topic.prerequisites:
                prereq_ids = [int(x.strip()) for x in topic.prerequisites.split(',') if x.strip()]
                prereq_met = all(knowledge_map.get(pid, 0) > 0.5 for pid in prereq_ids)
                if prereq_met:
                    score += 2
                elif any(knowledge_map.get(pid, 0) > 0 for pid in prereq_ids):
                    score += 1  # Some prerequisites started
                else:
                    score -= 1  # Prerequisites not met, but don't exclude completely
            else:
                score += 1  # No prerequisites, easier to start
            
            topic_scores.append((topic, score))
        
        # Sort by score and return top topic
        topic_scores.sort(key=lambda x: x[1], reverse=True)
        
        if topic_scores:
            return topic_scores[0][0]
        return None
    
    def get_progress_summary(self, user_id):
        """Get overall learning progress for a user"""
        knowledge_states = KnowledgeState.query.filter_by(user_id=user_id).all()
        
        if not knowledge_states:
            return {
                'average_knowledge': 0,
                'topics_mastered': 0,
                'topics_in_progress': 0,
                'total_practice_count': 0,
                'weak_topics': [],
                'strong_topics': []
            }
        
        total_knowledge = sum(ks.knowledge_level for ks in knowledge_states)
        avg_knowledge = total_knowledge / len(knowledge_states)
        
        mastered = [ks for ks in knowledge_states if ks.knowledge_level >= 0.8]
        in_progress = [ks for ks in knowledge_states if 0 < ks.knowledge_level < 0.8]
        weak = [ks for ks in knowledge_states if ks.knowledge_level <= 0.3 and ks.knowledge_level > 0]
        not_started = [ks for ks in knowledge_states if ks.knowledge_level == 0]
        
        total_practice = sum(ks.practice_count for ks in knowledge_states)
        
        return {
            'average_knowledge': round(avg_knowledge, 2),
            'topics_mastered': len(mastered),
            'topics_in_progress': len(in_progress),
            'total_practice_count': total_practice,
            'weak_topics': [{'id': ks.topic_id, 'level': round(ks.knowledge_level, 2)} 
                           for ks in sorted(weak + not_started, key=lambda x: x.knowledge_level)[:5]],
            'strong_topics': [{'id': ks.topic_id, 'level': round(ks.knowledge_level, 2)} 
                             for ks in sorted(mastered, key=lambda x: x.knowledge_level, reverse=True)[:5]]
        }