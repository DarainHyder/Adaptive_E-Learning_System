import json
"""
Assessment Agent - Autonomous quiz generation and evaluation
"""
from .base_agent import BaseAgent
from llm_service import LLMService
from agent_knowledge.rules.assessment_rules import AssessmentRuleEngine
from agent_communication.message_bus import AgentMessageBus
from datetime import datetime

class AssessmentAgent(BaseAgent):
    """
    Autonomous agent responsible for:
    - Generating adaptive quizzes
    - Evaluating answers
    - Adjusting question difficulty
    - Providing detailed feedback
    """
    
    def __init__(self):
        super().__init__("AA-001", "AssessmentAgent")
        self.llm_service = LLMService()
        self.rule_engine = AssessmentRuleEngine()
        self.message_bus = AgentMessageBus()
        self.quizzes_generated = 0
        self.questions_evaluated = 0
        self.difficulty_adjustments = 0
        
    def perceive(self, student_state):
        """
        Perceive student's quiz context
        
        Args:
            student_state: object with student's current state (e.g., knowledge_level)
        """
        self.update_state("perceiving")
        self.log(f"Perceiving assessment needs for user {student_state.user_id}")
        
        self.user_id = student_state.user_id
        self.topic_id = student_state.topic_id
        self.knowledge_level = student_state.knowledge_level
        self.recent_performance = student_state.recent_performance
        self.quiz_type = student_state.quiz_type
        
        # Logic to determine number of questions could be more dynamic
        self.num_questions = 3 if self.knowledge_level < 0.5 else 5
        return self.state
    
    def decide(self):
        """
        Autonomous decisions:
        - What difficulty level for questions?
        - How many questions?
        - Question types (MCQ, coding, etc.)
        - Focus areas
        """
        self.update_state("deciding")
        
        # Decide on the mix of questions (difficulty, type)
        self.question_mix = self.rule_engine.select_question_types(
            self.knowledge_level, 
            "intermediate" # topic difficulty placeholder
        )
        self.log(f"Decided question mix: {self.question_mix}")
        return self
    
    def act(self, topic, prompt=None):
        """
        Execute: Generate adaptive quiz
        """
        self.update_state("acting")
        self.log(f"Generating quiz for topic: {topic.name}")
        
        if not topic:
            self.log("Topic not found", "error")
            return {"error": "Topic not found"}
        
        questions = []
        try:
            # 1. Try to generate questions from templates first (Rule-Based)
            for difficulty, count in self.question_mix.items():
                for _ in range(count):
                    template = self.rule_engine.get_template_for_topic(topic.name, difficulty)
                    if template:
                        # Use LLM just to fill the template (cheaper/faster than full gen)
                        # In future, fetch from ContentLibrary DB directly
                        q_prompt = self.rule_engine.formulate_question_prompt(
                            template, topic.name, difficulty
                        )
                        # We still use LLM service but with a very specific prompt
                        # This bridges the gap until we have a full static DB
                        generated = self.llm_service.generate_quiz_with_prompt(
                            topic.name, 1, custom_prompt=q_prompt
                        )
                        if generated:
                             questions.extend(generated)
            
            # 2. Fallback or Fill remaining
            if len(questions) < self.num_questions:
                needed = self.num_questions - len(questions)
                self.log(f"Template generation insufficient, requesting {needed} from LLM fallback.")
                fallback_qs = self.llm_service.generate_quiz_with_prompt(
                    topic.name, needed, custom_prompt=prompt
                )
                if fallback_qs:
                    questions.extend(fallback_qs)

            # 3. Notify Knowledge Agent of new assessment (simulated)
            # self.message_bus.send_message(...)
            
            self.quizzes_generated += 1
            self.log(f"Quiz generated successfully (Total: {self.quizzes_generated})")
            
            # Store in memory
            self.memory.append({
                "action": "quiz_generated",
                "topic": topic.name,
                "num_questions": self.num_questions,
                "difficulty_mix": self.difficulty_mix,
                "user_id": self.user_id
            })
            
            self.update_state("completed")
            
            return {
                "questions": quiz_questions,
                "metadata": {
                    "difficulty_mix": self.difficulty_mix,
                    "focus_areas": self.focus_areas,
                    "agent": self.name,
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            self.log(f"Error generating quiz: {str(e)}", "error")
            self.update_state("error")
            return {"error": str(e)}
    
    def evaluate_answer(self, question, user_answer, correct_answer, context):
        """
        Autonomous answer evaluation with detailed feedback
        
        Args:
            question: str
            user_answer: str
            correct_answer: str
            context: dict with topic info
        """
        self.update_state("evaluating")
        self.log(f"Evaluating answer: {user_answer} vs {correct_answer}")
        
        is_correct = user_answer == correct_answer
        self.questions_evaluated += 1
        
        # Generate intelligent feedback
        feedback_prompt = f"""
        Question: {question}
        Student answered: {user_answer}
        Correct answer: {correct_answer}
        Result: {"Correct" if is_correct else "Incorrect"}
        
        Provide encouraging, educational feedback (2-3 sentences):
        1. If correct: Explain why and reinforce the concept
        2. If incorrect: Explain the misconception and guide to correct understanding
        
        Be supportive and educational.
        """
        
        try:
            feedback = self.llm_service.model.generate_content(feedback_prompt).text
        except:
            feedback = "Review the concept and try again!" if not is_correct else "Great job!"
        
        self.log(f"Answer evaluated. Correct: {is_correct}")
        
        return {
            "is_correct": is_correct,
            "feedback": feedback,
            "agent": self.name,
            "evaluated_at": datetime.utcnow().isoformat()
        }
    
    def get_statistics(self):
        """Return agent statistics"""
        return {
            "agent": self.name,
            "quizzes_generated": self.quizzes_generated,
            "questions_evaluated": self.questions_evaluated,
            "state": self.state,
            "memory_size": len(self.memory)
        }