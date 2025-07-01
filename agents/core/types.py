"""
공통 타입 정의 모듈
"""
from typing import TypedDict, List, Dict, Any, Optional, Annotated
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
import operator


class ReportFormat(str, Enum):
    """보고서 형식"""
    MARKDOWN = "markdown"
    PLAINTEXT = "plaintext"
    HTML = "html"


class ReportType(str, Enum):
    """보고서 타입"""
    IDEA_VALIDATION = "idea_validation"
    MARKET_RESEARCH = "market_research"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    INDUSTRY_ANALYSIS = "industry_analysis"
    CUSTOM = "custom"


class AgentType(str, Enum):
    """에이전트 타입"""
    WEB_SEARCH = "web_search"
    VECTOR_SEARCH = "vector_search"
    PLANNING = "planning"
    REPORT_WRITING = "report_writing"
    MEMORY = "memory"
    ORCHESTRATOR = "orchestrator"


class SearchResult(BaseModel):
    """검색 결과"""
    title: str
    url: str
    content: str
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VectorSearchResult(BaseModel):
    """벡터 검색 결과"""
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float = Field(ge=0.0, le=1.0)
    embedding: Optional[List[float]] = None


class ReportSection(BaseModel):
    """보고서 섹션"""
    title: str
    content: str
    order: int
    subsections: List['ReportSection'] = Field(default_factory=list)


class ReportOutline(BaseModel):
    """보고서 개요"""
    title: str
    description: str
    sections: List[ReportSection]
    estimated_length: int  # 예상 글자 수
    format: ReportFormat = ReportFormat.MARKDOWN


class ReportRequest(BaseModel):
    """보고서 요청"""
    topic: str
    report_type: ReportType
    format: ReportFormat = ReportFormat.MARKDOWN
    length: Optional[int] = None  # 원하는 글자 수
    include_citations: bool = True
    include_summary: bool = True
    include_visuals: bool = False
    custom_requirements: Optional[str] = None


class Report(BaseModel):
    """생성된 보고서"""
    id: str
    title: str
    content: str
    format: ReportFormat
    report_type: ReportType
    outline: ReportOutline
    citations: List[Dict[str, str]] = Field(default_factory=list)
    summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemoryEntry(BaseModel):
    """메모리 엔트리"""
    id: str
    user_id: str
    session_id: str
    content: str
    summary: str
    embedding: Optional[List[float]] = None
    importance_score: float = Field(ge=0.0, le=1.0)
    created_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


# LangGraph State 정의
class OrchestratorState(TypedDict):
    """오케스트레이터 상태"""
    # 사용자 입력
    user_request: str
    report_request: Optional[ReportRequest]
    
    # 검색 결과
    web_search_results: List[SearchResult]
    vector_search_results: List[VectorSearchResult]
    
    # 계획
    report_outline: Optional[ReportOutline]
    
    # 생성된 보고서
    report: Optional[Report]
    
    # 메모리
    memory_entries: List[MemoryEntry]
    
    # 메시지 히스토리
    messages: Annotated[List[BaseMessage], operator.add]
    
    # 현재 단계
    current_step: str
    
    # 에러
    error: Optional[str]


class WebSearchState(TypedDict):
    """웹 검색 에이전트 상태"""
    query: str
    filters: Dict[str, Any]
    results: List[SearchResult]
    messages: Annotated[List[BaseMessage], operator.add]


class VectorSearchState(TypedDict):
    """벡터 검색 에이전트 상태"""
    query: str
    collection_name: str
    top_k: int
    results: List[VectorSearchResult]
    messages: Annotated[List[BaseMessage], operator.add]


class PlanningState(TypedDict):
    """계획 에이전트 상태"""
    user_request: str
    report_type: ReportType
    report_format: ReportFormat
    context: Dict[str, Any]
    outline: Optional[ReportOutline]
    messages: Annotated[List[BaseMessage], operator.add]


class ReportWritingState(TypedDict):
    """보고서 작성 에이전트 상태"""
    outline: ReportOutline
    search_results: List[Dict[str, Any]]
    report: Optional[Report]
    messages: Annotated[List[BaseMessage], operator.add]


class MemoryState(TypedDict):
    """메모리 에이전트 상태"""
    user_id: str
    session_id: str
    conversation: List[BaseMessage]
    summary: Optional[str]
    memory_entries: List[MemoryEntry]
    messages: Annotated[List[BaseMessage], operator.add]


# A2A Protocol 관련 타입
class AgentCapability(BaseModel):
    """에이전트 능력"""
    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class AgentInfo(BaseModel):
    """에이전트 정보"""
    name: str
    agent_type: AgentType
    description: str
    version: str
    capabilities: List[AgentCapability]
    url: str


# 응답 타입
class AgentResponse(BaseModel):
    """에이전트 응답"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
