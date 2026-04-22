import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'akatsuki-bench-Area51'

    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.dirname(basedir), 'data', 'database.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    
    # Knowledge Tracing Parameters
    INITIAL_KNOWLEDGE = 0.0  
    LEARNING_RATE = 0.15  # Increased slightly for faster progression
    FORGETTING_RATE = 0.05
    
    # Difficulty Levels
    DIFFICULTY_LEVELS = ['beginner', 'intermediate', 'advanced']