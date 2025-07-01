"""보고서 작성 에이전트: 수집된 정보를 바탕으로 구조화된 보고서를 생성하는 에이전트"""
from typing import Any, ClassVar, List, Dict, Literal
from datetime import datetime

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import StateGraph, END
from langgraph.store.base import BaseStore
from pydantic import BaseModel, Field

from agents.base import BaseAgent, BaseState


class ReportSection(BaseModel):
    """보고서 섹션"""
    title: str = Field(description="섹션 제목")
    content: str = Field(description="섹션 내용")
    order: int = Field(description="섹션 순서")
    subsections: List['ReportSection'] = Field(default_factory=list, description="하위 섹션")


class ReportWritingState(BaseState):
    """보고서 작성 에이전트의 상태"""
    topic: str = Field(description="보고서 주제")
    research_data: str = Field(description="조사된 데이터")
    report_outline: List[str] = Field(default_factory=list, description="보고서 개요")
    sections: List[ReportSection] = Field(default_factory=list, description="보고서 섹션")
    draft_report: str = Field(default="", description="초안")
    final_report: str = Field(default="", description="최종 보고서")
    citations: List[str] = Field(default_factory=list, description="인용 목록")
    report_metadata: Dict[str, Any] = Field(default_factory=dict, description="보고서 메타데이터")
    quality_score: float = Field(default=0.0, description="품질 점수")
    needs_revision: bool = Field(default=False, description="수정 필요 여부")


class ReportWritingAgent(BaseAgent):
    """보고서 작성 에이전트"""
    
    NODE_NAMES: ClassVar[dict[str, str]] = {
        "STRUCTURE": "structure_content",
        "WRITE_SECTIONS": "write_sections",
        "COMPILE_DRAFT": "compile_draft",
        "REVIEW_QUALITY": "review_quality",
        "FINALIZE": "finalize_report",
    }

    def __init__(
        self,
        model: BaseChatModel,
        state_schema: Any = ReportWritingState,
        config_schema: Any | None = None,
        input_schema: Any | None = None,
        output_schema: Any | None = None,
        checkpointer: BaseCheckpointSaver | None = None,
        store: BaseStore | None = None,
        max_retry_attempts: int = 2,
        agent_name: str = "ReportWritingAgent",
        is_debug: bool = True,
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

    def init_nodes(self, graph: StateGraph):
        """그래프에 노드 초기화"""
        structure_node = self.get_node_name("STRUCTURE")
        write_sections_node = self.get_node_name("WRITE_SECTIONS")
        compile_draft_node = self.get_node_name("COMPILE_DRAFT")
        review_quality_node = self.get_node_name("REVIEW_QUALITY")
        finalize_node = self.get_node_name("FINALIZE")
        
        graph.add_node(structure_node, self.structure_content)
        graph.add_node(write_sections_node, self.write_sections)
        graph.add_node(compile_draft_node, self.compile_draft)
        graph.add_node(review_quality_node, self.review_quality)
        graph.add_node(finalize_node, self.finalize_report)

    def init_edges(self, graph: StateGraph):
        """그래프에 엣지 초기화"""
        structure_node = self.get_node_name("STRUCTURE")
        write_sections_node = self.get_node_name("WRITE_SECTIONS")
        compile_draft_node = self.get_node_name("COMPILE_DRAFT")
        review_quality_node = self.get_node_name("REVIEW_QUALITY")
        finalize_node = self.get_node_name("FINALIZE")
        
        # 워크플로우 정의
        graph.set_entry_point(structure_node)
        graph.add_edge(structure_node, write_sections_node)
        graph.add_edge(write_sections_node, compile_draft_node)
        graph.add_edge(compile_draft_node, review_quality_node)
        
        # 조건부 엣지: 품질 검토 후 수정 필요 여부에 따라 분기
        graph.add_conditional_edges(
            review_quality_node,
            self.should_revise,
            {
                "revise": write_sections_node,
                "finalize": finalize_node,
            }
        )
        
        graph.add_edge(finalize_node, END)

    async def structure_content(self, state: ReportWritingState, config: RunnableConfig) -> ReportWritingState:
        """콘텐츠 구조화 및 개요 작성"""
        try:
            prompt = f"""다음 주제와 조사 데이터를 바탕으로 체계적인 보고서 개요를 작성하세요:

주제: {state.topic}

조사 데이터:
{state.research_data[:2000]}...

다음 형식으로 보고서 개요를 작성하세요:
1. 제목
2. 요약 (Executive Summary)
3. 서론
4. 본론 (2-4개의 주요 섹션)
5. 결론
6. 권고사항 (해당하는 경우)
7. 참고문헌

각 섹션의 제목과 간단한 설명을 포함하세요."""

            response = await self.model.ainvoke([HumanMessage(content=prompt)], config)
            
            # 개요 파싱
            outline_lines = response.content.strip().split('\n')
            state.report_outline = [line.strip() for line in outline_lines if line.strip()]
            
            # 메타데이터 설정
            state.report_metadata = {
                "created_at": datetime.now().isoformat(),
                "author": self.agent_name,
                "version": "1.0",
                "topic": state.topic
            }
            
            if self.is_debug:
                print(f"[{self.agent_name}] 보고서 구조화 완료:")
                print(f"  섹션 수: {len(state.report_outline)}")
            
            return state
            
        except Exception as e:
            if self.is_debug:
                print(f"[{self.agent_name}] 구조화 중 오류: {e}")
            raise e

    async def write_sections(self, state: ReportWritingState, config: RunnableConfig) -> ReportWritingState:
        """섹션별 내용 작성"""
        try:
            state.sections = []
            
            for i, outline_item in enumerate(state.report_outline):
                # 각 섹션에 대한 내용 생성
                section_prompt = f"""다음 섹션에 대한 내용을 작성하세요:

섹션: {outline_item}
주제: {state.topic}

참고 데이터:
{state.research_data[:1500]}...

다음 사항을 고려하세요:
1. 명확하고 간결한 문장 사용
2. 사실과 데이터 기반의 내용
3. 논리적 흐름 유지
4. 전문적인 어조

200-500단어로 작성하세요."""

                response = await self.model.ainvoke([HumanMessage(content=section_prompt)], config)
                
                # 섹션 제목 추출 (개요에서 번호와 제목 분리)
                title_parts = outline_item.split('.', 1)
                title = title_parts[1].strip() if len(title_parts) > 1 else outline_item
                
                section = ReportSection(
                    title=title,
                    content=response.content,
                    order=i
                )
                state.sections.append(section)
                
                if self.is_debug:
                    print(f"[{self.agent_name}] 섹션 작성 완료: {title}")
            
            return state
            
        except Exception as e:
            if self.is_debug:
                print(f"[{self.agent_name}] 섹션 작성 중 오류: {e}")
            raise e

    async def compile_draft(self, state: ReportWritingState, config: RunnableConfig) -> ReportWritingState:
        """초안 편집"""
        try:
            # 마크다운 형식으로 보고서 편집
            draft_parts = [
                f"# {state.topic}",
                f"\n**작성일**: {state.report_metadata['created_at'][:10]}",
                f"**작성자**: {state.report_metadata['author']}",
                "\n---\n"
            ]
            
            # 섹션들을 순서대로 추가
            for section in sorted(state.sections, key=lambda x: x.order):
                # 섹션 제목 레벨 결정
                if "요약" in section.title or "Executive" in section.title:
                    draft_parts.append(f"\n## {section.title}\n")
                elif any(keyword in section.title for keyword in ["서론", "본론", "결론", "권고"]):
                    draft_parts.append(f"\n## {section.title}\n")
                else:
                    draft_parts.append(f"\n### {section.title}\n")
                
                draft_parts.append(section.content)
            
            # 인용 추가 (있는 경우)
            if state.citations:
                draft_parts.append("\n## 참고문헌\n")
                for i, citation in enumerate(state.citations):
                    draft_parts.append(f"{i+1}. {citation}")
            
            state.draft_report = "\n".join(draft_parts)
            
            if self.is_debug:
                print(f"[{self.agent_name}] 초안 편집 완료:")
                print(f"  초안 길이: {len(state.draft_report)} 문자")
            
            return state
            
        except Exception as e:
            if self.is_debug:
                print(f"[{self.agent_name}] 초안 편집 중 오류: {e}")
            raise e

    async def review_quality(self, state: ReportWritingState, config: RunnableConfig) -> ReportWritingState:
        """품질 검토"""
        try:
            review_prompt = f"""다음 보고서 초안의 품질을 검토하고 평가하세요:

보고서 초안:
{state.draft_report[:3000]}...

다음 기준으로 평가하세요:
1. 구조와 논리적 흐름 (20점)
2. 내용의 완성도와 정확성 (30점)
3. 가독성과 명확성 (20점)
4. 전문성과 어조 (15점)
5. 인용과 참고문헌 (15점)

총 100점 만점으로 점수를 매기고, 80점 이상이면 "승인", 
그 미만이면 "수정필요"로 판단하세요. 
개선이 필요한 부분을 구체적으로 지적하세요.

형식:
점수: XX/100
판정: 승인/수정필요
피드백: ..."""

            response = await self.model.ainvoke([HumanMessage(content=review_prompt)], config)
            
            # 점수 추출
            import re
            score_match = re.search(r'점수[:\s]*(\d+)', response.content)
            if score_match:
                state.quality_score = float(score_match.group(1)) / 100.0
            
            # 수정 필요 여부 판단
            if "수정필요" in response.content or state.quality_score < 0.8:
                state.needs_revision = True
                # 피드백을 연구 데이터에 추가하여 다음 작성에 반영
                state.research_data += f"\n\n품질 검토 피드백:\n{response.content}"
            else:
                state.needs_revision = False
            
            if self.is_debug:
                print(f"[{self.agent_name}] 품질 검토 완료:")
                print(f"  품질 점수: {state.quality_score * 100:.1f}/100")
                print(f"  수정 필요: {state.needs_revision}")
            
            return state
            
        except Exception as e:
            if self.is_debug:
                print(f"[{self.agent_name}] 품질 검토 중 오류: {e}")
            raise e

    async def finalize_report(self, state: ReportWritingState, config: RunnableConfig) -> ReportWritingState:
        """최종 보고서 완성"""
        try:
            # 최종 다듬기
            finalize_prompt = f"""다음 보고서를 최종적으로 다듬어주세요:

{state.draft_report}

다음 사항을 확인하고 개선하세요:
1. 오탈자나 문법 오류 수정
2. 일관된 형식과 스타일 유지
3. 전환 문구 추가로 흐름 개선
4. 핵심 메시지 강조

최종 보고서를 완성된 형태로 반환하세요."""

            response = await self.model.ainvoke([HumanMessage(content=finalize_prompt)], config)
            state.final_report = response.content
            
            # 메타데이터 업데이트
            state.report_metadata["finalized_at"] = datetime.now().isoformat()
            state.report_metadata["quality_score"] = state.quality_score
            
            # 최종 메시지 추가
            state.messages.append(
                AIMessage(content=f"보고서 작성이 완료되었습니다. (품질 점수: {state.quality_score * 100:.1f}/100)")
            )
            
            if self.is_debug:
                print(f"[{self.agent_name}] 보고서 완성:")
                print(f"  최종 보고서 길이: {len(state.final_report)} 문자")
                print(f"  섹션 수: {len(state.sections)}")
            
            return state
            
        except Exception as e:
            if self.is_debug:
                print(f"[{self.agent_name}] 보고서 완성 중 오류: {e}")
            raise e

    def should_revise(self, state: ReportWritingState) -> Literal["revise", "finalize"]:
        """수정 필요 여부에 따라 다음 단계 결정"""
        return "revise" if state.needs_revision else "finalize"