"""자료조사 에이전트: 웹 검색과 벡터 DB 검색을 통해 정보를 수집하는 에이전트"""
from typing import Any, ClassVar, List, Dict, Optional
from datetime import datetime

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import StateGraph, END
from langgraph.store.base import BaseStore
from pydantic import BaseModel, Field

from agents.base import BaseAgent, BaseState


class SearchResult(BaseModel):
    """검색 결과"""
    source: str = Field(description="출처 (web/vector)")
    title: str = Field(description="제목")
    content: str = Field(description="내용")
    url: Optional[str] = Field(default=None, description="URL (웹 검색인 경우)")
    relevance_score: float = Field(description="관련성 점수")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")


class ResearchState(BaseState):
    """자료조사 에이전트의 상태"""
    research_query: str = Field(description="조사 주제/질문")
    search_keywords: List[str] = Field(default_factory=list, description="검색 키워드")
    web_results: List[SearchResult] = Field(default_factory=list, description="웹 검색 결과")
    vector_results: List[SearchResult] = Field(default_factory=list, description="벡터 검색 결과")
    aggregated_results: List[SearchResult] = Field(default_factory=list, description="통합 검색 결과")
    research_summary: str = Field(default="", description="조사 결과 요약")
    sources_cited: List[str] = Field(default_factory=list, description="인용된 출처")


class ResearchAgent(BaseAgent):
    """자료조사 에이전트"""
    
    NODE_NAMES: ClassVar[dict[str, str]] = {
        "EXTRACT_KEYWORDS": "extract_keywords",
        "SEARCH_WEB": "search_web",
        "SEARCH_VECTOR": "search_vector",
        "AGGREGATE": "aggregate_results",
        "SUMMARIZE": "summarize_findings",
    }

    def __init__(
        self,
        model: BaseChatModel,
        state_schema: Any = ResearchState,
        config_schema: Any | None = None,
        input_schema: Any | None = None,
        output_schema: Any | None = None,
        checkpointer: BaseCheckpointSaver | None = None,
        store: BaseStore | None = None,
        max_retry_attempts: int = 2,
        agent_name: str = "ResearchAgent",
        is_debug: bool = True,
        mcp_client: Any = None,  # MCP 클라이언트는 나중에 주입
    ) -> None:
        super().__init__(
            model=model,
            state_schema=state_schema,
            config_schema=config_schema,
            input_schema=input_schema,
            output_schema=output_schema,
            checkpointer=checkpointer,
            store=store,
            max_retry_attempts=max_retry_attempts,
            agent_name=agent_name,
            is_debug=is_debug,
        )
        self.mcp_client = mcp_client

    def init_nodes(self, graph: StateGraph):
        """그래프에 노드 초기화"""
        extract_node = self.get_node_name("EXTRACT_KEYWORDS")
        web_search_node = self.get_node_name("SEARCH_WEB")
        vector_search_node = self.get_node_name("SEARCH_VECTOR")
        aggregate_node = self.get_node_name("AGGREGATE")
        summarize_node = self.get_node_name("SUMMARIZE")
        
        graph.add_node(extract_node, self.extract_keywords)
        graph.add_node(web_search_node, self.search_web)
        graph.add_node(vector_search_node, self.search_vector)
        graph.add_node(aggregate_node, self.aggregate_results)
        graph.add_node(summarize_node, self.summarize_findings)

    def init_edges(self, graph: StateGraph):
        """그래프에 엣지 초기화"""
        extract_node = self.get_node_name("EXTRACT_KEYWORDS")
        web_search_node = self.get_node_name("SEARCH_WEB")
        vector_search_node = self.get_node_name("SEARCH_VECTOR")
        aggregate_node = self.get_node_name("AGGREGATE")
        summarize_node = self.get_node_name("SUMMARIZE")
        
        # 워크플로우 정의
        graph.set_entry_point(extract_node)
        
        # 키워드 추출 후 병렬로 웹 검색과 벡터 검색 수행
        graph.add_edge(extract_node, web_search_node)
        graph.add_edge(extract_node, vector_search_node)
        
        # 두 검색이 완료되면 결과 통합
        graph.add_edge(web_search_node, aggregate_node)
        graph.add_edge(vector_search_node, aggregate_node)
        
        # 통합 후 요약
        graph.add_edge(aggregate_node, summarize_node)
        graph.add_edge(summarize_node, END)

    async def extract_keywords(self, state: ResearchState, config: RunnableConfig) -> ResearchState:
        """검색 키워드 추출"""
        try:
            prompt = f"""다음 조사 주제에서 효과적인 검색을 위한 키워드를 추출하세요:

조사 주제: {state.research_query}

다음 사항을 고려하세요:
1. 핵심 개념과 용어
2. 관련 동의어나 유사어
3. 영어 키워드도 포함 (국제 자료 검색용)
4. 구체적이고 명확한 키워드

5-8개의 키워드를 쉼표로 구분하여 나열하세요."""

            response = await self.model.ainvoke([HumanMessage(content=prompt)], config)
            
            # 키워드 파싱
            keywords = [kw.strip() for kw in response.content.split(',')]
            state.search_keywords = keywords[:8]  # 최대 8개로 제한
            
            if self.is_debug:
                print(f"[{self.agent_name}] 키워드 추출 완료:")
                print(f"  키워드: {', '.join(state.search_keywords)}")
            
            return state
            
        except Exception as e:
            if self.is_debug:
                print(f"[{self.agent_name}] 키워드 추출 중 오류: {e}")
            raise e

    async def search_web(self, state: ResearchState, config: RunnableConfig) -> ResearchState:
        """웹 검색 수행"""
        try:
            # MCP 클라이언트가 없는 경우 모의 결과 생성
            if self.mcp_client is None:
                # 실제 구현에서는 MCP 클라이언트를 통해 검색
                if self.is_debug:
                    print(f"[{self.agent_name}] MCP 클라이언트가 없어 모의 웹 검색 수행")
                
                # 모의 검색 결과
                for i, keyword in enumerate(state.search_keywords[:3]):
                    state.web_results.append(
                        SearchResult(
                            source="web",
                            title=f"{keyword}에 대한 웹 검색 결과 {i+1}",
                            content=f"{keyword}와 관련된 최신 정보입니다. 이는 모의 데이터입니다.",
                            url=f"https://example.com/{keyword.replace(' ', '-')}-{i+1}",
                            relevance_score=0.8 - (i * 0.1),
                            metadata={"search_date": datetime.now().isoformat()}
                        )
                    )
            else:
                # 실제 MCP를 통한 웹 검색
                # 키워드를 조합하여 하나의 통합 쿼리 생성
                combined_query = " ".join(state.search_keywords[:3])
                
                try:
                    results = await self.mcp_client.search_web(
                        query=combined_query,
                        max_results=10,
                        search_depth="basic"
                    )
                    
                    # 결과를 SearchResult 형태로 변환
                    for result in results:
                        state.web_results.append(
                            SearchResult(
                                source="web",
                                title=result.get("title", "제목 없음"),
                                content=result.get("content", ""),
                                url=result.get("url"),
                                relevance_score=result.get("score", 0.5),
                                metadata=result.get("metadata", {})
                            )
                        )
                except Exception as mcp_error:
                    if self.is_debug:
                        print(f"[{self.agent_name}] MCP 웹 검색 오류: {mcp_error}")
                    # 오류 발생 시 빈 결과 유지
            
            if self.is_debug:
                print(f"[{self.agent_name}] 웹 검색 완료:")
                print(f"  결과 수: {len(state.web_results)}")
            
            return state
            
        except Exception as e:
            if self.is_debug:
                print(f"[{self.agent_name}] 웹 검색 중 오류: {e}")
            raise e

    async def search_vector(self, state: ResearchState, config: RunnableConfig) -> ResearchState:
        """벡터 DB 검색 수행"""
        try:
            # MCP 클라이언트가 없는 경우 모의 결과 생성
            if self.mcp_client is None:
                if self.is_debug:
                    print(f"[{self.agent_name}] MCP 클라이언트가 없어 모의 벡터 검색 수행")
                
                # 모의 검색 결과
                for i, keyword in enumerate(state.search_keywords[:2]):
                    state.vector_results.append(
                        SearchResult(
                            source="vector",
                            title=f"{keyword}에 대한 문서 {i+1}",
                            content=f"{keyword}와 관련된 저장된 문서 내용입니다. 이는 모의 데이터입니다.",
                            relevance_score=0.9 - (i * 0.1),
                            metadata={
                                "collection": "default",
                                "document_id": f"doc_{i+1}",
                                "created_at": datetime.now().isoformat()
                            }
                        )
                    )
            else:
                # 실제 MCP를 통한 벡터 검색
                # 키워드를 조합하여 검색
                combined_query = " ".join(state.search_keywords[:3])
                
                try:
                    results = await self.mcp_client.search_vector(
                        query=combined_query,
                        collection="default",
                        top_k=10
                    )
                    
                    # 결과를 SearchResult 형태로 변환
                    for result in results:
                        # 오류 결과는 건너뛰기
                        if "error" in result:
                            continue
                            
                        state.vector_results.append(
                            SearchResult(
                                source="vector",
                                title=result.get("title", "제목 없음"),
                                content=result.get("content", ""),
                                relevance_score=result.get("score", 0.5),
                                metadata=result.get("metadata", {})
                            )
                        )
                except Exception as mcp_error:
                    if self.is_debug:
                        print(f"[{self.agent_name}] MCP 벡터 검색 오류: {mcp_error}")
                    # 오류 발생 시 빈 결과 유지
            
            if self.is_debug:
                print(f"[{self.agent_name}] 벡터 검색 완료:")
                print(f"  결과 수: {len(state.vector_results)}")
            
            return state
            
        except Exception as e:
            if self.is_debug:
                print(f"[{self.agent_name}] 벡터 검색 중 오류: {e}")
            raise e

    async def aggregate_results(self, state: ResearchState, config: RunnableConfig) -> ResearchState:
        """검색 결과 통합 및 중복 제거"""
        try:
            # 모든 결과를 하나의 리스트로 합치기
            all_results = state.web_results + state.vector_results
            
            # 관련성 점수로 정렬
            all_results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # 중복 제거 (제목과 내용의 유사성 기반)
            seen_content = set()
            unique_results = []
            
            for result in all_results:
                # 간단한 중복 체크 (실제로는 더 정교한 방법 필요)
                content_hash = hash(result.title + result.content[:100])
                if content_hash not in seen_content:
                    seen_content.add(content_hash)
                    unique_results.append(result)
            
            # 상위 10개 결과만 유지
            state.aggregated_results = unique_results[:10]
            
            # 출처 수집
            state.sources_cited = list(set([
                result.url or f"{result.source}:{result.title}"
                for result in state.aggregated_results
            ]))
            
            if self.is_debug:
                print(f"[{self.agent_name}] 결과 통합 완료:")
                print(f"  통합 결과 수: {len(state.aggregated_results)}")
                print(f"  인용 출처 수: {len(state.sources_cited)}")
            
            return state
            
        except Exception as e:
            if self.is_debug:
                print(f"[{self.agent_name}] 결과 통합 중 오류: {e}")
            raise e

    async def summarize_findings(self, state: ResearchState, config: RunnableConfig) -> ResearchState:
        """조사 결과 요약"""
        try:
            # 검색 결과를 문자열로 정리
            results_text = "\n\n".join([
                f"[{i+1}] {result.title}\n출처: {result.source}\n내용: {result.content[:200]}..."
                for i, result in enumerate(state.aggregated_results)
            ])
            
            prompt = f"""다음 검색 결과를 바탕으로 '{state.research_query}'에 대한 종합적인 요약을 작성하세요:

검색 결과:
{results_text}

요약 작성 시 다음 사항을 포함하세요:
1. 핵심 발견사항
2. 주요 트렌드나 패턴
3. 중요한 통계나 사실
4. 추가 조사가 필요한 부분

체계적이고 읽기 쉬운 형태로 작성하세요."""

            response = await self.model.ainvoke([HumanMessage(content=prompt)], config)
            state.research_summary = response.content
            
            # 최종 메시지 추가
            state.messages.append(
                AIMessage(content=f"조사 완료: {len(state.aggregated_results)}개의 관련 자료를 찾았습니다.\n\n{state.research_summary}")
            )
            
            if self.is_debug:
                print(f"[{self.agent_name}] 요약 완료:")
                print(f"  요약 길이: {len(state.research_summary)} 문자")
            
            return state
            
        except Exception as e:
            if self.is_debug:
                print(f"[{self.agent_name}] 요약 생성 중 오류: {e}")
            raise e