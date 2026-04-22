from flask import Flask, request, jsonify, session
from flask_cors import CORS
from models import db, User, Topic, KnowledgeState, LearningSession, QuizAttempt
from knowledge_tracker import KnowledgeTracker
from llm_service import LLMService
from config import Config
from agents.coordinator_agent import CoordinatorAgent
import os
from datetime import datetime
import re

app = Flask(__name__)
app.config.from_object(Config)

# UPDATED CORS CONFIGURATION
CORS(app, 
     supports_credentials=True,
     origins=['http://localhost:3000', 'https://adaptive-e-learning-system.vercel.app'], # placeholder - will improve with regex or wildcard
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

db.init_app(app)

# Initialize agents and services

knowledge_tracker = KnowledgeTracker()
llm_service = LLMService()
coordinator = CoordinatorAgent()

# Initialize database and sample data
def init_db():
    with app.app_context():
        db.create_all()
        
        # Create sample topics if none exist
        if Topic.query.count() == 0:
            sample_topics = [
                Topic(name="Python Basics", category="Programming", difficulty="beginner",
                      description="Introduction to Python programming"),
                Topic(name="Data Structures", category="Programming", difficulty="intermediate",
                      description="Learn about arrays, lists, stacks, and queues", prerequisites="1"),
                Topic(name="Object-Oriented Programming", category="Programming", difficulty="intermediate",
                      description="Classes, objects, inheritance, and polymorphism", prerequisites="1"),
                Topic(name="Algorithms", category="Programming", difficulty="advanced",
                      description="Sorting, searching, and algorithm complexity", prerequisites="2"),
                Topic(name="Machine Learning Basics", category="AI/ML", difficulty="intermediate",
                      description="Introduction to ML concepts and algorithms", prerequisites="1,2"),
                Topic(name="Web Development", category="Web", difficulty="beginner",
                      description="HTML, CSS, and JavaScript fundamentals"),
                Topic(name="Database Design", category="Database", difficulty="intermediate",
                      description="SQL and database normalization", prerequisites="1"),
                Topic(name="Neural Networks", category="AI/ML", difficulty="advanced",
                      description="Deep learning and neural network architectures", prerequisites="5"),
            ]
            db.session.bulk_save_objects(sample_topics)
            db.session.commit()

# UPDATED: Root route now returns API info instead of template
@app.route('/')
def index():
    return jsonify({
        'message': 'Adaptive E-Learning API',
        'version': '1.0.0',
        'status': 'running',
        'ai_agents': '5 autonomous agents active',
        'endpoints': {
            'auth': '/api/login, /api/register, /api/logout, /api/current-user',
            'topics': '/api/topics, /api/topics/<id>',
            'learning': '/api/generate-lesson',
            'quiz': '/api/generate-quiz, /api/submit-answer',
            'progress': '/api/progress-summary, /api/knowledge-state/<id>',
            'utility': '/api/check-code, /api/ask-challenge-hint, /api/agent-status'
        }
    })

# REMOVED: All HTML template routes (dashboard, learn, quiz, progress)
# React frontend handles all routing

# API Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    
    existing_user = User.query.filter_by(username=data['username']).first()
    if existing_user:
        return jsonify({'error': 'Username already exists'}), 400
    
    user = User(
        username=data['username'],
        email=data['email']
    )
    db.session.add(user)
    db.session.commit()
    
    session['user_id'] = user.id
    session['username'] = user.username
    
    return jsonify({
        'message': 'User registered successfully',
        'user_id': user.id,
        'username': user.username
    })

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    
    if user:
        session['user_id'] = user.id
        session['username'] = user.username
        return jsonify({
            'message': 'Login successful',
            'user_id': user.id,
            'username': user.username
        })
    else:
        return jsonify({'error': 'User not found'}), 404

@app.route('/api/current-user', methods=['GET'])
def current_user():
    if 'user_id' in session:
        return jsonify({
            'user_id': session['user_id'],
            'username': session['username']
        })
    return jsonify({'error': 'Not logged in'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'})

@app.route('/api/topics', methods=['GET'])
def get_topics():
    topics = Topic.query.all()
    return jsonify([{
        'id': t.id,
        'name': t.name,
        'category': t.category,
        'difficulty': t.difficulty,
        'description': t.description
    } for t in topics])

@app.route('/api/topics/<int:topic_id>', methods=['GET'])
def get_topic(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    return jsonify({
        'id': topic.id,
        'name': topic.name,
        'category': topic.category,
        'difficulty': topic.difficulty,
        'description': topic.description
    })

def format_lesson_content(content):
    """Format lesson content for better display"""
    import re
    
    # Remove multiple consecutive blank lines
    content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
    
    # Remove extra whitespace from each line
    content = '\n'.join(line.strip() for line in content.split('\n'))
    
    # Convert markdown code blocks to HTML
    content = re.sub(r'```python\n(.*?)\n```', r'<pre><code class="python">\1</code></pre>', content, flags=re.DOTALL)
    content = re.sub(r'```\n(.*?)\n```', r'<pre><code>\1</code></pre>', content, flags=re.DOTALL)
    
    # Convert markdown headers to HTML
    content = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
    content = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', content, flags=re.MULTILINE)
    content = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', content, flags=re.MULTILINE)
    
    # Convert markdown bold to HTML
    content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
    
    # Convert inline code to HTML (before lists to preserve code in lists)
    content = re.sub(r'`([^`]+)`', r'<code>\1</code>', content)
    
    # Convert markdown lists to HTML - IMPROVED
    lines = content.split('\n')
    in_list = False
    result_lines = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Skip empty lines
        if not line:
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            continue
        
        # Handle list items
        if line.startswith('- '):
            if not in_list:
                result_lines.append('<ul>')
                in_list = True
            result_lines.append(f'<li>{line[2:]}</li>')
        else:
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            result_lines.append(line)
    
    if in_list:
        result_lines.append('</ul>')
    
    content = '\n'.join(result_lines)
    
    # Convert paragraphs - NO NEWLINES
    lines = content.split('\n')
    formatted_lines = []
    in_pre = False
    
    for line in lines:
        line = line.strip()
        
        # Skip completely empty lines
        if not line:
            continue
        
        # Handle pre blocks
        if '<pre>' in line:
            in_pre = True
            formatted_lines.append(line)
            continue
        elif '</pre>' in line:
            in_pre = False
            formatted_lines.append(line)
            continue
        elif in_pre:
            formatted_lines.append(line)
            continue
        
        # Keep HTML tags as-is
        if line.startswith('<h') or line.startswith('<ul>') or line.startswith('</ul>') or line.startswith('<li>'):
            formatted_lines.append(line)
        else:
            # Wrap non-HTML content in paragraph
            formatted_lines.append(f'<p>{line}</p>')
    
    # Join WITHOUT newlines to eliminate all spacing
    return ''.join(formatted_lines)

def format_study_tips(content):
    """Format study tips markdown to HTML"""
    import re
    
    # Convert **bold** to HTML
    content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
    
    # Convert bullet points to HTML list
    lines = content.split('\n')
    formatted_lines = []
    in_list = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if it's a header
        if line.endswith(':') and not line.startswith('-') and not line.startswith('•'):
            if in_list:
                formatted_lines.append('</ul>')
                in_list = False
            formatted_lines.append(f'<h3 style="color: var(--primary-color); margin-top: 1.5rem; margin-bottom: 0.75rem;">{line}</h3>')
        # Check if it's a bullet point
        elif line.startswith('- ') or line.startswith('• '):
            if not in_list:
                formatted_lines.append('<ul style="list-style-type: disc; margin-left: 1.5rem; line-height: 1.8;">')
                in_list = True
            # Remove the bullet character
            text = line[2:] if line.startswith('- ') else line[2:]
            formatted_lines.append(f'<li style="margin-bottom: 1rem; color: #4b5563;">{text}</li>')
        else:
            if in_list:
                formatted_lines.append('</ul>')
                in_list = False
            formatted_lines.append(f'<p style="margin-bottom: 0.75rem; color: #4b5563;">{line}</p>')
    
    if in_list:
        formatted_lines.append('</ul>')
    
    return ''.join(formatted_lines)

@app.route('/api/generate-lesson', methods=['POST'])
def generate_lesson():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.json
    topic_id = data['topic_id']
    
    # Use Coordinator Agent
    result = coordinator.perceive({
        'task': 'generate_lesson',
        'user_id': session['user_id'],
        'context': {
            'topic_id': topic_id,
            'learning_history': []
        }
    }).decide().act()
    
    if not result['success']:
        return jsonify({'error': result.get('error')}), 500
    
    # Extract teaching agent result
    teaching_result = result['results'].get('TeachingAgent', {})
    
    # Format content
    content = format_lesson_content(teaching_result.get('content', ''))
    
    # Save to database
    topic = Topic.query.get(topic_id)
    
    learning_session = LearningSession(
        user_id=session['user_id'],
        topic_id=topic_id,
        content=content,
        difficulty=teaching_result.get('metadata', {}).get('complexity', 'beginner')
    )
    db.session.add(learning_session)
    db.session.commit()
    
    return jsonify({
        'content': content,
        'difficulty': teaching_result.get('metadata', {}).get('complexity'),
        'knowledge_level': teaching_result.get('metadata', {}).get('knowledge_level', 0),
        'topic_name': topic.name,
        'agent_metadata': teaching_result.get('metadata', {})
    })

@app.route('/api/generate-quiz', methods=['POST'])
def generate_quiz():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.json
    topic_id = data['topic_id']
    
    # Use Coordinator Agent
    result = coordinator.perceive({
        'task': 'generate_quiz',
        'user_id': session['user_id'],
        'context': {
            'topic_id': topic_id,
            'recent_performance': []
        }
    }).decide().act()
    
    if not result['success']:
        return jsonify({'error': result.get('error')}), 500
    
    assessment_result = result['results'].get('AssessmentAgent', {})
    
    topic = Topic.query.get(topic_id)
    
    return jsonify({
        'questions': assessment_result.get('questions', []),
        'difficulty': 'adaptive',
        'topic_name': topic.name,
        'topic_id': topic_id,
        'agent_metadata': assessment_result.get('metadata', {})
    })

@app.route('/api/submit-answer', methods=['POST'])
def submit_answer():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.json
    topic_id = data['topic_id']
    question = data['question']
    user_answer = data['user_answer']
    correct_answer = data['correct_answer']
    difficulty = data['difficulty']
    
    is_correct = user_answer == correct_answer
    
    # Save quiz attempt
    attempt = QuizAttempt(
        user_id=session['user_id'],
        topic_id=topic_id,
        question=question,
        user_answer=user_answer,
        correct_answer=correct_answer,
        is_correct=is_correct,
        difficulty=difficulty
    )
    db.session.add(attempt)
    db.session.commit()
    
    # Update knowledge state
    state = knowledge_tracker.update_knowledge(
        session['user_id'],
        topic_id,
        is_correct,
        difficulty
    )
    
    # Generate explanation
    topic = Topic.query.get(topic_id)
    explanation = llm_service.explain_answer(
        question,
        user_answer,
        correct_answer,
        topic.name
    )
    
    return jsonify({
        'is_correct': is_correct,
        'explanation': explanation,
        'new_knowledge_level': state.knowledge_level,
        'confidence': state.confidence
    })

@app.route('/api/knowledge-state/<int:topic_id>', methods=['GET'])
def get_knowledge_state(topic_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    state = knowledge_tracker.get_or_create_knowledge_state(
        session['user_id'], topic_id
    )
    
    topic = Topic.query.get(topic_id)
    
    return jsonify({
        'topic_id': topic_id,
        'topic_name': topic.name,
        'knowledge_level': state.knowledge_level,
        'confidence': state.confidence,
        'practice_count': state.practice_count,
        'last_practiced': state.last_practiced.isoformat()
    })

@app.route('/api/progress-summary', methods=['GET'])
def get_progress_summary():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    summary = knowledge_tracker.get_progress_summary(session['user_id'])
    
    # Enhance with topic names
    for topic_list in ['weak_topics', 'strong_topics']:
        for item in summary[topic_list]:
            topic = Topic.query.get(item['id'])
            if topic:
                item['name'] = topic.name
    
    return jsonify(summary)

@app.route('/api/next-topic', methods=['GET'])
def get_next_topic():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    current_topic_id = request.args.get('current_topic_id', type=int)
    
    # Use Coordinator Agent
    result = coordinator.perceive({
        'task': 'recommend_topic',
        'user_id': session['user_id'],
        'context': {
            'current_topic_id': current_topic_id
        }
    }).decide().act()
    
    if not result['success']:
        return jsonify({'message': 'No recommendations'}), 404
    
    recommendation_result = result['results'].get('RecommendationAgent', {})
    next_best = recommendation_result.get('next_best')
    
    if next_best:
        return jsonify({
            'id': next_best['topic_id'],
            'name': next_best['name'],
            'category': next_best['category'],
            'difficulty': next_best['difficulty'],
            'description': next_best['reason'],
            'agent_recommendation': True
        })
    
    return jsonify({'message': 'No recommendations available'}), 404

@app.route('/api/study-tips', methods=['GET'])
def get_study_tips():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    summary = knowledge_tracker.get_progress_summary(session['user_id'])
    
    weak_topic_names = []
    strong_topic_names = []
    
    for item in summary['weak_topics']:
        topic = Topic.query.get(item['id'])
        if topic:
            weak_topic_names.append(topic.name)
    
    for item in summary['strong_topics']:
        topic = Topic.query.get(item['id'])
        if topic:
            strong_topic_names.append(topic.name)
    
    tips = llm_service.generate_study_tips(weak_topic_names, strong_topic_names)
    
    # Format the tips
    formatted_tips = format_study_tips(tips)
    
    return jsonify({'tips': formatted_tips})

@app.route('/api/check-code', methods=['POST'])
def check_code():
    """Execute Python code safely and return output"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.json
    user_code = data.get('code', '')
    
    # Security: limit execution time and dangerous operations
    if any(keyword in user_code.lower() for keyword in ['import os', 'import sys', 'eval', 'exec', 'open', 'file', '__import__']):
        return jsonify({
            'success': False,
            'output': 'Error: Restricted operations detected. Please use only basic Python syntax.',
            'error': True
        })
    
    try:
        # Capture output
        import io
        import sys
        from contextlib import redirect_stdout
        
        output_buffer = io.StringIO()
        
        with redirect_stdout(output_buffer):
            # Create a restricted namespace
            namespace = {'__builtins__': {
                'print': print,
                'input': lambda x='': '',
                'len': len,
                'range': range,
                'str': str,
                'int': int,
                'float': float,
                'list': list,
                'dict': dict,
                'set': set,
                'tuple': tuple,
                'sum': sum,
                'max': max,
                'min': min,
                'abs': abs,
                'round': round,
            }}
            
            # Execute code
            exec(user_code, namespace)
        
        output = output_buffer.getvalue()
        
        return jsonify({
            'success': True,
            'output': output if output else 'Code executed successfully (no output)',
            'error': False
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'output': f'Error: {str(e)}',
            'error': True
        })

@app.route('/api/ask-challenge-hint', methods=['POST'])
def ask_challenge_hint():
    """Get hint for practice challenge using LLM"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.json
    
    # Use Coordinator Agent with Tutor Agent
    result = coordinator.perceive({
        'task': 'provide_hint',
        'user_id': session['user_id'],
        'context': {
            'question': data.get('question'),
            'challenge': data.get('challenge'),
            'attempt_count': data.get('attempt_count', 1),
            'frustration_level': 'normal'
        }
    }).decide().act()
    
    if not result['success']:
        return jsonify({'hint': 'Break the problem into smaller steps!'}), 200
    
    tutor_result = result['results']
    
    return jsonify({
        'hint': tutor_result.get('hint'),
        'hint_level': tutor_result.get('hint_level'),
        'agent': tutor_result.get('agent')
    })

@app.route('/api/agent-status', methods=['GET'])
def get_agent_status():
    """Get status of all agents"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    status = coordinator.get_agent_status()
    return jsonify(status)

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 7860))
    app.run(debug=True, host='0.0.0.0', port=port)