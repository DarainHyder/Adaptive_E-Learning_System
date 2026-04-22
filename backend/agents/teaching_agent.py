"""
Teaching Agent - Autonomous content generation and delivery
"""
import json
from .base_agent import BaseAgent
from llm_service import LLMService
from agent_knowledge.rules.teaching_rules import TeachingRuleEngine
from agent_communication.message_bus import AgentMessageBus
from agent_communication.protocols import MessageProtocols
from datetime import datetime
import random


class TeachingAgent(BaseAgent):
    """
    Autonomous agent responsible for:
    - Generating personalized lessons
    - Adapting teaching style
    - Selecting examples based on student performance
    """
    
    def __init__(self):
        super().__init__("TA-001", "TeachingAgent")
        self.llm_service = LLMService()
        self.rule_engine = TeachingRuleEngine()
        self.message_bus = AgentMessageBus()
        self.lessons_generated = 0
        self.knowledge_level = 0.0
        self.learning_style = "visual"
        self.lesson_complexity = "beginner"
        self.current_strategy = {}
        
    def perceive(self, student_state):
        self.update_state("perceiving")
        self.log(f"Perceiving student state for user {student_state.user_id}")
        
        # Update internal state based on student data
        self.user_id = student_state.user_id
        self.knowledge_level = student_state.knowledge_level
        self.learning_style = student_state.learning_style or "visual"
        
        # Determine lesson complexity based on knowledge level
        if self.knowledge_level < 0.3:
            self.lesson_complexity = "beginner"
        elif self.knowledge_level < 0.7:
            self.lesson_complexity = "intermediate"
        else:
            self.lesson_complexity = "advanced"
        
        self.update_state("perceived")
        return self.state
    
    def decide(self):
        self.update_state("deciding")
        
        # Use rule engine to determine strategy
        student_profile = {
            "knowledge_level": self.knowledge_level,
            "learning_style": self.learning_style,
            # Mock recent performance for now, ideally comes from KnowledgeAgent
            "recent_performance": 0.8 
        }
        
        self.current_strategy = self.rule_engine.select_teaching_strategy(student_profile)
        self.log(f"Selected teaching strategy: {self.current_strategy['name']}")
        
        self.update_state("decided")
        return self
    
    def act(self, topic, prompt=None):
        self.update_state("acting")
        self.log(f"Generating lesson for topic: {topic.name} with strategy {self.current_strategy['name']}")
        
        # 1. Request updated profile from KnowledgeAgent (Async/Simulated)
        self.message_bus.send_message(
            self.name, 
            "KnowledgeAgent", 
            MessageProtocols.KNOWLEDGE_REQUEST, 
            MessageProtocols.request_student_profile(self.user_id, topic.id)
        )

        try:
            # 2. Generate Lesson Structure using Rule Engine (No LLM)
            lesson_structure = self.rule_engine.generate_lesson_structure(topic, self.current_strategy)
            
            # 3. Fill in content (Hybrid: Try Templates first, else Fallback to LLM for specific sections)
            # For this MVP, we will use the structure to guide the LLM, reducing its "thinking" time
            # In a full impl, we would pull pre-written content from ContentLibrary
            
            structured_prompt = f"""
            Create a lesson for topic '{topic.name}' ({topic.difficulty}) following this structure:
            
            Strategy: {self.current_strategy['name']} ({self.current_strategy['description']})
            
            Sections:
            """
            
            for section in lesson_structure['sections']:
                structured_prompt += f"\n- {section['title']}: {section['instruction_for_llm']}"
            
            # Fallback to LLM for content generation but with strict structure
            lesson_content = self.llm_service.generate_lesson_with_prompt(
                topic.name,
                topic.difficulty,
                self.knowledge_level,
                custom_prompt=structured_prompt
            )
            
            self.lessons_generated += 1
            self.log(f"Lesson generated successfully using rule-guided structure. (Total: {self.lessons_generated})")
            
            # Store in agent memory
            self.memory.append({
                "action": "lesson_generated",
                "topic": topic.name,
                "strategy": self.current_strategy['name'],
                "complexity": self.lesson_complexity,
                "user_id": self.user_id
            })
            
            self.update_state("completed")
            
            return {
                "content": lesson_content,
                "metadata": {
                    "teaching_style": self.current_strategy.get('name', 'default'),
                    "complexity": self.lesson_complexity,
                    "example_count": self.current_strategy.get('example_count', 3),
                    "agent": self.name,
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            self.log(f"Error generating lesson: {str(e)}", "error")
            self.update_state("error")
            return {"error": str(e)}
    
    def get_statistics(self):
        """Return agent statistics"""
        return {
            "agent": self.name,
            "lessons_generated": self.lessons_generated,
            "current_style": self.current_style,
            "state": self.state,
            "memory_size": len(self.memory)
        }