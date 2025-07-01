"""MCP 클라이언트 설정 - LangGraph 에이전트가 MCP 서버와 통신하기 위한 클라이언트"""
import os
from typing import Dict, Any, List
import asyncio

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import BaseTool
from dotenv import load_dotenv

load_dotenv()


class MCPSearchClient:
    """MCP 검색 클라이언트"""
    
    def __init__(self, mcp_server_url: str | None = None, transport: str = "streamable_http"):
        """
        MCP 검색 클라이언트 초기화
        
        Args:
            mcp_server_url: MCP 서버 URL (기본값: 환경변수 또는 localhost:8090)
            transport: Transport 유형 (stdio, streamable_http, sse)
        """
        self.mcp_server_url = mcp_server_url or os.getenv("MCP_SERVER_URL", "http://localhost:8090/mcp")
        self.transport = transport
        self.client = None
        self.tools = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """클라이언트 초기화 및 도구 로드"""
        if self._initialized:
            return
        
        try:
            # MCP 클라이언트 설정
            config = {
                "search": {
                    "url": self.mcp_server_url,
                    "transport": self.transport,
                }
            }
            
            # API 키가 필요한 경우
            api_key = os.getenv("MCP_API_KEY")
            if api_key:
                config["search"]["headers"] = f"Authorization: Bearer {api_key}"
            
            # 클라이언트 생성
            self.client = MultiServerMCPClient(connections=config)
            
            # 도구 로드
            self.tools = await self.client.get_tools()
            self._initialized = True
            
            print(f"MCP 클라이언트 초기화 완료: {self.mcp_server_url}")
            print(f"사용 가능한 도구: {list(self.tools.keys())}")
            
        except Exception as e:
            print(f"MCP 클라이언트 초기화 실패: {e}")
            raise
    
    async def get_search_tools(self) -> Dict[str, BaseTool]:
        """검색 도구 반환"""
        if not self._initialized:
            await self.initialize()
        
        # 검색 관련 도구만 필터링
        search_tools = {}
        for name, tool in self.tools.items():
            if any(keyword in name.lower() for keyword in ["search", "vector", "web"]):
                search_tools[name] = tool
        
        return search_tools
    
    async def search_vector(
        self,
        query: str,
        collection: str = "default",
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """벡터 검색 수행"""
        if not self._initialized:
            await self.initialize()
        
        tool = self.tools.get("search_vector")
        if not tool:
            raise ValueError("벡터 검색 도구를 찾을 수 없습니다")
        
        result = await tool.ainvoke({
            "query": query,
            "collection": collection,
            "top_k": top_k
        })
        
        return result
    
    async def search_web(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic"
    ) -> List[Dict[str, Any]]:
        """웹 검색 수행"""
        if not self._initialized:
            await self.initialize()
        
        tool = self.tools.get("search_web")
        if not tool:
            raise ValueError("웹 검색 도구를 찾을 수 없습니다")
        
        result = await tool.ainvoke({
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth
        })
        
        return result
    
    async def search_all(
        self,
        query: str,
        collection: str = "default",
        max_results: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """통합 검색 수행"""
        if not self._initialized:
            await self.initialize()
        
        tool = self.tools.get("search_all")
        if not tool:
            raise ValueError("통합 검색 도구를 찾을 수 없습니다")
        
        result = await tool.ainvoke({
            "query": query,
            "collection": collection,
            "max_results": max_results
        })
        
        return result
    
    async def close(self) -> None:
        """클라이언트 종료"""
        if self.client:
            await self.client.close()
            self._initialized = False


# 싱글톤 인스턴스
_mcp_client_instance = None


async def get_mcp_client() -> MCPSearchClient:
    """MCP 클라이언트 싱글톤 인스턴스 반환"""
    global _mcp_client_instance
    
    if _mcp_client_instance is None:
        _mcp_client_instance = MCPSearchClient()
        await _mcp_client_instance.initialize()
    
    return _mcp_client_instance


# 편의 함수들
async def search_vector(query: str, collection: str = "default", top_k: int = 5) -> List[Dict[str, Any]]:
    """벡터 검색 편의 함수"""
    client = await get_mcp_client()
    return await client.search_vector(query, collection, top_k)


async def search_web(query: str, max_results: int = 5, search_depth: str = "basic") -> List[Dict[str, Any]]:
    """웹 검색 편의 함수"""
    client = await get_mcp_client()
    return await client.search_web(query, max_results, search_depth)


async def search_all(query: str, collection: str = "default", max_results: int = 10) -> Dict[str, List[Dict[str, Any]]]:
    """통합 검색 편의 함수"""
    client = await get_mcp_client()
    return await client.search_all(query, collection, max_results)


# 테스트 코드
if __name__ == "__main__":
    async def test():
        """MCP 클라이언트 테스트"""
        try:
            # 클라이언트 초기화
            client = await get_mcp_client()
            
            # 도구 목록 확인
            tools = await client.get_search_tools()
            print(f"\n사용 가능한 검색 도구: {list(tools.keys())}")
            
            # 웹 검색 테스트
            print("\n=== 웹 검색 테스트 ===")
            web_results = await search_web("LangGraph multi-agent", max_results=3)
            for i, result in enumerate(web_results):
                print(f"{i+1}. {result.get('title', 'No title')}")
                print(f"   출처: {result.get('source', 'Unknown')}")
                print(f"   점수: {result.get('score', 0)}")
            
            # 벡터 검색 테스트 (LangConnect가 실행 중인 경우)
            print("\n=== 벡터 검색 테스트 ===")
            try:
                vector_results = await search_vector("agent", top_k=3)
                for i, result in enumerate(vector_results):
                    print(f"{i+1}. {result.get('title', 'No title')}")
                    print(f"   출처: {result.get('source', 'Unknown')}")
                    print(f"   점수: {result.get('score', 0)}")
            except Exception as e:
                print(f"벡터 검색 실패: {e}")
            
            # 통합 검색 테스트
            print("\n=== 통합 검색 테스트 ===")
            all_results = await search_all("AI agent", max_results=5)
            print(f"웹 검색 결과: {len(all_results.get('web', []))}개")
            print(f"벡터 검색 결과: {len(all_results.get('vector', []))}개")
            
        except Exception as e:
            print(f"테스트 실패: {e}")
        finally:
            # 클라이언트 종료
            if client:
                await client.close()
    
    # 테스트 실행
    asyncio.run(test())