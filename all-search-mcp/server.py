"""All-Search MCP Server: LangConnect(벡터 검색)와 Tavily(웹 검색)를 통합하는 MCP 서버"""
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import httpx

from fastmcp import FastMCP
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# MCP 서버 인스턴스 생성
mcp = FastMCP(name="All-Search MCP Server")

# 설정
LANGCONNECT_API_URL = os.getenv("LANGCONNECT_API_URL", "http://localhost:8080")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
TAVILY_API_URL = "https://api.tavily.com/search"


class SearchResult(BaseModel):
    """검색 결과 모델"""
    title: str = Field(description="제목")
    content: str = Field(description="내용")
    url: Optional[str] = Field(default=None, description="URL")
    source: str = Field(description="출처 (web/vector)")
    score: float = Field(description="관련성 점수")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")


class VectorSearchParams(BaseModel):
    """벡터 검색 파라미터"""
    query: str = Field(description="검색 쿼리")
    collection: str = Field(default="default", description="컬렉션 이름")
    top_k: int = Field(default=5, description="반환할 결과 수")


class WebSearchParams(BaseModel):
    """웹 검색 파라미터"""
    query: str = Field(description="검색 쿼리")
    max_results: int = Field(default=5, description="최대 결과 수")
    search_depth: str = Field(default="basic", description="검색 깊이 (basic/advanced)")


async def _search_vector_impl(
    query: str,
    collection: str = "default",
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """벡터 검색 내부 구현"""
    try:
        async with httpx.AsyncClient() as client:
            # LangConnect API 호출
            response = await client.post(
                f"{LANGCONNECT_API_URL}/collections/{collection}/search",
                json={
                    "query": query,
                    "top_k": top_k,
                    "metadata_filter": {}
                }
            )
            
            if response.status_code != 200:
                return [{
                    "error": f"LangConnect API error: {response.status_code}",
                    "message": response.text
                }]
            
            data = response.json()
            results = []
            
            # 결과 포맷팅
            for item in data.get("results", []):
                result = SearchResult(
                    title=item.get("metadata", {}).get("title", "제목 없음"),
                    content=item.get("content", ""),
                    source="vector",
                    score=item.get("score", 0.0),
                    metadata={
                        "collection": collection,
                        "document_id": item.get("id", ""),
                        "created_at": item.get("metadata", {}).get("created_at", "")
                    }
                )
                results.append(result.dict())
            
            return results
            
    except httpx.ConnectError:
        return [{
            "error": "LangConnect 서버에 연결할 수 없습니다",
            "message": f"URL: {LANGCONNECT_API_URL}"
        }]
    except Exception as e:
        return [{
            "error": "벡터 검색 중 오류 발생",
            "message": str(e)
        }]


@mcp.tool()
async def search_vector(
    query: str,
    collection: str = "default",
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    LangConnect를 통한 벡터 데이터베이스 검색
    
    Args:
        query: 검색 쿼리
        collection: 검색할 컬렉션 이름
        top_k: 반환할 최대 결과 수
    
    Returns:
        검색 결과 목록
    """
    return await _search_vector_impl(query, collection, top_k)


async def _search_web_impl(
    query: str,
    max_results: int = 5,
    search_depth: str = "basic"
) -> List[Dict[str, Any]]:
    """웹 검색 내부 구현"""
    if not TAVILY_API_KEY:
        return [{
            "error": "Tavily API 키가 설정되지 않았습니다",
            "message": "환경 변수 TAVILY_API_KEY를 설정하세요"
        }]
    
    try:
        async with httpx.AsyncClient() as client:
            # Tavily API 호출
            response = await client.post(
                TAVILY_API_URL,
                json={
                    "api_key": TAVILY_API_KEY,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": search_depth,
                    "include_answer": True,
                    "include_raw_content": False
                }
            )
            
            if response.status_code != 200:
                return [{
                    "error": f"Tavily API error: {response.status_code}",
                    "message": response.text
                }]
            
            data = response.json()
            results = []
            
            # 결과 포맷팅
            for item in data.get("results", []):
                result = SearchResult(
                    title=item.get("title", ""),
                    content=item.get("content", ""),
                    url=item.get("url", ""),
                    source="web",
                    score=item.get("score", 0.0),
                    metadata={
                        "published_date": item.get("published_date", ""),
                        "search_date": datetime.now().isoformat()
                    }
                )
                results.append(result.dict())
            
            # Tavily의 AI 생성 답변도 포함
            if data.get("answer"):
                results.insert(0, {
                    "title": "AI 생성 답변",
                    "content": data["answer"],
                    "source": "web",
                    "score": 1.0,
                    "metadata": {"type": "ai_answer"}
                })
            
            return results
            
    except httpx.ConnectError:
        return [{
            "error": "Tavily API에 연결할 수 없습니다",
            "message": "인터넷 연결을 확인하세요"
        }]
    except Exception as e:
        return [{
            "error": "웹 검색 중 오류 발생",
            "message": str(e)
        }]


@mcp.tool()
async def search_web(
    query: str,
    max_results: int = 5,
    search_depth: str = "basic"
) -> List[Dict[str, Any]]:
    """
    Tavily API를 통한 웹 검색
    
    Args:
        query: 검색 쿼리
        max_results: 최대 결과 수
        search_depth: 검색 깊이 (basic/advanced)
    
    Returns:
        검색 결과 목록
    """
    return await _search_web_impl(query, max_results, search_depth)


@mcp.tool()
async def search_all(
    query: str,
    collection: str = "default",
    max_results: int = 10
) -> Dict[str, Any]:
    """
    벡터 검색과 웹 검색을 동시에 수행하는 통합 검색
    
    Args:
        query: 검색 쿼리
        collection: 벡터 검색에 사용할 컬렉션
        max_results: 각 검색 유형별 최대 결과 수
    
    Returns:
        {"vector": [...], "web": [...]} 형태의 통합 검색 결과
    """
    # 병렬로 두 검색 실행 (내부 구현 함수들을 직접 호출)
    vector_task = _search_vector_impl(query, collection, max_results)
    web_task = _search_web_impl(query, max_results)
    
    vector_results, web_results = await asyncio.gather(
        vector_task, web_task, return_exceptions=True
    )
    
    # 에러 처리
    if isinstance(vector_results, Exception):
        vector_results = [{
            "error": "벡터 검색 실패",
            "message": str(vector_results)
        }]
    
    if isinstance(web_results, Exception):
        web_results = [{
            "error": "웹 검색 실패",
            "message": str(web_results)
        }]
    
    return {
        "vector": vector_results,
        "web": web_results,
        "query": query,
        "timestamp": datetime.now().isoformat()
    }


@mcp.resource("search://status")
async def get_search_status() -> str:
    """검색 서버 상태 확인"""
    status = {
        "server": "All-Search MCP Server",
        "version": "1.0.0",
        "services": {
            "langconnect": {
                "url": LANGCONNECT_API_URL,
                "status": "unknown"
            },
            "tavily": {
                "configured": bool(TAVILY_API_KEY),
                "status": "configured" if TAVILY_API_KEY else "not configured"
            }
        },
        "timestamp": datetime.now().isoformat()
    }
    
    # LangConnect 연결 테스트
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{LANGCONNECT_API_URL}/health")
            if response.status_code == 200:
                status["services"]["langconnect"]["status"] = "healthy"
            else:
                status["services"]["langconnect"]["status"] = "unhealthy"
    except:
        status["services"]["langconnect"]["status"] = "unreachable"
    
    return json.dumps(status, indent=2, ensure_ascii=False)


@mcp.prompt()
async def search_prompt(topic: str) -> str:
    """주제에 대한 검색 프롬프트 생성"""
    return f"""다음 주제에 대해 종합적인 검색을 수행하세요: {topic}

1. 먼저 벡터 데이터베이스에서 관련 문서를 검색하세요
2. 웹에서 최신 정보를 검색하세요
3. 두 검색 결과를 종합하여 분석하세요

검색 도구:
- search_vector: 내부 문서 검색
- search_web: 웹 검색
- search_all: 통합 검색"""


if __name__ == "__main__":
    # 서버 실행
    print("All-Search MCP Server 시작...")
    print(f"LangConnect URL: {LANGCONNECT_API_URL}")
    print(f"Tavily API: {'구성됨' if TAVILY_API_KEY else '구성 안됨'}")
    
    # 서버 실행 (기본적으로 stdio transport 사용)
    mcp.run()