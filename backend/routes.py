"""HTTP API. Response shapes of the v1 endpoints are preserved (plus new fields)."""
import hashlib
import re
from datetime import datetime, timedelta

from flask import Blueprint, current_app, g, jsonify, request, session
from langchain_core.messages import HumanMessage, SystemMessage

from agents.metrics import METRICS
from agents.recommendation_agent import learning_path, score_topics
from models import LearningSession, QuestionBank, QuizAttempt, Topic, User, db, ContentLibrary
from services import content
from services.auth import current_user_id, issue_token, login_required, rate_limited
from services.sandbox import run_code

api = Blueprint('api', __name__)

USERNAME_RE = re.compile(r'^[A-Za-z0-9_.-]{3,40}$')
EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
BANDIT_WINDOW = timedelta(hours=48)
BANDIT_MAX_REWARDS_PER_LESSON = 6


def svc():
    return current_app.extensions['elearn']


def body():
    return request.get_json(silent=True) or {}


def get_topic_or_404(topic_id):
    topic = db.session.get(Topic, int(topic_id)) if str(topic_id).isdigit() else None
    if topic is None:
        return None, (jsonify({'error': 'Topic not found'}), 404)
    return topic, None


# ------------------------------------------------------------------ meta

@api.get('/')
def index():
    s = svc()
    return jsonify({
        'message': 'Adaptive E-Learning API',
        'version': '2.0.0',
        'status': 'running',
        'ai_agents': 'LangGraph multi-agent system: coordinator + knowledge, teaching, assessment, tutor, recommendation',
        'llm': s.llm.info(),
        'knowledge_model': s.knowledge.kt.meta.get('architecture', 'bkt') if s.knowledge.kt.available else 'bkt',
        'endpoints': sorted(str(r) for r in current_app.url_map.iter_rules() if str(r).startswith('/api')),
    })


@api.get('/api/health')
def health():
    db.session.execute(db.text('SELECT 1'))
    return jsonify({'status': 'ok', 'time': datetime.utcnow().isoformat(timespec='seconds')})


# ------------------------------------------------------------------ auth

def _auth_response(user, message, status=200):
    session['user_id'] = user.id
    return jsonify({'message': message, 'token': issue_token(user.id), **user.to_dict()}), status


@api.post('/api/register')
def register():
    data = body()
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    if not USERNAME_RE.match(username):
        return jsonify({'error': 'Username must be 3-40 characters (letters, numbers, _ . -)'}), 400
    if not EMAIL_RE.match(email):
        return jsonify({'error': 'Please enter a valid email address'}), 400
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400
    user = User(username=username, email=email, learning_style=data.get('learning_style') or 'mixed', goals=[])
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return _auth_response(user, 'User registered successfully', 201)


@api.post('/api/login')
def login():
    data = body()
    user = User.query.filter_by(username=(data.get('username') or '').strip()).first()
    password = data.get('password') or ''
    if user and user.password_hash is None and len(password) >= 8:
        # v1 accounts had no password: the first login sets it.
        user.set_password(password)
        db.session.commit()
        return _auth_response(user, 'Password set; login successful')
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid username or password'}), 401
    return _auth_response(user, 'Login successful')


@api.get('/api/current-user')
def current_user():
    uid = current_user_id()
    user = db.session.get(User, uid) if uid else None
    if not user:
        return jsonify({'error': 'Not logged in'}), 401
    return jsonify(user.to_dict())


@api.post('/api/logout')
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'})


@api.put('/api/profile')
@login_required
def update_profile():
    data = body()
    user = db.session.get(User, g.user_id)
    if data.get('learning_style') in ('visual', 'reading', 'kinesthetic', 'auditory', 'mixed'):
        user.learning_style = data['learning_style']
    if isinstance(data.get('goals'), list):
        user.goals = [str(x)[:60] for x in data['goals'][:10]]
    db.session.commit()
    return jsonify(user.to_dict())


# ------------------------------------------------------------------ topics

@api.get('/api/topics')
def get_topics():
    return jsonify([t.to_dict() for t in Topic.query.order_by(Topic.position, Topic.id).all()])


@api.get('/api/topics/<int:topic_id>')
def get_topic(topic_id):
    topic, err = get_topic_or_404(topic_id)
    return err or jsonify(topic.to_dict())


# ------------------------------------------------------------------ learning

def _user_prefs():
    user = db.session.get(User, g.user_id)
    return {'learning_style': user.learning_style or 'mixed', 'goals': user.goals or []}


@api.post('/api/generate-lesson')
@login_required
@rate_limited
def generate_lesson():
    data = body()
    topic, err = get_topic_or_404(data.get('topic_id'))
    if err:
        return err
    out = svc().coordinator.run('generate_lesson', g.user_id, topic.id, fresh=bool(data.get('fresh')), **_user_prefs())
    lesson, strategy = out['lesson'], out['strategy']
    ls = LearningSession(user_id=g.user_id, topic_id=topic.id, content=lesson['markdown'],
                         difficulty=strategy['complexity'], strategy=strategy['name'], context_bucket=strategy['bucket'])
    db.session.add(ls)
    db.session.commit()
    return jsonify({
        'content': lesson['markdown'],
        'lesson': lesson['lesson'],
        'source': lesson['source'],
        'session_id': ls.id,
        'difficulty': strategy['complexity'],
        'knowledge_level': strategy['knowledge_level'],
        'topic_name': topic.name,
        'agent_metadata': {
            'teaching_style': strategy['name'],
            'rule_choice': strategy['rule_choice'],
            'bandit_samples': strategy['bandit_samples'],
            'complexity': strategy['complexity'],
            'example_count': len(lesson['lesson'].get('code_examples', [])),
            'source': lesson['source'],
            'trace': out.get('trace', []),
        },
    })


@api.post('/api/generate-quiz')
@login_required
@rate_limited
def generate_quiz():
    data = body()
    topic, err = get_topic_or_404(data.get('topic_id'))
    if err:
        return err
    out = svc().coordinator.run('generate_quiz', g.user_id, topic.id)
    db.session.commit()
    quiz = out['quiz']
    if not quiz.get('questions'):
        return jsonify({'error': 'No questions available for this topic yet'}), 503
    return jsonify({
        'questions': quiz['questions'],
        'difficulty': 'adaptive',
        'topic_name': topic.name,
        'topic_id': topic.id,
        'agent_metadata': {**quiz['metadata'], 'trace': out.get('trace', [])},
    })


def _reward_teaching_strategy(user_id, topic_id, is_correct):
    """Credit the teaching strategy of the learner's latest lesson on this topic (bandit feedback)."""
    ls = (LearningSession.query.filter(LearningSession.user_id == user_id, LearningSession.topic_id == topic_id,
                                       LearningSession.strategy.isnot(None),
                                       LearningSession.created_at >= datetime.utcnow() - BANDIT_WINDOW)
          .order_by(LearningSession.created_at.desc()).first())
    if not ls or (ls.reward_count or 0) >= BANDIT_MAX_REWARDS_PER_LESSON:
        return None
    svc().bandit.update(ls.context_bucket or 'low', ls.strategy, 1.0 if is_correct else 0.0, weight=0.5)
    ls.reward_count = (ls.reward_count or 0) + 1
    ls.reward_sum = (ls.reward_sum or 0) + (1.0 if is_correct else 0.0)
    return ls.strategy


@api.post('/api/submit-answer')
@login_required
def submit_answer():
    data = body()
    topic, err = get_topic_or_404(data.get('topic_id'))
    if err:
        return err
    user_answer = str(data.get('user_answer') or '').strip().upper()[:1]
    q = db.session.get(QuestionBank, int(data['question_id'])) if str(data.get('question_id', '')).isdigit() else None
    if q is not None:
        if q.topic_id != topic.id:
            return jsonify({'error': 'Question does not belong to this topic'}), 400
        is_correct = user_answer == q.correct_answer
        difficulty, correct_answer, explanation, question_text = q.difficulty, q.correct_answer, q.explanation, q.question
        q.times_answered = (q.times_answered or 0) + 1
        q.times_correct = (q.times_correct or 0) + (1 if is_correct else 0)
    else:  # legacy payload (v1 frontend)
        correct_answer = str(data.get('correct_answer') or '').strip().upper()[:1]
        is_correct = bool(user_answer) and user_answer == correct_answer
        difficulty = data.get('difficulty') if data.get('difficulty') in ('beginner', 'intermediate', 'advanced') else 'intermediate'
        explanation = data.get('explanation') or f'The correct answer is {correct_answer}.'
        question_text = str(data.get('question') or '')[:2000] or 'n/a'

    db.session.add(QuizAttempt(user_id=g.user_id, topic_id=topic.id, question_id=q.id if q else None,
                               question=question_text, user_answer=user_answer, correct_answer=correct_answer,
                               is_correct=is_correct, difficulty=difficulty,
                               time_taken=int(data['time_taken']) if str(data.get('time_taken', '')).isdigit() else None))
    state = svc().knowledge.record_answer(g.user_id, topic, is_correct, difficulty)
    rewarded = _reward_teaching_strategy(g.user_id, topic.id, is_correct)
    db.session.commit()
    return jsonify({
        'is_correct': is_correct,
        'correct_answer': correct_answer,
        'explanation': explanation,
        'new_knowledge_level': round(state.knowledge_level, 4),
        'confidence': state.confidence,
        'rewarded_strategy': rewarded,
    })


# ------------------------------------------------------------------ progress

def _profile():
    return svc().knowledge.profile(g.user_id)


def _legacy_state(p):
    return {'topic_id': p['topic_id'], 'topic_name': p['name'], 'knowledge_level': p['effective_mastery'],
            'confidence': p['confidence'], 'practice_count': p['practice_count'],
            'last_practiced': p['last_practiced'], **p}


@api.get('/api/knowledge-state/<int:topic_id>')
@login_required
def get_knowledge_state(topic_id):
    p = _profile()['topics'].get(topic_id)
    if p is None:
        return jsonify({'error': 'Topic not found'}), 404
    return jsonify(_legacy_state(p))


@api.get('/api/knowledge-states')
@login_required
def get_knowledge_states():
    """Bulk endpoint: one request instead of one per topic."""
    prof = _profile()
    return jsonify({'model': prof['model'], 'states': [_legacy_state(p) for p in prof['topics'].values()]})


@api.get('/api/progress-summary')
@login_required
def progress_summary():
    prof = _profile()
    started = [p for p in prof['topics'].values() if p['practice_count']]
    simplify = lambda items: [{'id': p['topic_id'], 'name': p['name'], 'level': round(p['effective_mastery'], 2)} for p in items]
    return jsonify({
        'average_knowledge': round(prof['average_knowledge'], 2),
        'topics_mastered': sum(p['effective_mastery'] >= 0.8 for p in started),
        'topics_in_progress': sum(0 < p['effective_mastery'] < 0.8 for p in started),
        'topics_total': len(prof['topics']),
        'total_practice_count': sum(p['practice_count'] for p in started),
        'weak_topics': simplify(prof['weak_topics']),
        'strong_topics': simplify(prof['strong_topics']),
        'review_due': len(prof['review_queue']),
        'model': prof['model'],
    })


@api.get('/api/next-topic')
@login_required
def next_topic():
    out = svc().coordinator.run('recommend_topic', g.user_id,
                                current_topic_id=request.args.get('current_topic_id', type=int), **_user_prefs())
    best = out['recommendations'].get('next_best')
    if not best:
        return jsonify({'message': 'No recommendations available'}), 404
    return jsonify({'id': best['topic_id'], 'name': best['name'], 'category': best['category'],
                    'difficulty': best['difficulty'], 'description': best['description'],
                    'reason': best['reason'], 'agent_recommendation': True, **best})


@api.get('/api/recommendations')
@login_required
def recommendations():
    out = svc().coordinator.run('recommend_topic', g.user_id, **_user_prefs())
    return jsonify(out['recommendations'])


@api.get('/api/learning-path/<int:topic_id>')
@login_required
def get_learning_path(topic_id):
    topic, err = get_topic_or_404(topic_id)
    if err:
        return err
    topics = Topic.query.order_by(Topic.position, Topic.id).all()
    return jsonify(learning_path(_profile(), topics, topic.id))


@api.get('/api/review-queue')
@login_required
def review_queue():
    prof = _profile()
    return jsonify({'due': prof['review_queue'],
                    'upcoming': sorted((p for p in prof['topics'].values()
                                        if p['practice_count'] and not p['due_for_review']),
                                       key=lambda p: p['days_until_review'] or 0)[:5]})


def _fallback_tips(prof, nxt):
    tips = []
    for r in prof['review_queue'][:2]:
        tips.append(f"- **Review {r['name']}** today: your estimated recall is {r['recall']:.0%}. "
                    f"A short quiz now resets the forgetting curve.")
    for w in prof['weak_topics'][:2]:
        tips.append(f"- **Strengthen {w['name']}** ({w['effective_mastery']:.0%} mastery): re-read the lesson, "
                    f"then take a quiz. Quizzes adapt so you succeed about 70% of the time.")
    if nxt:
        tips.append(f"- **Next up: {nxt['name']}** ({nxt['reason'].lower()}).")
    tips.append('- **Practise actively**: run and modify the playground code instead of only reading it.')
    tips.append('- **Space your sessions**: 20-30 minutes daily beats one long weekly session.')
    return '\n'.join(tips[:5])


@api.get('/api/study-tips')
@login_required
def study_tips():
    prof = _profile()
    topics = Topic.query.order_by(Topic.position, Topic.id).all()
    ranked = score_topics(prof, topics)
    nxt = ranked[0] if ranked else None
    weak = [w['name'] for w in prof['weak_topics']]
    strong = [s['name'] for s in prof['strong_topics']]
    due = [r['name'] for r in prof['review_queue']]
    fingerprint = hashlib.sha1(repr((weak, strong, due, nxt and nxt['name'])).encode()).hexdigest()[:12]
    key = f'tips:{g.user_id}:{datetime.utcnow():%Y-%m-%d}:{fingerprint}'
    tips = content.get_text_cache(key)
    if tips is None:
        llm = svc().llm
        tips = llm.chat([
            SystemMessage('You are a learning coach. Reply ONLY with 3-5 Markdown bullet points ("- "), '
                          'each 1-2 sentences, using **bold** for key terms. Be specific and encouraging.'),
            HumanMessage(f'Weak areas: {weak or "none"}. Strong areas: {strong or "none"}. Due for review: '
                         f'{due or "none"}. Recommended next topic: {nxt["name"] if nxt else "n/a"}. '
                         f'Overall mastery {prof["average_knowledge"]:.0%}.'),
        ]) if llm.available else None
        tips = tips or _fallback_tips(prof, nxt)
        content.set_text_cache(key, tips)
        db.session.commit()
    return jsonify({'tips': tips, 'format': 'markdown'})


# ------------------------------------------------------------------ practice + tutor

@api.post('/api/check-code')
@login_required
@rate_limited
def check_code():
    cfg = current_app.config
    return jsonify(run_code(str(body().get('code') or ''), timeout_s=cfg['SANDBOX_TIMEOUT_S'],
                            memory_mb=cfg['SANDBOX_MEMORY_MB'], max_output=cfg['SANDBOX_MAX_OUTPUT'],
                            stdin=str(body().get('stdin') or '')))


@api.post('/api/ask-challenge-hint')
@login_required
@rate_limited
def ask_challenge_hint():
    data = body()
    topic_id = data.get('topic_id') if str(data.get('topic_id', '')).isdigit() else None
    out = svc().coordinator.run('provide_hint', g.user_id, int(topic_id) if topic_id else None,
                                question=data.get('question'), challenge=data.get('challenge'),
                                attempt_count=data.get('attempt_count', 1), last_output=data.get('last_output'),
                                practice_hints=data.get('practice_hints') or [])
    return jsonify(out['hint'])


@api.post('/api/tutor/chat')
@login_required
@rate_limited
def tutor_chat():
    data = body()
    message = str(data.get('message') or '').strip()
    if not message:
        return jsonify({'error': 'Message is empty'}), 400
    topic_id = int(data['topic_id']) if str(data.get('topic_id', '')).isdigit() else None
    reply = svc().tutor_chat.send(g.user_id, topic_id, message[:4000])
    return jsonify({'reply': reply, 'topic_id': topic_id})


@api.get('/api/tutor/history')
@login_required
def tutor_history():
    topic_id = request.args.get('topic_id', type=int)
    return jsonify({'messages': svc().tutor_chat.history(g.user_id, topic_id), 'topic_id': topic_id})


@api.delete('/api/tutor/history')
@login_required
def tutor_clear():
    svc().tutor_chat.clear(g.user_id, request.args.get('topic_id', type=int))
    return jsonify({'message': 'Conversation cleared'})


# ------------------------------------------------------------------ system

@api.get('/api/agent-status')
@login_required
def agent_status():
    agents, recent = METRICS.snapshot()
    coord = agents.pop('coordinator')
    return jsonify({
        'coordinator': {**coord, 'tasks_coordinated': coord['runs']},
        'sub_agents': agents,
        'total_memory': len(recent),
        'recent_activity': recent,
        'llm': svc().llm.info(),
        'framework': 'LangGraph',
    })


@api.get('/api/model-info')
def model_info():
    s = svc()
    return jsonify({
        'knowledge_tracing': {'available': s.knowledge.kt.available, **s.knowledge.kt.meta},
        'bkt_topics_fitted': len(s.knowledge.bkt.params),
        'teaching_bandit': s.bandit.summary(),
        'question_bank': {'total': QuestionBank.query.count(),
                          'llm_generated': QuestionBank.query.filter_by(source='llm').count()},
        'cached_lessons': ContentLibrary.query.filter_by(content_type='lesson').count(),
        'llm': s.llm.info(),
        'agent_graph_mermaid': s.coordinator.mermaid(),
    })
