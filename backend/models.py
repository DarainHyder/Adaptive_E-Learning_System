from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))  # nullable for accounts created before v2
    learning_style = db.Column(db.String(30), default='mixed')
    goals = db.Column(db.JSON, default=list)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    knowledge_states = db.relationship('KnowledgeState', backref='user', lazy=True)
    learning_sessions = db.relationship('LearningSession', backref='user', lazy=True)
    quiz_attempts = db.relationship('QuizAttempt', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return bool(self.password_hash) and check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'user_id': self.id,
            'username': self.username,
            'email': self.email,
            'learning_style': self.learning_style or 'mixed',
            'goals': self.goals or [],
        }


class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(80), unique=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)
    prerequisites = db.Column(db.String(200))  # Comma-separated topic IDs
    key_concepts = db.Column(db.JSON, default=list)
    position = db.Column(db.Integer, default=0)

    knowledge_states = db.relationship('KnowledgeState', backref='topic', lazy=True)

    @property
    def prerequisite_ids(self):
        if not self.prerequisites:
            return []
        return [int(x) for x in self.prerequisites.split(',') if x.strip().isdigit()]

    def to_dict(self):
        return {
            'id': self.id,
            'slug': self.slug,
            'name': self.name,
            'category': self.category,
            'difficulty': self.difficulty,
            'description': self.description,
            'prerequisites': self.prerequisite_ids,
            'key_concepts': self.key_concepts or [],
        }


class KnowledgeState(db.Model):
    __table_args__ = (db.UniqueConstraint('user_id', 'topic_id', name='uq_knowledge_user_topic'),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    knowledge_level = db.Column(db.Float, default=0.0)  # BKT posterior P(mastered)
    confidence = db.Column(db.Float, default=0.0)
    last_practiced = db.Column(db.DateTime, default=datetime.utcnow)
    practice_count = db.Column(db.Integer, default=0)
    correct_count = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LearningSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(20))
    strategy = db.Column(db.String(50))
    context_bucket = db.Column(db.String(20))
    reward_sum = db.Column(db.Float, default=0.0)
    reward_count = db.Column(db.Integer, default=0)
    duration = db.Column(db.Integer)  # in seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question_bank.id'))
    question = db.Column(db.Text, nullable=False)
    user_answer = db.Column(db.Text)
    correct_answer = db.Column(db.Text)
    is_correct = db.Column(db.Boolean)
    difficulty = db.Column(db.String(20))
    time_taken = db.Column(db.Integer)  # in seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)


class QuestionBank(db.Model):
    """Reusable question pool. Most quizzes are assembled from here without an LLM call."""
    __tablename__ = 'question_bank'

    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False, index=True)
    difficulty = db.Column(db.String(20), nullable=False)
    concept = db.Column(db.String(120))
    question = db.Column(db.Text, nullable=False)
    question_hash = db.Column(db.String(40), unique=True)
    options = db.Column(db.JSON, nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)
    explanation = db.Column(db.Text)
    source = db.Column(db.String(20), default='llm')  # seed | llm
    times_served = db.Column(db.Integer, default=0)
    times_answered = db.Column(db.Integer, default=0)
    times_correct = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def empirical_p_correct(self):
        # Beta(2,2)-smoothed proportion correct, an item-difficulty estimate
        return (self.times_correct + 2) / (self.times_answered + 4)

    def to_public_dict(self):
        """What the client sees while answering: no answer key; grading happens server-side."""
        return {
            'id': self.id,
            'question': self.question,
            'options': self.options,
            'difficulty': self.difficulty,
            'concept': self.concept,
        }


class AgentKnowledge(db.Model):
    """Stores learned patterns and strategies for each agent (e.g. bandit arm posteriors)."""
    id = db.Column(db.Integer, primary_key=True)
    agent_type = db.Column(db.String(50), index=True)
    knowledge_type = db.Column(db.String(50))
    key = db.Column(db.String(120), index=True)
    content = db.Column(db.JSON)
    effectiveness_score = db.Column(db.Float, default=0.5)
    usage_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentMessage(db.Model):
    """Communication between agents (kept for backwards compatibility)."""
    id = db.Column(db.Integer, primary_key=True)
    from_agent = db.Column(db.String(50))
    to_agent = db.Column(db.String(50))
    message_type = db.Column(db.String(50))
    content = db.Column(db.JSON)
    status = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)


class AgentPerformance(db.Model):
    """Per-run agent telemetry."""
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.String(50))
    action_type = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    success_metric = db.Column(db.Float)
    api_calls_used = db.Column(db.Integer, default=0)
    execution_time_ms = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ContentLibrary(db.Model):
    """Generated content cache (lessons, study tips) to reduce LLM calls."""
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'))
    content_type = db.Column(db.String(50), index=True)
    cache_key = db.Column(db.String(200), index=True)
    difficulty = db.Column(db.String(20))
    content = db.Column(db.Text)
    meta_data = db.Column(db.JSON)
    quality_score = db.Column(db.Float, default=0.5)
    usage_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def migrate_schema():
    """Tiny additive migration for SQLite databases created by v1 (adds missing columns)."""
    inspector = inspect(db.engine)
    existing_tables = set(inspector.get_table_names())
    with db.engine.begin() as conn:
        for table in db.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue
            present = {c['name'] for c in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in present:
                    continue
                col_type = column.type.compile(dialect=db.engine.dialect)
                conn.execute(text(f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {col_type}'))
