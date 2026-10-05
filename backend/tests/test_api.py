from conftest import register
from models import QuestionBank, User, db


def test_index_and_topics(client):
    assert client.get('/').status_code == 200
    topics = client.get('/api/topics').get_json()
    assert len(topics) == 20
    by_slug = {t['slug']: t for t in topics}
    assert by_slug['functions']['prerequisites'] == [by_slug['control-flow']['id']]


def test_auth_flow(client):
    assert client.post('/api/register', json={'username': 'bob', 'email': 'bad', 'password': 'x'}).status_code == 400
    headers = register(client, 'bob')
    fresh = client.application.test_client()  # no session cookie
    assert fresh.get('/api/current-user').status_code == 401
    assert fresh.get('/api/current-user', headers=headers).get_json()['username'] == 'bob'
    assert fresh.post('/api/login', json={'username': 'bob', 'password': 'wrong-pass'}).status_code == 401
    assert fresh.post('/api/generate-quiz', json={'topic_id': 1}).status_code == 401
    assert fresh.post('/api/login', json={'username': 'bob', 'password': 'correct-horse'}).status_code == 200
    assert fresh.post('/api/generate-quiz', json={'topic_id': 1}).status_code == 200  # session-cookie fallback


def test_legacy_user_sets_password_on_first_login(app, client):
    with app.app_context():
        db.session.add(User(username='legacy', email='legacy@example.com'))
        db.session.commit()
    r = client.post('/api/login', json={'username': 'legacy', 'password': 'new-password'})
    assert r.status_code == 200 and r.get_json()['token']
    assert client.post('/api/login', json={'username': 'legacy', 'password': 'other-password'}).status_code == 401


def test_offline_lesson_and_quiz(client, auth):
    lesson = client.post('/api/generate-lesson', json={'topic_id': 1}, headers=auth).get_json()
    assert lesson['source'] == 'offline' and lesson['lesson']['practice']['starter_code']
    assert [s['agent'] for s in lesson['agent_metadata']['trace']] == ['knowledge', 'teaching', 'teaching']

    quiz = client.post('/api/generate-quiz', json={'topic_id': 1}, headers=auth).get_json()
    assert quiz['questions'] and 'correct_answer' not in quiz['questions'][0]  # answer key stays server-side
    assert client.post('/api/generate-lesson', json={'topic_id': 999}, headers=auth).status_code == 404


def test_server_side_grading_updates_knowledge_and_bandit(client, auth, app):
    client.post('/api/generate-lesson', json={'topic_id': 1}, headers=auth)
    with app.app_context():
        q = QuestionBank.query.filter_by(topic_id=1).first()
        qid, correct = q.id, q.correct_answer
    r = client.post('/api/submit-answer', json={'topic_id': 1, 'question_id': qid, 'user_answer': correct,
                                                'correct_answer': 'Z'}, headers=auth).get_json()
    assert r['is_correct'] is True and r['correct_answer'] == correct  # client-sent key is ignored
    assert r['new_knowledge_level'] > 0 and r['rewarded_strategy']
    wrong = 'A' if correct != 'A' else 'B'
    r2 = client.post('/api/submit-answer', json={'topic_id': 1, 'question_id': qid, 'user_answer': wrong}, headers=auth).get_json()
    assert r2['is_correct'] is False and r2['new_knowledge_level'] < r['new_knowledge_level']
    with app.app_context():
        q = db.session.get(QuestionBank, qid)
        assert (q.times_answered, q.times_correct) == (2, 1)


def test_progress_endpoints(client, auth):
    summary = client.get('/api/progress-summary', headers=auth).get_json()
    assert summary['topics_total'] == 20 and summary['total_practice_count'] == 0
    states = client.get('/api/knowledge-states', headers=auth).get_json()['states']
    assert len(states) == 20 and set(states[0]['predicted_success']) == {'beginner', 'intermediate', 'advanced'}
    nxt = client.get('/api/next-topic', headers=auth).get_json()
    assert nxt['readiness'] == 1.0  # never recommend something whose prerequisites are unmet
    path = client.get('/api/learning-path/20', headers=auth).get_json()
    names = [p['name'] for p in path['path']]
    assert names[0] == 'Python Basics' and names[-1] == 'LLM Apps & Agents'
    assert client.get('/api/study-tips', headers=auth).get_json()['tips'].startswith('- ')
    assert client.get('/api/review-queue', headers=auth).status_code == 200
    assert client.get('/api/agent-status', headers=auth).get_json()['framework'] == 'LangGraph'
    assert 'graph' in client.get('/api/model-info').get_json()['agent_graph_mermaid']


def test_llm_paths_with_fake_model(client, auth, fake_llm, app):
    lesson = client.post('/api/generate-lesson', json={'topic_id': 2}, headers=auth).get_json()
    assert lesson['source'] == 'llm' and lesson['lesson']['title'] == 'Fake lesson'
    assert '```python' in lesson['content']

    # Exhaust the seeded bank so the assessment agent must generate (graph cycle).
    with app.app_context():
        before = QuestionBank.query.filter_by(topic_id=2).count()
    quiz = client.post('/api/generate-quiz', json={'topic_id': 2}, headers=auth).get_json()
    for q in quiz['questions']:
        client.post('/api/submit-answer', json={'topic_id': 2, 'question_id': q['id'], 'user_answer': 'A'}, headers=auth)
    quiz2 = client.post('/api/generate-quiz', json={'topic_id': 2}, headers=auth).get_json()
    assert 'Quiz' in fake_llm.calls
    with app.app_context():
        assert QuestionBank.query.filter_by(topic_id=2).count() > before
    assert not {q['id'] for q in quiz['questions']} & {q['id'] for q in quiz2['questions']}  # no repeats

    hint = client.post('/api/ask-challenge-hint', json={'topic_id': 2, 'challenge': 'x', 'attempt_count': 1},
                       headers=auth).get_json()
    assert hint['source'] == 'llm' and hint['hint_level'] == 'subtle'


def test_tutor_chat_memory(client, auth, fake_llm):
    r = client.post('/api/tutor/chat', json={'message': 'What is a loop?', 'topic_id': 2}, headers=auth).get_json()
    assert r['reply'] == 'Tutor reply to: What is a loop?'
    client.post('/api/tutor/chat', json={'message': 'And recursion?', 'topic_id': 2}, headers=auth)
    hist = client.get('/api/tutor/history?topic_id=2', headers=auth).get_json()['messages']
    assert [m['role'] for m in hist] == ['user', 'assistant', 'user', 'assistant']
    assert client.get('/api/tutor/history?topic_id=3', headers=auth).get_json()['messages'] == []
    client.delete('/api/tutor/history?topic_id=2', headers=auth)
    assert client.get('/api/tutor/history?topic_id=2', headers=auth).get_json()['messages'] == []
