"""Question bank, lesson cache and offline (no-LLM) content."""
import hashlib
import random
import re

from models import ContentLibrary, QuestionBank, QuizAttempt, db

LETTERS = ('A', 'B', 'C', 'D')


# ---------------------------------------------------------------- question bank

def question_hash(topic_id, text):
    norm = re.sub(r'\W+', ' ', text.lower()).strip()
    return hashlib.sha1(f'{topic_id}:{norm}'.encode()).hexdigest()


def validate_question(q):
    """Return a cleaned question dict or None if it is malformed."""
    options = q.get('options') or {}
    if hasattr(options, 'model_dump'):
        options = options.model_dump()
    if isinstance(options, list) and len(options) == 4:
        options = dict(zip(LETTERS, options))
    if set(options) != set(LETTERS) or not all(str(v).strip() for v in options.values()):
        return None
    if len({str(v).strip().lower() for v in options.values()}) < 4:
        return None
    answer = str(q.get('correct_answer', '')).strip().upper()[:1]
    if answer not in LETTERS or not str(q.get('question', '')).strip():
        return None
    difficulty = q.get('difficulty') if q.get('difficulty') in ('beginner', 'intermediate', 'advanced') else 'intermediate'
    return {
        'question': str(q['question']).strip(),
        'options': {k: str(options[k]).strip() for k in LETTERS},
        'correct_answer': answer,
        'explanation': str(q.get('explanation', '')).strip(),
        'difficulty': difficulty,
        'concept': str(q.get('concept', '') or '')[:120],
    }


def add_questions(topic_id, questions, source='llm'):
    added = []
    for raw in questions:
        q = validate_question(raw)
        if not q:
            continue
        h = question_hash(topic_id, q['question'])
        if QuestionBank.query.filter_by(question_hash=h).first():
            continue
        row = QuestionBank(topic_id=topic_id, question_hash=h, source=source, **q)
        db.session.add(row)
        added.append(row)
    db.session.flush()
    return added


def pick_questions(user_id, topic_id, mix, target_p=0.7, rng=None, allow_seen=False):
    """
    Assemble a quiz from the bank.
    mix: {difficulty: count}. Prefers questions the learner hasn't seen recently, and among those,
    items whose empirical success rate is closest to the target (desirable difficulty).
    Returns (rows, shortfall_by_difficulty).
    """
    rng = rng or random.Random()
    seen = {qid for (qid,) in db.session.query(QuizAttempt.question_id)
            .filter(QuizAttempt.user_id == user_id, QuizAttempt.topic_id == topic_id,
                    QuizAttempt.question_id.isnot(None)).all()}
    pool = QuestionBank.query.filter_by(topic_id=topic_id).all()
    chosen, shortfall = [], {}
    used = set()
    for difficulty, count in mix.items():
        if count <= 0:
            continue
        cands = [q for q in pool if q.difficulty == difficulty and q.id not in used
                 and (allow_seen or q.id not in seen)]
        cands.sort(key=lambda q: (abs(q.empirical_p_correct - target_p) + rng.random() * 0.15, q.times_served))
        take = cands[:count]
        chosen.extend(take)
        used.update(q.id for q in take)
        if len(take) < count:
            shortfall[difficulty] = count - len(take)
    return chosen, shortfall


def fill_from_any(user_id, topic_id, exclude_ids, n, rng=None):
    """Last resort when the bank is short and no LLM is available: reuse other questions."""
    rng = rng or random.Random()
    pool = [q for q in QuestionBank.query.filter_by(topic_id=topic_id).all() if q.id not in exclude_ids]
    rng.shuffle(pool)
    return pool[:n]


# ---------------------------------------------------------------- lesson cache

def lesson_cache_key(topic_id, complexity, strategy):
    return f'lesson:v2:{topic_id}:{complexity}:{strategy}'


def cached_lessons(key):
    return ContentLibrary.query.filter_by(content_type='lesson', cache_key=key).all()


def store_lesson(key, topic_id, complexity, lesson_dict, markdown):
    row = ContentLibrary(topic_id=topic_id, content_type='lesson', cache_key=key, difficulty=complexity,
                         content=markdown, meta_data=lesson_dict, usage_count=1)
    db.session.add(row)
    db.session.flush()
    return row


def get_text_cache(key):
    row = ContentLibrary.query.filter_by(content_type='text', cache_key=key).first()
    return row.content if row else None


def set_text_cache(key, text):
    db.session.add(ContentLibrary(content_type='text', cache_key=key, content=text))
    db.session.flush()


# ---------------------------------------------------------------- rendering

def lesson_to_markdown(lesson):
    parts = [f"# {lesson['title']}", lesson.get('summary', '')]
    if lesson.get('objectives'):
        parts.append('## Learning objectives\n' + '\n'.join(f'- {o}' for o in lesson['objectives']))
    for s in lesson.get('sections', []):
        parts.append(f"## {s['title']}\n{s['body_markdown']}")
    for ex in lesson.get('code_examples', []):
        parts.append(f"### {ex['title']}\n```{ex.get('language', 'python')}\n{ex['code']}\n```\n{ex['explanation']}")
    if lesson.get('key_takeaways'):
        parts.append('## Key takeaways\n' + '\n'.join(f'- {t}' for t in lesson['key_takeaways']))
    p = lesson.get('practice')
    if p:
        parts.append(f"## Practice challenge\n{p['prompt']}\n\n**Expected output:** `{p['expected_output']}`")
    return '\n\n'.join(x for x in parts if x)


# ---------------------------------------------------------------- offline content

STARTERS = {
    'Programming': ('# TODO: complete the function\n'
                    'def solve(values):\n'
                    '    # your code here\n'
                    '    return sum(values)\n\n'
                    'print(solve([3, 4, 5]))\n', '12'),
    'AI/ML': ('# TODO: compute the mean and variance without libraries\n'
              'data = [2, 4, 4, 4, 5, 5, 7, 9]\n'
              'mean = sum(data) / len(data)\n'
              'var = sum((x - mean) ** 2 for x in data) / len(data)\n'
              'print(mean, var)\n', '5.0 4.0'),
    'Database': ('# Model rows as dicts and "query" them\n'
                 'users = [{"id": 1, "name": "Ada"}, {"id": 2, "name": "Linus"}]\n'
                 'print([u["name"] for u in users if u["id"] == 2])\n', "['Linus']"),
    'Web': ('# Build an HTML string from data\n'
            'items = ["Home", "About", "Contact"]\n'
            'html = "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"\n'
            'print(html)\n', '<ul><li>Home</li><li>About</li><li>Contact</li></ul>'),
}


def md_escape(text):
    return re.sub(r'([\\`*_{}\[\]<>#|])', r'\\\1', text)


def offline_lesson(topic, complexity, strategy_name):
    """Deterministic lesson built from the curriculum when no LLM is configured or it fails."""
    concepts = topic.key_concepts or [topic.name]
    starter, expected = STARTERS.get(topic.category, STARTERS['Programming'])
    depth = {'beginner': 'from first principles', 'intermediate': 'with practical patterns',
             'advanced': 'with edge cases and trade-offs'}[complexity if complexity in ('beginner', 'intermediate', 'advanced') else 'beginner']
    sections = [{
        'title': 'Why this matters',
        'body_markdown': f"{topic.description} In this lesson we study **{topic.name}** {depth}, "
                         f"using a *{strategy_name.replace('_', ' ')}* approach.",
    }]
    for c in concepts:
        safe = md_escape(c)
        sections.append({
            'title': c[:1].upper() + c[1:],
            'body_markdown': f"**{safe}** is a core idea in {topic.name}. Try to explain it in your own words, "
                             f"then find one real example of it in code or in a tool you use. "
                             f"Ask the AI tutor on this page to go deeper on *{safe}*.",
        })
    return {
        'title': f'{topic.name}: {complexity.title()} lesson',
        'summary': f'A structured walkthrough of {topic.name}. (Offline mode: configure GEMINI_API_KEY for richer, AI-generated lessons.)',
        'objectives': [f'Explain {c}' for c in concepts[:3]] + [f'Apply {topic.name} in a short exercise'],
        'sections': sections,
        'code_examples': [{'title': 'Warm-up', 'code': starter, 'language': 'python',
                           'explanation': 'Run this in the playground below, then modify it.'}],
        'key_takeaways': [f'{c[:1].upper() + c[1:]} is essential to {topic.name}.' for c in concepts[:4]],
        'practice': {'prompt': f'Complete the starter code to practise {topic.name}.', 'starter_code': starter,
                     'expected_output': expected,
                     'hints': ['Read the TODO comment carefully.', 'Print intermediate values to debug.',
                               'Compare your output with the expected output character by character.']},
        'estimated_minutes': {'beginner': 10, 'intermediate': 15, 'advanced': 20}.get(complexity, 10),
    }
