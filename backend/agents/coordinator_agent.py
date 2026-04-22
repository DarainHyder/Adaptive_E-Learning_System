"""
Coordinator Agent - Orchestrates all other agents
"""
from agents.base_agent import BaseAgent, StudentState
from agents.teaching_agent import TeachingAgent
from agents.assessment_agent import AssessmentAgent
from agents.knowledge_agent import KnowledgeAgent
from agents.tutor_agent import TutorAgent
from agents.recommendation_agent import RecommendationAgent
from datetime import datetime
import json

class CoordinatorAgent(BaseAgent):
    """
    Master agent that coordinates all other agents
    """
    
    def __init__(self):
        super().__init__("CA-001", "CoordinatorAgent")
        
        # Initialize all sub-agents
        self.teaching_agent = TeachingAgent()
        self.assessment_agent = AssessmentAgent()
        self.knowledge_agent = KnowledgeAgent()
        self.tutor_agent = TutorAgent()
        self.recommendation_agent = RecommendationAgent()
        
        self.tasks_coordinated = 0
        
        self.log("Coordinator initialized with 5 sub-agents")
    
    def perceive(self, environment):
        """
        Perceive global learning environment
        """
        self.update_state("perceiving")
        self.log(f"Coordinating agents for task: {environment.get('task')}")
        
        self.task = environment.get('task')
        self.user_id = environment.get('user_id')
        self.context = environment.get('context', {})
        
        return self
    
    def decide(self):
        """
        Decide which agents to activate
        """
        self.update_state("deciding")
        
        # Route to appropriate agents based on task
        self.active_agents = []
        
        if self.task == "generate_lesson":
            self.active_agents = [self.teaching_agent, self.knowledge_agent]
            self.workflow = "sequential"  # Knowledge first, then teaching
            
        elif self.task == "generate_quiz":
            self.active_agents = [self.knowledge_agent, self.assessment_agent]
            self.workflow = "sequential"
            
        elif self.task == "evaluate_answer":
            self.active_agents = [self.assessment_agent, self.knowledge_agent]
            self.workflow = "sequential"
            
        elif self.task == "provide_hint":
            self.active_agents = [self.tutor_agent]
            self.workflow = "single"
            
        elif self.task == "recommend_topic":
            self.active_agents = [self.knowledge_agent, self.recommendation_agent]
            self.workflow = "sequential"
            
        elif self.task == "full_learning_session":
            # Complex workflow involving all agents
            self.active_agents = [
                self.knowledge_agent,
                self.recommendation_agent,
                self.teaching_agent,
                self.assessment_agent,
                self.tutor_agent
            ]
            self.workflow = "complex"
        
        else:
            self.log(f"Unknown task: {self.task}", "warning")
            self.active_agents = []
            self.workflow = "none"
        
        self.log(f"Activating {len(self.active_agents)} agents in {self.workflow} workflow")
        
        return self
    
    def act(self):
        """
        Execute coordinated agent workflow
        """
        self.update_state("acting")
        self.log("Executing coordinated workflow...")
        
        results = {}
        
        try:
            # Create standardized student state
            student_state = StudentState(
                user_id=self.user_id,
                **self.context
            )
            
            # Fetch Topic object if ID is present
            current_topic = None
            if self.context.get('topic_id'):
                from models import Topic
                current_topic = Topic.query.get(self.context['topic_id'])
            
            if self.workflow == "single":
                # Single agent execution
                agent = self.active_agents[0]
                agent.perceive(student_state)
                agent.decide()
                
                # Handle specific agent signatures
                if isinstance(agent, TeachingAgent):
                    results = agent.act(topic=current_topic)
                elif isinstance(agent, AssessmentAgent):
                    results = agent.act(topic=current_topic)
                elif isinstance(agent, TutorAgent):
                    results = agent.act(prompt=self.context.get('question'))
                elif isinstance(agent, KnowledgeAgent):
                     # KnowledgeAgent act requires specific action type usually
                     # For general single execution, we assume a state update or status check
                     action = self.context.get('action_type', 'get_status')
                     results = agent.act(self.user_id, action_type=action, **self.context)
                elif isinstance(agent, RecommendationAgent):
                    results = agent.act()
                
            elif self.workflow == "sequential":
                # Sequential agent execution
                # Note: This generic loop is hard to maintain with diverse signatures.
                # We will customize it based on the specific sequence defined in decide()
                
                for i, agent in enumerate(self.active_agents):
                    self.log(f"Step {i+1}: Executing {agent.name}")
                    
                    # Update state with results from previous steps
                    for key, val in results.items():
                        setattr(student_state, key, val)
                    
                    agent.perceive(student_state)
                    agent.decide()
                    
                    agent_result = {}
                    if isinstance(agent, TeachingAgent):
                        # Teaching agent needs a topic. If not in context, maybe from previous agent?
                        topic_to_teach = current_topic
                        if 'next_best' in results: # From RecommendationAgent
                             # Mocking topic object from result dict if needed, or fetching DB
                             from models import Topic
                             topic_to_teach = Topic.query.get(results['next_best']['topic_id'])
                        
                        if topic_to_teach:
                            agent_result = agent.act(topic=topic_to_teach)
                        else:
                            self.log("TeachingAgent needs a topic but none provided", "error")
                            
                    elif isinstance(agent, AssessmentAgent):
                        agent_result = agent.act(topic=current_topic)
                    elif isinstance(agent, KnowledgeAgent):
                        # Sequential usually implies updating state after something
                        if 'quiz_score' in self.context:
                             agent_result = agent.act(self.user_id, 'update_state', 
                                                      topic_id=current_topic.id,
                                                      is_correct=self.context.get('is_correct'),
                                                      difficulty=current_topic.difficulty)
                        else:
                             agent_result = agent.act(self.user_id, 'get_weak_areas')

                    elif isinstance(agent, RecommendationAgent):
                        agent_result = agent.act()
                        
                    results[agent.name] = agent_result
                
            elif self.workflow == "complex":
                results = self._execute_complex_workflow(student_state, current_topic)
            
            self.tasks_coordinated += 1
            self.log(f"Workflow completed successfully")
            self.update_state("completed")
            
            return {
                "success": True,
                "results": results,
                "workflow": self.workflow
            }
            
        except Exception as e:
            self.log(f"Workflow error: {str(e)}", "error")
            return {"success": False, "error": str(e)}
    
    def _execute_complex_workflow(self, student_state, current_topic):
        """
        Execute complex multi-agent workflow
        """
        results = {}
        
        # Step 1: Knowledge Agent analyzes current state
        self.log("Complex workflow - Step 1: Knowledge analysis")
        self.knowledge_agent.perceive(student_state)
        # No decide/act needed for just analysis in this flow, but let's get weak areas
        knowledge_result = self.knowledge_agent.act(self.user_id, 'get_weak_areas')
        results['knowledge_analysis'] = knowledge_result
        
        # Step 2: Recommendation Agent suggests path
        self.log("Complex workflow - Step 2: Path recommendation")
        self.recommendation_agent.perceive(student_state)
        self.recommendation_agent.decide()
        recommendation_result = self.recommendation_agent.act()
        results['recommendations'] = recommendation_result
        
        # Step 3: Teaching Agent creates lesson
        if recommendation_result.get('next_best'):
            next_topic_data = recommendation_result['next_best']
            from models import Topic
            next_topic = Topic.query.get(next_topic_data['topic_id'])
            
            self.log("Complex workflow - Step 3: Lesson generation")
            # Update student state with specific topic context
            student_state.topic_id = next_topic.id
            student_state.knowledge_level = next_topic_data.get('current_knowledge', 0)
            
            self.teaching_agent.perceive(student_state)
            self.teaching_agent.decide()
            teaching_result = self.teaching_agent.act(topic=next_topic)
            results['lesson'] = teaching_result
            
            # Step 4: Assessment Agent prepares quiz for this new topic
            self.log("Complex workflow - Step 4: Assessment preparation")
            self.assessment_agent.perceive(student_state)
            self.assessment_agent.decide()
            assessment_result = self.assessment_agent.act(topic=next_topic)
            results['assessment'] = assessment_result
        
        return results
    
    def get_agent_status(self):
        """
        Get status of all agents
        """
        return {
            "coordinator": self.get_statistics(),
            "sub_agents": {
                "teaching": self.teaching_agent.get_statistics(),
                "assessment": self.assessment_agent.get_statistics(),
                "knowledge": self.knowledge_agent.get_statistics(),
                "tutor": self.tutor_agent.get_statistics(),
                "recommendation": self.recommendation_agent.get_statistics()
            },
            "total_memory": sum([
                len(self.teaching_agent.memory),
                len(self.assessment_agent.memory),
                len(self.knowledge_agent.memory),
                len(self.tutor_agent.memory),
                len(self.recommendation_agent.memory)
            ])
        }
    
    def get_statistics(self):
        """Return coordinator statistics"""
        return {
            "agent": self.name,
            "tasks_coordinated": self.tasks_coordinated,
            "state": self.state,
            "active_sub_agents": len(self.active_agents) if hasattr(self, 'active_agents') else 0,
            "memory_size": len(self.memory)
        }