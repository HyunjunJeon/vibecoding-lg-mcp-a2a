"""LangGraph 에이전트 그래프 빌더"""
import os
from typing import Any

from langchain_openai import AzureChatOpenAI
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.memory import MemorySaver

from agents.agent.planning_agent import PlanningAgent, PlanningState
from agents.agent.research_agent import ResearchAgent, ResearchState
from agents.agent.report_writing_agent import ReportWritingAgent, ReportWritingState
from agents.tools.mcp_client import get_mcp_client


def create_azure_llm() -> AzureChatOpenAI:
    """Azure OpenAI LLM 인스턴스 생성"""
    return AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4.1"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-02-01-preview"),
        temperature=0.2,
        top_p=0.95,
        streaming=True
    )


async def create_planning_graph() -> CompiledStateGraph:
    """계획 수립 에이전트 그래프 생성"""
    # LLM 생성
    llm = create_azure_llm()
    
    # 체크포인터 생성
    checkpointer = MemorySaver()
    
    # 에이전트 생성
    agent = PlanningAgent(
        model=llm,
        state_schema=PlanningState,
        checkpointer=checkpointer,
        is_debug=True
    )
    
    # 그래프 빌드
    graph = agent.build_graph()
    return graph


async def create_research_graph() -> CompiledStateGraph:
    """자료조사 에이전트 그래프 생성"""
    # LLM 생성
    llm = create_azure_llm()
    
    # 체크포인터 생성
    checkpointer = MemorySaver()
    
    # MCP 클라이언트 생성
    mcp_client = await get_mcp_client()
    
    # 에이전트 생성
    agent = ResearchAgent(
        model=llm,
        state_schema=ResearchState,
        checkpointer=checkpointer,
        mcp_client=mcp_client,
        is_debug=True
    )
    
    # 그래프 빌드
    graph = agent.build_graph()
    return graph


async def create_report_writing_graph() -> CompiledStateGraph:
    """보고서 작성 에이전트 그래프 생성"""
    # LLM 생성
    llm = create_azure_llm()
    
    # 체크포인터 생성
    checkpointer = MemorySaver()
    
    # 에이전트 생성
    agent = ReportWritingAgent(
        model=llm,
        state_schema=ReportWritingState,
        checkpointer=checkpointer,
        is_debug=True
    )
    
    # 그래프 빌드
    graph = agent.build_graph()
    return graph


# 동기 방식의 래퍼 함수들 (LangGraph가 요구하는 형식)
def planning_graph() -> Any:
    """계획 수립 그래프 (동기 래퍼)"""
    import asyncio
    return asyncio.run(create_planning_graph())


def research_graph() -> Any:
    """자료조사 그래프 (동기 래퍼)"""
    import asyncio
    return asyncio.run(create_research_graph())


def report_writing_graph() -> Any:
    """보고서 작성 그래프 (동기 래퍼)"""
    import asyncio
    return asyncio.run(create_report_writing_graph())