import google.generativeai as genai
from config import Config
import json
import time

class LLMService:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.generation_config = {
            'temperature': 0.7,
            'top_p': 0.8,
            'top_k': 40,
            'max_output_tokens': 2048,
        }
    
    # ============ AGENT-COMPATIBLE METHODS ============
    
    def generate_lesson_with_prompt(self, topic_name, difficulty, knowledge_level, custom_prompt=None):
        """
        Generate lesson with custom prompt (for Teaching Agent)
        
        Args:
            topic_name: str - Name of the topic
            difficulty: str - Difficulty level
            knowledge_level: float - Current knowledge (0-1)
            custom_prompt: str - Custom prompt from Teaching Agent (optional)
        
        Returns:
            str - Generated lesson content
        """
        if custom_prompt:
            prompt = custom_prompt
        else:
            # Use default prompt structure
            prompt = self._default_lesson_prompt(topic_name, difficulty, knowledge_level)
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            return response.text
        except Exception as e:
            print(f"Error generating lesson: {e}")
            return self._get_fallback_lesson(topic_name, difficulty)
    
    def generate_quiz_with_prompt(self, topic_name, num_questions, custom_prompt=None):
        """
        Generate quiz with custom prompt (for Assessment Agent)
        
        Args:
            topic_name: str - Name of the topic
            num_questions: int - Number of questions to generate
            custom_prompt: str - Custom prompt from Assessment Agent (optional)
        
        Returns:
            list - Array of quiz questions
        """
        if custom_prompt:
            prompt = custom_prompt
        else:
            prompt = self._default_quiz_prompt(topic_name, num_questions)
        
        try:
            response = self.model.generate_content(
                prompt, 
                generation_config=self.generation_config
            )
            text = response.text.strip()
            
            # Extract JSON from response
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0]
            elif '```' in text:
                text = text.split('```')[1].split('```')[0]
            
            questions = json.loads(text.strip())
            
            # Validate structure
            if isinstance(questions, list) and len(questions) > 0:
                return questions
            else:
                raise ValueError("Invalid JSON structure")
                
        except Exception as e:
            print(f"Error generating quiz: {e}")
            return self._get_fallback_quiz(topic_name, 'intermediate', num_questions)
    
    def generate_hint_with_context(self, question, context, hint_level='moderate'):
        """
        Generate hint with specific context (for Tutor Agent)
        
        Args:
            question: str - Student's question
            context: dict - Context information
            hint_level: str - Level of hint detail (subtle, moderate, detailed)
        
        Returns:
            str - Generated hint
        """
        challenge = context.get('challenge', '')
        attempt_count = context.get('attempt_count', 1)
        
        hint_instructions = {
            'subtle': 'Provide a gentle nudge without revealing the solution. Ask guiding questions.',
            'moderate': 'Explain the concept and provide a partial solution or approach.',
            'detailed': 'Provide clear explanation with example code, but encourage student to try.'
        }
        
        prompt = f"""
        You are a supportive programming tutor.
        
        STUDENT CONTEXT:
        - Question: {question}
        - Challenge: {challenge}
        - Previous attempts: {attempt_count}
        
        INSTRUCTIONS:
        {hint_instructions.get(hint_level, hint_instructions['moderate'])}
        
        Be encouraging and educational. Keep response 2-4 sentences.
        """
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            return response.text
        except Exception as e:
            print(f"Error generating hint: {e}")
            return "Think about what you've learned. Break the problem into smaller steps!"
    
    # ============ LEGACY METHODS (Still supported) ============
    
    def generate_lesson(self, topic_name, difficulty, knowledge_level):
        """
        Generate personalized lesson content (Legacy method)
        Calls the agent-compatible method internally
        """
        return self.generate_lesson_with_prompt(
            topic_name, 
            difficulty, 
            knowledge_level, 
            custom_prompt=None
        )
    
    def generate_quiz_questions(self, topic_name, difficulty, num_questions=5):
        """
        Generate quiz questions for a topic (Legacy method)
        Calls the agent-compatible method internally
        """
        prompt = self._default_quiz_prompt(topic_name, num_questions, difficulty)
        return self.generate_quiz_with_prompt(topic_name, num_questions, prompt)
    
    def explain_answer(self, question, user_answer, correct_answer, topic):
        """
        Generate explanation for why an answer is correct/incorrect
        Used by Assessment Agent
        """
        prompt = f"""
        Topic: {topic}
        Question: {question}
        Student's Answer: {user_answer}
        Correct Answer: {correct_answer}
        
        Provide a clear, encouraging explanation (2-3 sentences) about:
        1. Why the correct answer is right
        2. If wrong, what misconception the student might have
        3. A tip to remember this concept
        
        Be supportive and educational.
        """
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            return response.text
        except Exception as e:
            print(f"Error generating explanation: {e}")
            if user_answer == correct_answer:
                return f"Correct! The answer {correct_answer} demonstrates your understanding of {topic}."
            else:
                return f"The correct answer is {correct_answer}. Review the key concepts of {topic} to strengthen your understanding."
    
    def generate_study_tips(self, weak_topics, strong_topics):
        """
        Generate personalized study recommendations
        Used by Recommendation Agent and dashboard
        """
        weak_str = ', '.join(weak_topics) if weak_topics else 'None'
        strong_str = ', '.join(strong_topics) if strong_topics else 'None'
        
        prompt = f"""
        Based on a student's performance:
        
        Weak areas: {weak_str}
        Strong areas: {strong_str}
        
        Provide 3-5 personalized, actionable study tips.
        
        FORMATTING RULES:
        - Start each tip with a dash (-)
        - Keep each tip to 2-3 sentences
        - Use **bold** for key terms
        - Be specific and encouraging
        - Make tips actionable
        
        Format as simple bullet points with dashes.
        """
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            return response.text
        except Exception as e:
            print(f"Error generating tips: {e}")
            return "- Practice regularly with focused study sessions\n- Review weak topics daily\n- Build on your strengths\n- Take breaks to avoid burnout\n- Track your progress"
    
    # ============ PRIVATE HELPER METHODS ============
    
    def _default_lesson_prompt(self, topic_name, difficulty, knowledge_level):
        """Default lesson prompt structure"""
        return f"""
        Create a comprehensive lesson on "{topic_name}" for a student at {difficulty} level 
        with current knowledge level of {knowledge_level*100:.0f}%.
        
        Structure the lesson as follows:
        
        ## Introduction
        Brief overview (2-3 sentences)
        
        ## Core Concepts
        Main ideas explained clearly with examples
        
        ## Practical Examples
        Real code or scenarios (use proper formatting)
        
        ## Real-World Applications
        Where this is used in industry
        
        ## Key Takeaways
        3-5 bullet points summarizing main ideas
        
        ## Practice Challenge
        ONE simple coding exercise that students can solve.
        Format: "Write a Python program that [task description]. Expected output: [example]"
        Make it achievable for {difficulty} level students.
        
        FORMATTING RULES:
        - Use ## for main headings, ### for subheadings
        - Keep paragraphs SHORT (2-3 sentences max)
        - Use bullet points (-) for lists
        - Use **bold** for important terms
        - Use code blocks with ```python for code examples
        - Keep total length 400-600 words
        - Make it engaging and easy to scan
        - For Practice Challenge, give clear task and expected output
        """
    
    def _default_quiz_prompt(self, topic_name, num_questions, difficulty='intermediate'):
        """Default quiz prompt structure"""
        return f"""
        Generate {num_questions} multiple-choice questions on "{topic_name}" at {difficulty} level.
        
        For each question, provide:
        1. The question
        2. Four options (A, B, C, D)
        3. The correct answer (letter only: A, B, C, or D)
        4. A brief explanation
        
        Return ONLY a valid JSON array with this exact structure:
        [
            {{
                "question": "Question text here?",
                "options": {{
                    "A": "Option A text",
                    "B": "Option B text",
                    "C": "Option C text",
                    "D": "Option D text"
                }},
                "correct_answer": "A",
                "explanation": "Explanation here"
            }}
        ]
        
        Return ONLY the JSON array, no other text.
        """
    
    def _get_fallback_lesson(self, topic_name, difficulty):
        """Fallback lesson content when API fails"""
        return f"""
        <h2>Introduction to {topic_name}</h2>
        <p>Welcome to this {difficulty} level lesson on {topic_name}. This is an important topic that will help you build your knowledge.</p>
        <h3>Core Concepts</h3>
        <p>{topic_name} is a fundamental concept that requires understanding and practice. Let's break it down into manageable parts.</p>
        <h3>Key Points to Remember</h3>
        <ul>
            <li>Start with the basics and build gradually</li>
            <li>Practice regularly to reinforce learning</li>
            <li>Apply concepts to real-world scenarios</li>
            <li>Review and revise frequently</li>
        </ul>
        <h3>Next Steps</h3>
        <p>Take the quiz to test your understanding and track your progress. Don't worry if you don't get everything right the first time - learning is a journey!</p>
        <p><em>Note: This is a basic lesson. For detailed content, please check your internet connection and API settings.</em></p>
        """
    
    def _get_fallback_quiz(self, topic_name, difficulty, num_questions):
        """Fallback quiz when API fails"""
        questions = []
        for i in range(min(num_questions, 3)):
            questions.append({
                "question": f"Sample question {i+1} about {topic_name} ({difficulty} level)?",
                "options": {
                    "A": "This is option A",
                    "B": "This is option B",
                    "C": "This is option C",
                    "D": "This is option D"
                },
                "correct_answer": "A",
                "explanation": f"This is a sample question for {topic_name}. Practice with real content by ensuring your API connection is working."
            })
        return questions