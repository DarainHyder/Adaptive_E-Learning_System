from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    knowledge_states = db.relationship('KnowledgeState', backref='user', lazy=True)
    learning_sessions = db.relationship('LearningSession', backref='user', lazy=True)
    quiz_attempts = db.relationship('QuizAttempt', backref='user', lazy=True)

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)
    prerequisites = db.Column(db.String(200))  # Comma-separated topic IDs
    
    knowledge_states = db.relationship('KnowledgeState', backref='topic', lazy=True)

class KnowledgeState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    knowledge_level = db.Column(db.Float, default=0.0)  # Changed from 0.5 to 0.0
    confidence = db.Column(db.Float, default=0.0)  # Changed from 0.5 to 0.0
    last_practiced = db.Column(db.DateTime, default=datetime.utcnow)
    practice_count = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class LearningSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(20))
    duration = db.Column(db.Integer)  # in seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    user_answer = db.Column(db.Text)
    correct_answer = db.Column(db.Text)
    is_correct = db.Column(db.Boolean)
    difficulty = db.Column(db.String(20))
    time_taken = db.Column(db.Integer)  # in seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AgentKnowledge(db.Model):
    """Stores learned patterns and strategies for each agent"""
    id = db.Column(db.Integer, primary_key=True)
    agent_type = db.Column(db.String(50))  # teaching, assessment, etc.
    knowledge_type = db.Column(db.String(50))  # strategy, template, rule
    content = db.Column(db.JSON)
    effectiveness_score = db.Column(db.Float, default=0.5)
    usage_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AgentMessage(db.Model):
    """Communication between agents"""
    id = db.Column(db.Integer, primary_key=True)
    from_agent = db.Column(db.String(50))
    to_agent = db.Column(db.String(50))
    message_type = db.Column(db.String(50))  # request, response, notification
    content = db.Column(db.JSON)
    status = db.Column(db.String(20))  # pending, processed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)

class AgentPerformance(db.Model):
    """Track agent effectiveness over time"""
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.String(50))
    action_type = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    success_metric = db.Column(db.Float)  # User performance after agent action
    api_calls_used = db.Column(db.Integer, default=0)
    execution_time_ms = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ContentLibrary(db.Model):
    """Pre-generated content to reduce API calls"""
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'))
    content_type = db.Column(db.String(50))  # lesson, quiz, hint
    difficulty = db.Column(db.String(20))
    content = db.Column(db.Text)
    meta_data = db.Column(db.JSON)
    quality_score = db.Column(db.Float, default=0.5)
    usage_count = db.Column(db.Integer, default=0)