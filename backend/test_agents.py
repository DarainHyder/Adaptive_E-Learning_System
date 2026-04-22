"""
Test script for agents
"""
from app import app, db
from agents.coordinator_agent import CoordinatorAgent
from models import User, Topic
import json

def test_lesson_generation():
    """Test Teaching Agent via Coordinator"""
    print("\n" + "="*60)
    print("TEST 1: Lesson Generation")
    print("="*60)
    
    with app.app_context():
        # Ensure test user exists
        user = User.query.filter_by(username='test_user').first()
        if not user:
            user = User(username='test_user', email='test@example.com')
            db.session.add(user)
            db.session.commit()
            print(f"[OK] Created test user: {user.username}")
        else:
            print(f"[OK] Using existing user: {user.username}")
        
        # Get first topic
        topic = Topic.query.first()
        print(f"[OK] Testing with topic: {topic.name}")
        
        # Test coordinator
        coordinator = CoordinatorAgent()
        
        result = coordinator.perceive({
            'task': 'generate_lesson',
            'user_id': user.id,
            'context': {
                'topic_id': topic.id,
                'learning_history': []
            }
        }).decide().act()
        
        print(f"\nResult:")
        print(f"  Success: {result['success']}")
        print(f"  Agents Used: {result.get('agents_used', [])}")
        print(f"  Workflow: {result.get('workflow', 'N/A')}")
        
        if result['success']:
            teaching_result = result['results'].get('TeachingAgent', {})
            content = teaching_result.get('content', '')
            content_preview = content[:200] if content else 'No content'
            print(f"\nContent Preview:")
            print(f"  {content_preview}...")
            print(f"\n[PASS] Test PASSED")
            return True
        else:
            print(f"\n[FAIL] Test FAILED: {result.get('error', 'Unknown error')}")
            return False

def test_quiz_generation():
    """Test Assessment Agent via Coordinator"""
    print("\n" + "="*60)
    print("TEST 2: Quiz Generation")
    print("="*60)
    
    with app.app_context():
        user = User.query.filter_by(username='test_user').first()
        topic = Topic.query.first()
        
        coordinator = CoordinatorAgent()
        
        result = coordinator.perceive({
            'task': 'generate_quiz',
            'user_id': user.id,
            'context': {
                'topic_id': topic.id,
                'recent_performance': []
            }
        }).decide().act()
        
        print(f"\nResult:")
        print(f"  Success: {result['success']}")
        print(f"  Agents Used: {result.get('agents_used', [])}")
        
        if result['success']:
            assessment_result = result['results'].get('AssessmentAgent', {})
            questions = assessment_result.get('questions', [])
            print(f"\nQuestions Generated: {len(questions)}")
            if questions:
                print(f"  Sample Question: {questions[0].get('question', '')}")
            print(f"\n[PASS] Test PASSED")
            return True
        else:
            print(f"\n[FAIL] Test FAILED: {result.get('error', 'Unknown error')}")
            return False

def test_hint_generation():
    """Test Tutor Agent via Coordinator"""
    print("\n" + "="*60)
    print("TEST 3: Hint Generation")
    print("="*60)
    
    with app.app_context():
        coordinator = CoordinatorAgent()
        
        result = coordinator.perceive({
            'task': 'provide_hint',
            'user_id': 1,
            'context': {
                'question': 'How do I use a for loop?',
                'challenge': 'Write a program to print numbers 1 to 10',
                'attempt_count': 1
            }
        }).decide().act()
        
        print(f"\nResult:")
        print(f"  Success: {result['success']}")
        
        if result['success']:
            hint = result['results'].get('hint', '')
            print(f"\nHint Generated:")
            print(f"  {hint}\n")
            print(f"[PASS] Test PASSED")
            return True
        else:
            print(f"\n[FAIL] Test FAILED: {result.get('error', 'Unknown error')}")
            return False

def test_recommendation():
    """Test Recommendation Agent via Coordinator"""
    print("\n" + "="*60)
    print("TEST 4: Topic Recommendation")
    print("="*60)
    
    with app.app_context():
        user = User.query.filter_by(username='test_user').first()
        
        coordinator = CoordinatorAgent()
        
        result = coordinator.perceive({
            'task': 'recommend_topic',
            'user_id': user.id,
            'context': {
                'current_topic_id': None
            }
        }).decide().act()
        
        print(f"\nResult:")
        print(f"  Success: {result['success']}")
        
        if result['success']:
            rec_result = result['results'].get('RecommendationAgent', {})
            next_best = rec_result.get('next_best')
            if next_best:
                print(f"\nRecommendation:")
                print(f"  Topic: {next_best['name']}")
                print(f"  Reason: {next_best['reason']}")
            print(f"\n[PASS] Test PASSED")
            return True
        else:
            print(f"\n[FAIL] Test FAILED")
            return False

def test_agent_status():
    """Test Agent Status Retrieval"""
    print("\n" + "="*60)
    print("TEST 5: Agent Status")
    print("="*60)
    
    with app.app_context():
        coordinator = CoordinatorAgent()
        
        # Run a task first
        coordinator.perceive({
            'task': 'provide_hint',
            'user_id': 1,
            'context': {'question': 'Test', 'challenge': 'Test'}
        }).decide().act()
        
        status = coordinator.get_agent_status()
        
        print(f"\nAgent Status:")
        print(f"  Coordinator Tasks: {status['coordinator']['tasks_coordinated']}")
        print(f"  Total Memory: {status['total_memory']}")
        print(f"\nSub-Agents:")
        
        for agent_name, stats in status['sub_agents'].items():
            print(f"    {agent_name.capitalize()}: State={stats['state']}")
        
        print(f"\n[PASS] Test PASSED")
        return True

def run_all_tests():
    """Run all agent tests"""
    print("\n" + "*"*60)
    print("MULTI-AGENT SYSTEM TEST SUITE")
    print("*"*60)
    
    # Store test results
    test_results = {}
    
    try:
        test_results['lesson'] = test_lesson_generation()
    except Exception as e:
        print(f"[FAIL] Lesson test failed: {e}")
        test_results['lesson'] = False
    
    try:
        test_results['quiz'] = test_quiz_generation()
    except Exception as e:
        print(f"[FAIL] Quiz test failed: {e}")
        test_results['quiz'] = False
    
    try:
        test_results['hint'] = test_hint_generation()
    except Exception as e:
        print(f"[FAIL] Hint test failed: {e}")
        test_results['hint'] = False
    
    try:
        test_results['recommendation'] = test_recommendation()
    except Exception as e:
        print(f"[FAIL] Recommendation test failed: {e}")
        test_results['recommendation'] = False
    
    try:
        test_results['status'] = test_agent_status()
    except Exception as e:
        print(f"[FAIL] Status test failed: {e}")
        test_results['status'] = False
    
    # Calculate summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in test_results.values() if result is True)
    total = len(test_results)
    failed = total - passed
    
    print(f"  Total Tests: {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    
    # Show details
    print(f"\n  Details:")
    for test_name, result in test_results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"    {test_name.capitalize()}: {status}")
    
    if passed == total:
        print("\n" + "="*60)
        print("ALL TESTS PASSED!")
        print("="*60 + "\n")
    else:
        print(f"\n{failed} test(s) failed. Check logs above.\n")
    
    print("="*60 + "\n")
    
    return passed == total

if __name__ == '__main__':
    all_passed = run_all_tests()
    exit(0 if all_passed else 1)