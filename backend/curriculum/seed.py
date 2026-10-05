"""Idempotent seeding of the curriculum and the starter question bank."""
import json
import os

from models import QuestionBank, Topic, db
from services.content import add_questions, question_hash

HERE = os.path.dirname(os.path.abspath(__file__))


def seed_curriculum():
    with open(os.path.join(HERE, 'curriculum.json')) as f:
        topics = json.load(f)['topics']

    # Upsert by slug, falling back to name so v1 databases keep their topic IDs.
    rows = {}
    for pos, t in enumerate(topics):
        row = Topic.query.filter_by(slug=t['slug']).first() or Topic.query.filter_by(name=t['name']).first()
        if row is None:
            row = Topic(name=t['name'])
            db.session.add(row)
        row.slug, row.name, row.category = t['slug'], t['name'], t['category']
        row.difficulty, row.description = t['difficulty'], t['description']
        row.key_concepts, row.position = t['key_concepts'], pos
        rows[t['slug']] = row
    db.session.flush()
    for t in topics:
        rows[t['slug']].prerequisites = ','.join(str(rows[p].id) for p in t['prerequisites'])
    db.session.commit()
    return rows


def seed_questions(rows):
    with open(os.path.join(HERE, 'seed_questions.json')) as f:
        bank = json.load(f)
    added = 0
    for slug, questions in bank.items():
        if slug not in rows:
            continue
        topic_id = rows[slug].id
        new = []
        for q in questions:
            # Seed questions are keyed by (topic, difficulty, concept): edited wording updates in place.
            row = QuestionBank.query.filter_by(topic_id=topic_id, source='seed', difficulty=q['difficulty'],
                                               concept=q['concept']).first()
            if row is None:
                new.append(q)
            elif row.question != q['question']:
                row.question, row.question_hash = q['question'], question_hash(topic_id, q['question'])
                row.options, row.correct_answer, row.explanation = q['options'], q['correct_answer'], q['explanation']
        added += len(add_questions(topic_id, new, source='seed'))
    db.session.commit()
    return added


def seed_all():
    rows = seed_curriculum()
    return seed_questions(rows)
