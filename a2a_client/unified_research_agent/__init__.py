"""UnifiedResearch Agent - Google ADK 기반 오케스트레이터 에이전트"""

# ADK에서 agent를 찾을 수 있도록 agent.py의 root_agent를 export
from .agent import root_agent

__all__ = ['root_agent']