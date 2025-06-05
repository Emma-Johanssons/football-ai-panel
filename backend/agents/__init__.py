"""
Agent modules for football panel discussion
"""
from .base_agent import BaseAgent
from .host_agent import HostAgent
from .stats_agent import StatsAgent
from .coach_agent import CoachAgent
from .fan_agent import FanAgent
from .avatar_mapping import get_avatar_config

__all__ = [
    'BaseAgent',
    'HostAgent',
    'StatsAgent',
    'CoachAgent',
    'FanAgent',
    'get_avatar_config'
] 