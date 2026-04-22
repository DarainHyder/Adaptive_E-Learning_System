class MessageProtocols:
    """
    Defines standard message structures and types for agent communication.
    Ensures all agents speak the same 'language'.
    """
    
    # Message Types
    KNOWLEDGE_REQUEST = 'knowledge_request'
    KNOWLEDGE_RESPONSE = 'knowledge_response'
    LEARNING_COMPLETE = 'learning_complete'
    CONTENT_REQUEST = 'content_request'
    ASSESSMENT_RESULT = 'assessment_result'
    
    @staticmethod
    def request_student_profile(user_id, topic_id=None):
        """Teaching Agent -> Knowledge Agent"""
        return {
            'type': MessageProtocols.KNOWLEDGE_REQUEST,
            'user_id': user_id,
            'topic_id': topic_id,
            'fields': ['knowledge_level', 'learning_style', 'weak_areas', 'frustration_level']
        }
        
    @staticmethod
    def provide_student_profile(user_id, profile_data):
        """Knowledge Agent -> Teaching Agent"""
        return {
            'type': MessageProtocols.KNOWLEDGE_RESPONSE,
            'user_id': user_id,
            'profile': profile_data
        }

    @staticmethod
    def notify_assessment_complete(user_id, topic_id, score, details):
        """Assessment Agent -> Knowledge Agent"""
        return {
            'type': MessageProtocols.ASSESSMENT_RESULT,
            'user_id': user_id,
            'topic_id': topic_id,
            'score': score,
            'details': details
        }
    
    @staticmethod
    def request_content_generation(topic_id, content_type, difficulty):
        """Coordinator -> Specialist Agent"""
        return {
            'type': MessageProtocols.CONTENT_REQUEST,
            'topic_id': topic_id,
            'content_type': content_type,
            'difficulty': difficulty
        }
