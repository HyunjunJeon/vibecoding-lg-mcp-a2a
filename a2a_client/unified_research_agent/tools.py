"""Google ADK 에이전트 도구 함수들"""
import os
import json
from datetime import datetime
from typing import Dict, Any


def monitor_progress(stage: str, status: str, details: str = "") -> str:
    """진행 상황 모니터링
    
    Args:
        stage (str): 현재 진행 단계
        status (str): 상태 (시작됨/진행중/완료/실패)
        details (str): 추가 세부사항 (선택사항)
    
    Returns:
        str: 진행 상황 로그 메시지
    """
    timestamp = datetime.now().isoformat()
    progress_msg = f"[{timestamp}] {stage}: {status}"
    if details:
        progress_msg += f" - {details}"
    
    print(progress_msg)
    return f"Progress logged: {stage} is {status}"


def save_result(topic: str, report: str, metadata: Dict[str, Any]) -> str:
    """연구 결과를 파일로 저장
    
    Args:
        topic (str): 연구 주제
        report (str): 연구 보고서 내용
        metadata (Dict[str, Any]): 보고서 메타데이터
    
    Returns:
        str: 저장된 파일 경로
    """
    # 결과를 파일로 저장
    filename = f"research_report_{topic.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    filepath = os.path.join("reports", filename)
    
    # reports 디렉토리 생성
    os.makedirs("reports", exist_ok=True)
    
    # 보고서 저장
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)
    
    # 메타데이터 저장
    metadata_filepath = filepath.replace(".md", "_metadata.json")
    with open(metadata_filepath, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    return f"Report saved to {filepath}"


def plan_research(topic: str, depth: str = "comprehensive") -> str:
    """연구 계획 수립
    
    Args:
        topic (str): 연구 주제
        depth (str): 연구 깊이 (basic/comprehensive/expert)
    
    Returns:
        str: 연구 계획 개요
    """
    depth_plans = {
        "basic": "핵심 개념과 주요 요점을 중심으로 기본적인 조사를 수행합니다.",
        "comprehensive": "주제에 대한 포괄적인 분석과 다양한 관점을 포함한 종합적인 연구를 수행합니다.",
        "expert": "학술 자료, 최신 연구, 전문가 의견을 포함한 심층적인 분석을 수행합니다."
    }
    
    plan = f"""
연구 주제: {topic}
연구 수준: {depth}

계획 개요:
{depth_plans.get(depth, depth_plans["comprehensive"])}

주요 단계:
1. 주제 정의 및 범위 설정
2. 관련 정보 수집 및 검토
3. 데이터 분석 및 종합
4. 보고서 작성 및 검토
5. 최종 보고서 완성
"""
    
    return plan


def summarize_findings(topic: str, findings: str) -> str:
    """연구 결과 요약
    
    Args:
        topic (str): 연구 주제
        findings (str): 연구 결과 내용
    
    Returns:
        str: 요약된 연구 결과
    """
    # 실제 구현에서는 LLM을 사용하여 요약할 수 있음
    # 여기서는 간단한 형식으로 반환
    summary = f"""
# {topic} 연구 요약

## 주요 발견사항
{findings[:500]}...

## 결론
이 연구는 {topic}에 대한 종합적인 분석을 제공합니다.
"""
    
    return summary