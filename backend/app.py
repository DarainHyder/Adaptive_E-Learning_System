"""Flask application factory. `gunicorn app:app` serves the module-level instance."""
import json
import logging
import os
import re
import sqlite3
from types import SimpleNamespace

from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy import event
from sqlalchemy.engine import Engine

from agent_knowledge.rules.teaching_rules import TeachingRuleEngine
from agent_knowledge.rules.tutor_rules import TutorRuleEngine
from agents.graph import Coordinator
from agents.state import AgentContext
from agents.tutor_chat import TutorChat
from config import BASE_DIR, Config
from curriculum.seed import seed_all
from ml.bandit import StrategyBandit
from models import db, migrate_schema
from routes import api
from services.knowledge import KnowledgeService
from services.llm import LLMService

logging.basicConfig(level=os.environ.get('LOG_LEVEL', 'INFO'),
                    format='%(asctime)s %(levelname)s %(name)s: %(message)s')
log = logging.getLogger('app')


@event.listens_for(Engine, 'connect')
def _sqlite_pragmas(dbapi_conn, _record):
    if isinstance(dbapi_conn, sqlite3.Connection):
        cur = dbapi_conn.cursor()
        cur.execute('PRAGMA journal_mode=WAL')
        cur.execute('PRAGMA busy_timeout=5000')
        cur.execute('PRAGMA synchronous=NORMAL')
        cur.close()


def build_services(app):
    cfg = SimpleNamespace(**{k: app.config[k] for k in app.config if k.isupper()})
    with open(os.path.join(BASE_DIR, 'agent_knowledge', 'knowledge_bases', 'question_templates.json')) as f:
        templates = json.load(f).get('question_templates', [])
    teaching_rules = TeachingRuleEngine()
    ctx = AgentContext(
        llm=LLMService(cfg),
        knowledge=KnowledgeService(cfg.ML_ARTIFACTS_DIR),
        bandit=StrategyBandit(teaching_rules.strategies),
        teaching_rules=teaching_rules,
        tutor_rules=TutorRuleEngine(),
        question_templates=templates,
        config=cfg,
    )
    tutor_db = app.config.get('TUTOR_DB_PATH') or os.path.join(cfg.DATA_DIR, 'tutor_memory.db')
    return SimpleNamespace(llm=ctx.llm, knowledge=ctx.knowledge, bandit=ctx.bandit, ctx=ctx,
                           coordinator=Coordinator(ctx), tutor_chat=TutorChat(ctx, tutor_db))


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)
    if app.config['SECRET_KEY'] == 'dev-only-change-me' and not app.config.get('TESTING'):
        log.warning('SECRET_KEY is not set: tokens will not survive restarts. Set SECRET_KEY in production.')

    origins = list(app.config['CORS_ORIGINS'])
    if app.config.get('CORS_ORIGIN_REGEX'):
        origins.append(re.compile(app.config['CORS_ORIGIN_REGEX']))
    CORS(app, supports_credentials=True, origins=origins,
         allow_headers=['Content-Type', 'Authorization'], methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:///'):
        os.makedirs(os.path.dirname(app.config['SQLALCHEMY_DATABASE_URI'][len('sqlite:///'):]), exist_ok=True)
    db.init_app(app)

    with app.app_context():
        db.create_all()
        migrate_schema()
        added = seed_all()
        if added:
            log.info('Seeded %d questions into the question bank', added)
        app.extensions['elearn'] = build_services(app)
        log.info('LLM: %s | knowledge model: %s', app.extensions['elearn'].llm.info()['provider'],
                 'transformer+bkt' if app.extensions['elearn'].knowledge.kt.available else 'bkt')

    app.register_blueprint(api)

    @app.errorhandler(404)
    def not_found(_e):
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(405)
    def not_allowed(_e):
        return jsonify({'error': 'Method not allowed'}), 405

    @app.errorhandler(500)
    def server_error(_e):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

    @app.teardown_request
    def _rollback_on_error(exc):
        if exc is not None:
            db.session.rollback()

    return app


app = create_app() if os.environ.get('ELEARN_NO_AUTOAPP') != '1' else None

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1', host='0.0.0.0', port=int(os.environ.get('PORT', 7860)))
