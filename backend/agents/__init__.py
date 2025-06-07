"""
Agent module for football panel discussions
"""
from .base_agent import BaseAgent
from .host_agent import HostAgent
from .coach_agent import CoachAgent
from .stats_agent import StatsAgent
from .fan_agent import FanAgent
from .learning_agent import LearningAgent

__all__ = [
    'BaseAgent',
    'HostAgent',
    'CoachAgent',
    'StatsAgent',
    'FanAgent',
    'LearningAgent'
] 