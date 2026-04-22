import sys
from unittest.mock import MagicMock

# MOCK BROKEN DEPENDENCIES
mock_genai = MagicMock()
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = mock_genai
sys.modules['google.ai'] = MagicMock()
sys.modules['google.api_core'] = MagicMock()

from app import app, db
from models import AgentKnowledge, AgentMessage, AgentPerformance, ContentLibrary

with app.app_context():
    db.create_all()
    print("Database tables created successfully.")
    
    # Verify tables exist
    import sqlalchemy
    inspector = sqlalchemy.inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"Existing tables: {tables}")
