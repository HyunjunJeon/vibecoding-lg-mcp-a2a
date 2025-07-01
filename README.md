# TTimes Guide Coding - Multi-Agent Report Generation System

웹 검색과 보고서 작성을 자동화하는 LangGraph 기반 멀티 에이전트 시스템

## 개요

본 프로젝트는 사용자의 요청에 따라 웹 검색, 문서 검색, 보고서 계획 수립, 보고서 작성을 자동으로 수행하는 AI 멀티 에이전트 시스템입니다. LangGraph와 A2A(Agent-to-Agent) 프로토콜을 사용하여 여러 전문 에이전트들이 협력하여 고품질의 보고서를 생성합니다.

## 주요 기능

- 🔍 **실시간 웹 검색** - Tavily Search API를 통한 최신 정보 수집
- 📚 **벡터 DB 검색** - PostgreSQL pgvector를 이용한 유사 문서 검색
- 📋 **자동 계획 수립** - AI 기반 작업 계획 및 구조 설계
- ✍️ **보고서 작성** - 수집된 정보를 종합한 전문적인 보고서 생성
- 🤖 **MCP 통합** - Model Context Protocol을 통한 도구 통합
- 🔗 **A2A 통신** - Google ADK 기반 에이전트 간 통신

## Tech Stack

- **Python 3.13**
- **LangChain** - LLM 애플리케이션 프레임워크
- **LangGraph** - 상태 기반 AI 워크플로우
- **A2A Protocol** - 에이전트 간 통신 표준
- **FastMCP** - Model Context Protocol 서버
- **Google ADK** - Agent Development Kit
- **FastAPI** - 웹 서버
- **PostgreSQL + pgvector** - 벡터 데이터베이스
- **Redis** - 캐시 및 세션 관리
- **Azure OpenAI** - LLM 제공자

## 시스템 아키텍처

```
┌─────────────────────────┐
│ UnifiedResearch Agent   │ ← Google ADK 기반 오케스트레이터
│    (ADK Client)         │
└───────────┬─────────────┘
            │ A2A Protocol
    ┌───────┴───────┬──────────────┐
    ▼               ▼              ▼
┌─────────┐   ┌──────────┐   ┌──────────┐
│Planning │   │ Research │   │  Report  │
│  Agent  │   │  Agent   │   │ Writing  │
│(A2A Srv)│   │(A2A Srv) │   │(A2A Srv) │
└────┬────┘   └────┬─────┘   └──────────┘
     │             │ MCP Protocol
     │             ▼
     │      ┌──────────────┐
     │      │ All-Search   │
     │      │ MCP Server   │
     │      └───┬──────┬───┘
     │          │      │
     │          ▼      ▼
     │      [Tavily] [LangConnect]
     │                     │
     └─────────────────────┼─────────────┐
                           ▼             ▼
                    [PostgreSQL+pgvector] [Redis]
```

## 설치 방법

### 1. 사전 요구사항

- Python 3.13+
- Docker & Docker Compose
- uv (Python 패키지 매니저)

### 2. 프로젝트 클론

```bash
git clone https://github.com/yourusername/ttimes_guide_coding.git
cd ttimes_guide_coding
```

### 3. 환경 설정

```bash
# 환경 변수 파일 생성
cp .env.example .env

# .env 파일을 편집하여 필요한 API 키 입력:
# - AZURE_OPENAI_API_KEY
# - AZURE_OPENAI_ENDPOINT
# - AZURE_OPENAI_DEPLOYMENT_NAME
# - TAVILY_API_KEY
# - GOOGLE_API_KEY (ADK용)
# - 기타 설정값
```

### 4. 의존성 설치

```bash
# uv를 사용한 의존성 설치
uv sync --dev

# 또는 개발 의존성 제외
uv sync
```

## 실행 방법

### 1. LangConnect 시작 (벡터 DB)

```bash
cd langconnect
make up  # Docker Compose로 PostgreSQL + API 서버 시작
cd ..
```

### 2. 전체 시스템 실행

```bash
# 실행 권한 부여 (최초 1회)
chmod +x scripts/run_all_agents.sh

# 시스템 시작
./scripts/run_all_agents.sh
```

### 3. LangGraph 에이전트 개별 테스트

```bash
# LangGraph Studio로 테스트
./scripts/test_langgraph_agents.sh
```

### 4. 시스템 사용

```bash
# CLI 모드
python a2a_client/unified_research_agent.py

# 또는 API 호출
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"topic": "AI 트렌드 분석", "depth": "comprehensive"}'
```

### 5. 개별 A2A 서버 실행

```bash
# Planning Agent A2A Server
python agents/a2a_servers/planning_a2a_server.py

# Research Agent A2A Server  
python agents/a2a_servers/research_a2a_server.py

# Report Writing Agent A2A Server
python agents/a2a_servers/report_writing_a2a_server.py

# MCP Server
python all-search-mcp/run_server.py --transport http
```

## API 엔드포인트

각 에이전트는 A2A 프로토콜을 따르는 엔드포인트를 제공합니다:

- **UnifiedResearch Agent**: http://localhost:8000
- **Research Agent A2A**: http://localhost:8001
- **Planning Agent A2A**: http://localhost:8003  
- **Report Writing Agent A2A**: http://localhost:8004
- **MCP Server**: http://localhost:8090/mcp
- **LangConnect API**: http://localhost:8080
- **LangGraph Studio**: http://localhost:8123

## 사용 예제

### Python SDK 사용

```python
from a2a_client import UnifiedResearchAgent, ResearchRequest

# 에이전트 생성
agent = UnifiedResearchAgent()

# 연구 요청
request = ResearchRequest(
    topic="Python 웹 프레임워크 비교 분석",
    depth="comprehensive",
    output_format="markdown"
)

# 연구 수행
result = await agent.conduct_research(request)

# 결과 출력
print(result.report)
```

### REST API 사용

```bash
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Python 웹 프레임워크 비교 분석",
    "depth": "comprehensive"
  }'
```

### Google ADK Web UI

```bash
# ADK 웹 UI 시작
adk web a2a_client/
```

## 개발 가이드

### 프로젝트 구조

```
ttimes_guide_coding/
├── agents/              # LangGraph 에이전트
│   ├── agent/          # 에이전트 구현체
│   ├── a2a_servers/    # A2A 서버 래퍼
│   ├── base/           # 기본 클래스
│   └── tools/          # MCP 클라이언트
├── all-search-mcp/      # MCP 서버
├── a2a_client/          # Google ADK 클라이언트
├── langconnect/         # 벡터 DB API
├── docker/              # Docker 설정
├── scripts/             # 실행 스크립트
└── docs/                # 참고 문서
```

### 새로운 LangGraph 에이전트 추가하기

1. `/agents/agent/` 디렉토리에 새 에이전트 파일 생성
2. `BaseAgent` 클래스 상속 및 노드/엣지 구현
3. `/agents/graph_builders.py`에 그래프 빌더 함수 추가
4. `langgraph.json`에 에이전트 등록
5. A2A 서버 래퍼 구현 (optional)

### MCP 도구 추가하기

1. `/all-search-mcp/server.py`에 새 도구 함수 추가
2. `@mcp.tool()` 데코레이터로 도구 정의
3. 에이전트에서 MCP 클라이언트를 통해 사용

---

## MCP 서버 개발 가이드

### Describing your server

Once you've provided the documentation, clearly describe to Claude what kind of server you want to build. Be specific about:

- What resources your server will expose
- What tools it will provide
- Any prompts it should offer
- What external systems it needs to interact with

For example:

```text
Build an MCP server that:
- Connects to my company's PostgreSQL database
- Exposes table schemas as resources
- Provides tools for running read-only SQL queries
- Includes prompts for common data analysis tasks
```

### Working with Claude

When working with Claude on MCP servers:

1. Start with the core functionality first, then iterate to add more features
2. Ask Claude to explain any parts of the code you don't understand
3. Request modifications or improvements as needed
4. Have Claude help you test the server and handle edge cases

Claude can help implement all the key MCP features:

- Resource management and exposure
- Tool definitions and implementations
- Prompt templates and handlers
- Error handling and logging
- Connection and transport setup

### Best practices

When building MCP servers with Claude:

- Break down complex servers into smaller pieces
- Test each component thoroughly before moving on
- Keep security in mind - validate inputs and limit access appropriately
- Document your code well for future maintenance
- Follow MCP protocol specifications carefully

### Next steps

After Claude helps you build your server:

1. Review the generated code carefully
2. Test the server with the MCP Inspector tool
3. Connect it to Claude.app or other MCP clients
4. Iterate based on real usage and feedback

---

## A2A 개발 가이드

### Reference

[LangChain](https://python.langchain.com/llms.txt)  
[LangConnect-Client](https://github.com/teddynote-lab/LangConnect-Client)  
[LangGraph](https://langchain-ai.github.io/langgraph/llms-full.txt)  
[LangChain-MCP-Adapter(client)](https://langchain-ai.github.io/langgraph/reference/mcp/)  
[ModelContextProtocol](https://modelcontextprotocol.io/llms-full.txt)  
[MCP-Python-SDK](https://github.com/modelcontextprotocol/python-sdk)  
[FastMCP](https://github.com/jlowin/fastmcp)  
[FastMCP-llms.txt](https://gofastmcp.com/llms-full.txt)  
[A2A-SDK](https://github.com/a2aproject/a2a-python)  
[A2A-Directory](https://github.com/sing1ee/a2a-directory)  

### Cursor Tips

[REPOMIX](https://repomix.com/)  
[CURSOR-Rules](https://docs.cursor.com/context/rules)  
[CURSOR-RIPER-Framework](https://github.com/johnpeterman72/CursorRIPER.sigma)  