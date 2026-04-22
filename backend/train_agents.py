
import json
import os
from app import app, db
from models import AgentKnowledge, ContentLibrary
from datetime import datetime

def load_json(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return None

def train_teaching_agent():
    print("Training Teaching Agent...")
    data = load_json('agent_knowledge/knowledge_bases/teaching_strategies.json')
    if not data: return

    # Clear existing to avoid duplicates (for this script)
    AgentKnowledge.query.filter_by(agent_type='teaching').delete()
    
    count = 0
    # 1. Strategies
    for strategy in data.get('strategies', []):
        entry = AgentKnowledge(
            agent_type='teaching',
            knowledge_type='strategy',
            content=strategy,
            effectiveness_score=strategy.get('effectiveness_score', 0.5),
            usage_count=0
        )
        db.session.add(entry)
        count += 1
        
    # 2. Templates
    templates = data.get('lesson_templates', {})
    for name, template in templates.items():
        entry = AgentKnowledge(
            agent_type='teaching',
            knowledge_type='template',
            content={'name': name, 'template': template},
            effectiveness_score=0.8,
            usage_count=0
        )
        db.session.add(entry)
        count += 1
        
    print(f"  - Loaded {count} teaching knowledge items.")

def train_assessment_agent():
    print("Training Assessment Agent...")
    data = load_json('agent_knowledge/knowledge_bases/question_templates.json')
    if not data: return

    AgentKnowledge.query.filter_by(agent_type='assessment').delete()
    
    count = 0
    for template in data.get('templates', []):
        entry = AgentKnowledge(
            agent_type='assessment',
            knowledge_type='question_template',
            content=template,
            effectiveness_score=0.8,
            usage_count=0
        )
        db.session.add(entry)
        count += 1
        
    print(f"  - Loaded {count} assessment templates.")

def train_tutor_agent():
    print("Training Tutor Agent...")
    data = load_json('agent_knowledge/knowledge_bases/hint_strategies.json')
    if not data: return

    AgentKnowledge.query.filter_by(agent_type='tutor').delete()
    
    count = 0
    for strategy in data.get('strategies', []):
        entry = AgentKnowledge(
            agent_type='tutor',
            knowledge_type='hint_strategy',
            content=strategy,
            effectiveness_score=strategy.get('effectiveness_score', 0.5),
            usage_count=0
        )
        db.session.add(entry)
        count += 1
        
    print(f"  - Loaded {count} tutor strategies.")

def training_summary():
    print("\n" + "="*40)
    print("AGENT TRAINING COMPLETE")
    print("="*40)
    
    total_knowledge = AgentKnowledge.query.count()
    print(f"Total Knowledge Items in DB: {total_knowledge}")
    
    by_agent = db.session.query(AgentKnowledge.agent_type, db.func.count(AgentKnowledge.id)).group_by(AgentKnowledge.agent_type).all()
    for agent, count in by_agent:
        print(f"  - {agent.capitalize()} Agent: {count} items")
        
if __name__ == '__main__':
    with app.app_context():
        try:
            train_teaching_agent()
            train_assessment_agent()
            train_tutor_agent()
            
            db.session.commit()
            print("Database committed successfully.")
            
            training_summary()
            
        except Exception as e:
            db.session.rollback()
            print(f"Error during training: {str(e)}")
