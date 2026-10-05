import os
import sys

import pytest

os.environ['ELEARN_NO_AUTOAPP'] = '1'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.schemas import Hint, Lesson, Quiz  # noqa: E402
from app import create_app  # noqa: E402
from config import TestConfig  # noqa: E402


class FakeLLM:
    """Duck-typed stand-in for services.llm.LLMService that returns canned structured outputs."""

    def __init__(self):
        self.calls = []
        self.provider = 'fake'

    available = True

    def structured(self, schema, messages):
        self.calls.append(schema.__name__)
        if schema is Lesson:
            return Lesson(
                title='Fake lesson', summary='Summary.', objectives=['a', 'b', 'c'],
                sections=[{'title': 'Intro', 'body_markdown': 'Hello **world**'}],
                code_examples=[{'title': 'Ex', 'code': 'print(1)', 'language': 'python', 'explanation': 'prints 1'}],
                key_takeaways=['x', 'y', 'z'],
                practice={'prompt': 'Print 2', 'starter_code': 'print(2)', 'expected_output': '2', 'hints': ['h1', 'h2', 'h3']},
                estimated_minutes=10)
        if schema is Quiz:
            n = len([c for c in self.calls if c == 'Quiz'])
            return Quiz(questions=[{
                'question': f'Generated question {n}-{i}?',
                'options': {'A': f'a{i}', 'B': f'b{i}', 'C': f'c{i}', 'D': f'd{i}'},
                'correct_answer': 'C', 'explanation': 'because', 'difficulty': d, 'concept': 'testing'}
                for i, d in enumerate(['beginner', 'intermediate', 'advanced'] * 3)])
        if schema is Hint:
            return Hint(hint='Try printing the variable.', guiding_question='What is its type?')
        return None

    def chat(self, messages):
        self.calls.append('chat')
        return f'Tutor reply to: {messages[-1].content}'

    def info(self):
        return {'provider': 'fake', 'available': True, 'calls': len(self.calls)}


@pytest.fixture()
def app(tmp_path):
    class Cfg(TestConfig):
        DATA_DIR = str(tmp_path)
        TUTOR_DB_PATH = str(tmp_path / 'tutor.db')

    application = create_app(Cfg)
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def fake_llm(app):
    llm = FakeLLM()
    services = app.extensions['elearn']
    services.ctx.llm = llm
    services.llm = llm
    return llm


def register(client, username='alice'):
    r = client.post('/api/register', json={'username': username, 'email': f'{username}@example.com',
                                           'password': 'correct-horse'})
    assert r.status_code == 201, r.get_json()
    return {'Authorization': f"Bearer {r.get_json()['token']}"}


@pytest.fixture()
def auth(client):
    return register(client)
