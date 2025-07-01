"""UnifiedResearch Agent - Google ADK 표준 에이전트 정의"""
import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from .tools import monitor_progress, save_result, plan_research, summarize_findings
from .a2a_tools import call_planning_agent, call_research_agent, call_report_writing_agent, orchestrate_research

# 환경 변수 로드
load_dotenv()

# Azure OpenAI 설정
azure_config = {
    "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
    "api_base": os.getenv("AZURE_OPENAI_ENDPOINT"),
    "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
}

# 모델 설정 (Azure OpenAI 사용)
model = LiteLlm(
    f"azure/{os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o-preview')}",
    **azure_config
)

# 루트 에이전트 정의 (모듈 레벨)
root_agent = Agent(
    name="unified_research_orchestrator",
    model=model,  # Azure OpenAI 모델 사용
    description="종합 연구를 수행하는 오케스트레이터 에이전트",
    instruction="""당신은 종합 연구 오케스트레이터입니다. 
사용자의 연구 요청을 받아 다음과 같은 연구를 수행합니다:

1. 주제에 대한 체계적인 분석
2. 관련 정보 수집 및 정리
3. 전문적인 보고서 작성

사용 가능한 도구:
- orchestrate_research: 전체 연구 프로세스를 자동으로 조정하여 실행 (권장)
- call_planning_agent: Planning Agent를 호출하여 연구 계획 수립
- call_research_agent: Research Agent를 호출하여 정보 수집
- call_report_writing_agent: Report Writing Agent를 호출하여 보고서 작성
- monitor_progress: 진행 상황 모니터링
- save_result: 최종 보고서 저장

연구 요청을 받으면:
1. orchestrate_research를 사용하여 전체 프로세스를 실행하거나
2. 개별 에이전트들을 순차적으로 호출하여 작업을 수행하세요

각 단계마다 monitor_progress를 사용하여 진행 상황을 알려주세요.""",
    tools=[
        orchestrate_research,  # 전체 연구 프로세스 오케스트레이션
        call_planning_agent,   # Planning Agent 호출
        call_research_agent,   # Research Agent 호출
        call_report_writing_agent,  # Report Writing Agent 호출
        monitor_progress,
        save_result,
        plan_research,
        summarize_findings
    ]
)