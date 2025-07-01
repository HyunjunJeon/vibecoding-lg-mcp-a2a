"""UnifiedResearch Agent - 레거시 호환성을 위한 래퍼"""

from unified_research_agent.api_server import app
from unified_research_agent.models import ResearchRequest, ResearchResult
from unified_research_agent.agent import root_agent

# 레거시 호환성을 위한 export
__all__ = [
    "app",
    "ResearchRequest", 
    "ResearchResult",
    "root_agent"
]

# FastAPI 앱은 api_server.py에서 직접 실행
# uvicorn unified_research_agent.api_server:app --reload