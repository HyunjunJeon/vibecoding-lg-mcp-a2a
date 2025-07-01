"""FastAPI 서버 - UnifiedResearch Agent API"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from datetime import datetime

from .agent import root_agent
from .models import ResearchRequest, ResearchResult

# FastAPI 앱 생성
app = FastAPI(
    title="UnifiedResearch Agent API",
    description="종합 연구 에이전트 API - Google ADK 기반",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Runner와 Session 설정
session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent,
    app_name="unified_research_app",
    session_service=session_service
)


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 초기화"""
    print("UnifiedResearch Agent API 서버가 시작되었습니다.")
    print(f"Agent: {root_agent.name}")
    print(f"Model: {root_agent.model}")


@app.post("/research", response_model=ResearchResult)
async def create_research(request: ResearchRequest):
    """연구 수행 API
    
    Args:
        request: 연구 요청 정보 (주제, 깊이, 형식)
    
    Returns:
        ResearchResult: 연구 결과
    """
    try:
        # 세션 생성
        session_id = f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 연구 요청 프롬프트 생성
        prompt = f"""
주제: {request.topic}
연구 깊이: {request.depth}
출력 형식: {request.output_format}

위 주제에 대해 {request.depth} 수준의 연구를 수행하고 {request.output_format} 형식으로 보고서를 작성해주세요.
각 단계마다 진행 상황을 모니터링하고, 최종 결과를 저장해주세요.
"""
        
        # Runner를 통해 에이전트 실행
        async for response in runner.run(prompt, session_id=session_id):
            if response.final:
                # 최종 응답 처리
                final_response = response.result if hasattr(response, 'result') else str(response)
                
                # 결과 구성
                result = ResearchResult(
                    topic=request.topic,
                    report=final_response,
                    metadata={
                        "depth": request.depth,
                        "output_format": request.output_format,
                        "agent_version": "1.0.0",
                        "model": str(root_agent.model),
                        "session_id": session_id
                    },
                    sources=[],  # 실제 구현에서는 sources 추출
                    created_at=datetime.now().isoformat()
                )
                
                return result
        
        # 응답이 없는 경우
        raise HTTPException(status_code=500, detail="No response from agent")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "service": "UnifiedResearch Agent API",
        "agent": root_agent.name,
        "model": str(root_agent.model)
    }


@app.get("/agent/info")
async def agent_info():
    """에이전트 정보 조회"""
    return {
        "name": root_agent.name,
        "description": root_agent.description if hasattr(root_agent, 'description') else "종합 연구를 수행하는 오케스트레이터 에이전트",
        "model": str(root_agent.model),
        "tools": [tool.__name__ for tool in root_agent.tools] if hasattr(root_agent, 'tools') else []
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)