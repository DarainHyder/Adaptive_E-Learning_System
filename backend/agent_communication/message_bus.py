from datetime import datetime
from models import db, AgentMessage
import json

class AgentMessageBus:
    """
    Central message bus for inter-agent communication.
    Allows agents to subscribe to topics and send direct messages.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentMessageBus, cls).__new__(cls)
            cls._instance.subscribers = {}  # agent_id -> callback
        return cls._instance
        
    def subscribe(self, agent_id, callback):
        """
        Register an agent to receive messages.
        
        Args:
            agent_id (str): The ID of the receiving agent.
            callback (func): Function to call when message arrives.
        """
        self.subscribers[agent_id] = callback
        print(f"Agent {agent_id} subscribed to message bus.")
    
    def send_message(self, from_agent, to_agent, message_type, content):
        """
        Send a message from one agent to another.
        """
        # Create persistent record
        try:
            message = AgentMessage(
                from_agent=from_agent,
                to_agent=to_agent,
                message_type=message_type,
                content=content,
                status='pending'
            )
            # Use application context if running within request
            if db.session:
                db.session.add(message)
                db.session.commit()
        except Exception as e:
            print(f"Warning: Could not save message to DB: {e}")
            message = AgentMessage(
                from_agent=from_agent,
                to_agent=to_agent,
                message_type=message_type,
                content=content,
                status='pending'
            )
        
        # Direct delivery if subscriber exists (Synchronous for now)
        if to_agent in self.subscribers:
            try:
                response = self.subscribers[to_agent](message)
                
                # Update status
                if db.session:
                    message.status = 'processed'
                    message.processed_at = datetime.utcnow()
                    db.session.commit()
                    
                return response
            except Exception as e:
                print(f"Error delivering message to {to_agent}: {e}")
                if db.session:
                    message.status = 'failed'
                    db.session.commit()
                return None
        else:
            print(f"Agent {to_agent} not found or offline.")
            return None
    
    def broadcast(self, from_agent, message_type, content):
        """
        Send a message to all subscribed agents (except sender).
        """
        responses = {}
        for agent_id in self.subscribers:
            if agent_id != from_agent:
                response = self.send_message(from_agent, agent_id, message_type, content)
                responses[agent_id] = response
        return responses
