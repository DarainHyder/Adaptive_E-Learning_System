"""
Base Agent Class - All agents inherit from this
"""
from abc import ABC, abstractmethod
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)

class StudentState:
    """Standardized student state object for agent perception"""
    def __init__(self, user_id, **kwargs):
        self.user_id = user_id
        for key, value in kwargs.items():
            setattr(self, key, value)

class BaseAgent(ABC):
    """Base class for all autonomous agents"""
    
    def __init__(self, agent_id, name):
        self.agent_id = agent_id
        self.name = name
        self.state = "idle"
        self.memory = []
        self.logger = logging.getLogger(f"Agent-{name}")
        self.created_at = datetime.utcnow()
        
    def log(self, message, level="info"):
        """Log agent activities"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent": self.name,
            "message": message,
            "state": self.state
        }
        self.memory.append(log_entry)
        
        if level == "info":
            self.logger.info(f"[{self.name}] {message}")
        elif level == "error":
            self.logger.error(f"[{self.name}] {message}")
        elif level == "warning":
            self.logger.warning(f"[{self.name}] {message}")
    
    def update_state(self, new_state):
        """Update agent state"""
        old_state = self.state
        self.state = new_state
        self.log(f"State transition: {old_state} → {new_state}")
    
    @abstractmethod
    def perceive(self, environment):
        """Perceive the environment - to be implemented by subclasses"""
        pass
    
    @abstractmethod
    def decide(self):
        """Make autonomous decisions - to be implemented by subclasses"""
        pass
    
    @abstractmethod
    def act(self):
        """Execute actions - to be implemented by subclasses"""
        pass
    
    def get_memory(self, limit=10):
        """Retrieve recent memory"""
        return self.memory[-limit:]
    
    def clear_memory(self):
        """Clear agent memory"""
        self.memory = []
        self.log("Memory cleared")