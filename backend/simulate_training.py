
import sys
import random
import time
from unittest.mock import MagicMock

# MOCK BROKEN DEPENDENCIES BEFORE IMPORTING APP
# This is necessary because google-generativeai depends on protobuf which is broken on Python 3.14
mock_genai = MagicMock()
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = mock_genai
sys.modules['google.ai'] = MagicMock()
sys.modules['google.api_core'] = MagicMock()

from app import app, db
from models import User, Topic, AgentKnowledge, AgentPerformance, KnowledgeState, LearningSession, QuizAttempt
from agents.coordinator_agent import CoordinatorAgent

# Mock LLM Service to avoid API calls during simulation
class MockLLMService:
    def generate_lesson_with_prompt(self, topic, difficulty, knowledge_level, custom_prompt=None):
        return f"Simulated lesson content for {topic} ({difficulty})"
        
    def generate_quiz_with_prompt(self, topic, num_questions, custom_prompt=None):
        return [{"question": "Simulated Q", "options": ["A", "B"], "answer": "A"}] * num_questions

    def generate_content(self, prompt):
        return "Simulated content"

class SimulatedStudent:
    def __init__(self, profile_type):
        self.profile_type = profile_type
        self.id = int(time.time()) + random.randint(1000, 9999) # Fake ID
        self.knowledge = {} # topic_id -> level
        
        # Define characteristics
        if profile_type == "fast_visual":
            self.learning_rate = 1.5
            self.preferred_style = "visual"
            self.patience = 3
        elif profile_type == "slow_detailed":
            self.learning_rate = 0.8
            self.preferred_style = "reading"
            self.patience = 8
        else: # average
            self.learning_rate = 1.0
            self.preferred_style = "mixed"
            self.patience = 5
            
    def attempt_quiz(self, difficulty, content_quality):
        """Simulate quiz result based on difficulty vs learning match"""
        base_success = 0.7 * self.learning_rate
        
        # Adjust based on content quality match
        if self.preferred_style in content_quality.get('style', ''):
            base_success += 0.2
            
        # Adjust based on difficulty
        if difficulty == "advanced": base_success -= 0.3
        elif difficulty == "intermediate": base_success -= 0.1
        
        # Random variance
        success_prob = min(max(base_success + random.uniform(-0.1, 0.1), 0.1), 0.95)
        return random.random() < success_prob

class TrainingSimulator:
    def __init__(self):
        self.coordinator = CoordinatorAgent()
        
        # Patch agents with Mock Service
        mock_llm = MockLLMService()
        self.coordinator.teaching_agent.llm_service = mock_llm
        self.coordinator.assessment_agent.llm_service = mock_llm
        self.coordinator.tutor_agent.llm_service = mock_llm
        self.coordinator.recommendation_agent.llm_service = mock_llm
        
        self.strategies_updated = 0
        
    def run_simulation(self, iterations=10):
        print(f"Starting simulation with {iterations} cycles...")
        
        with app.app_context():
            # Ensure we have topics
            topics = Topic.query.all()
            if not topics:
                print("No topics found. Run init_db first.")
                return

            for i in range(iterations):
                student_type = random.choice(["fast_visual", "slow_detailed", "average"])
                student = SimulatedStudent(student_type)
                topic = random.choice(topics)
                
                print(f"\nCycle {i+1}: Student {student.profile_type} tackling '{topic.name}'")
                
                # 1. Generate Lesson
                result = self.coordinator.perceive({
                    'task': 'generate_lesson',
                    'user_id': student.id, # Mock ID
                    'context': {
                        'topic_id': topic.id,
                        'knowledge_level': student.knowledge.get(topic.id, 0),
                        'learning_style': student.preferred_style
                    }
                }).decide().act()
                
                if not result['success']:
                    print("  - Lesson generation failed")
                    continue
                    
                teaching_data = result['results'].get('TeachingAgent', {})
                strategy_name = teaching_data.get('metadata', {}).get('teaching_style', 'unknown')
                
                # 2. Simulate Learning & Quiz
                # We assume the lesson content has some style metadata
                # For simulation, we assume the agent picked a strategy name
                
                # 3. Assessment
                passed = student.attempt_quiz(
                    teaching_data.get('metadata', {}).get('complexity', 'beginner'),
                    {'style': strategy_name} # Simplified matching
                )
                
                outcome = "PASSED" if passed else "FAILED"
                print(f"  - Strategy: {strategy_name} -> {outcome}")
                
                # 4. Reinforcement (Update AgentKnowledge)
                self.update_agent_knowledge(strategy_name, passed)
                
    def update_agent_knowledge(self, strategy_name, success):
        """Reinforce the strategy in the database"""
        # Find the strategy
        # Note: In a real system, we'd query by ID. 
        # Here we search JSON content for the name.
        
        # We need to find the AgentKnowledge row where content->>'name' == strategy_name
        # SQLite JSON support is limited, so we iterate (slow but fine for simulation script)
        knowledge_items = AgentKnowledge.query.filter_by(agent_type='teaching').all()
        
        target_item = None
        for item in knowledge_items:
            if item.content.get('name') == strategy_name:
                target_item = item
                break
        
        if target_item:
            # Update Score (Moving Average)
            alpha = 0.1
            reward = 1.0 if success else 0.0
            new_score = (1 - alpha) * target_item.effectiveness_score + (alpha * reward)
            
            target_item.effectiveness_score = new_score
            target_item.usage_count += 1
            db.session.commit()
            self.strategies_updated += 1
            print(f"    [Updated] Score: {target_item.effectiveness_score:.2f} (Uses: {target_item.usage_count})")
        else:
            print(f"    [Warning] Strategy '{strategy_name}' not found in DB")

if __name__ == '__main__':
    sim = TrainingSimulator()
    # Run a batch for verification
    sim.run_simulation(iterations=20)
