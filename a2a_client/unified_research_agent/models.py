"""데이터 모델 정의"""
from typing import Dict, List, Any
from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    """연구 요청 모델"""
    topic: str = Field(description="연구 주제")
    depth: str = Field(default="comprehensive", description="연구 깊이 (basic/comprehensive/expert)")
    output_format: str = Field(default="markdown", description="출력 형식 (markdown/html/pdf)")


class ResearchResult(BaseModel):
    """연구 결과 모델"""
    topic: str
    report: str
    metadata: Dict[str, Any]
    sources: List[str]
    created_at: str