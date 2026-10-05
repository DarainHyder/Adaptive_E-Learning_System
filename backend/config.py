import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _default_data_dir():
    """Prefer HF Spaces persistent storage (/data) when it is mounted and writable."""
    if os.path.isdir('/data') and os.access('/data', os.W_OK):
        return '/data'
    return os.path.join(os.path.dirname(BASE_DIR), 'data')


def _bool(name, default=False):
    return os.environ.get(name, str(default)).lower() in ('1', 'true', 'yes')


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-only-change-me'

    DATA_DIR = os.environ.get('DATA_DIR') or _default_data_dir()
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(DATA_DIR, 'database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}

    # Cross-site cookies (Vercel frontend -> HF backend) need SameSite=None; Secure.
    # Bearer tokens are the primary auth mechanism, cookies are a fallback.
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'None')
    SESSION_COOKIE_SECURE = _bool('SESSION_COOKIE_SECURE', True)
    TOKEN_MAX_AGE = int(os.environ.get('TOKEN_MAX_AGE', 60 * 60 * 24 * 14))

    CORS_ORIGINS = [o.strip() for o in os.environ.get(
        'CORS_ORIGINS',
        'http://localhost:3000,http://localhost:5173,https://adaptive-e-learning-system.vercel.app'
    ).split(',') if o.strip()]
    # Vercel preview deployments
    CORS_ORIGIN_REGEX = os.environ.get('CORS_ORIGIN_REGEX', r'https://adaptive-e-learning-system.*\.vercel\.app')

    # LLM
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
    LLM_PROVIDER = os.environ.get('LLM_PROVIDER', 'gemini' if GEMINI_API_KEY else 'offline')
    LLM_MODEL = os.environ.get('LLM_MODEL', 'gemini-2.5-flash')
    LLM_TEMPERATURE = float(os.environ.get('LLM_TEMPERATURE', 0.6))
    LLM_TIMEOUT = int(os.environ.get('LLM_TIMEOUT', 60))
    LLM_MAX_RETRIES = int(os.environ.get('LLM_MAX_RETRIES', 2))

    # Content reuse: how many cached lesson variants to keep per (topic, level, strategy)
    LESSON_CACHE_VARIANTS = int(os.environ.get('LESSON_CACHE_VARIANTS', 3))
    QUIZ_SIZE_MIN = 4
    QUIZ_SIZE_MAX = 6

    # Knowledge tracing
    ML_ARTIFACTS_DIR = os.environ.get('ML_ARTIFACTS_DIR') or os.path.join(BASE_DIR, 'ml', 'artifacts')
    TARGET_SUCCESS_RATE = 0.7  # "desirable difficulty" target for adaptive quizzes
    MASTERY_THRESHOLD = 0.8
    PREREQ_READY_THRESHOLD = 0.6

    # Code sandbox
    SANDBOX_TIMEOUT_S = 5
    SANDBOX_MEMORY_MB = 256
    SANDBOX_MAX_OUTPUT = 10_000

    DIFFICULTY_LEVELS = ['beginner', 'intermediate', 'advanced']


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    SESSION_COOKIE_SECURE = False
    LLM_PROVIDER = 'offline'
