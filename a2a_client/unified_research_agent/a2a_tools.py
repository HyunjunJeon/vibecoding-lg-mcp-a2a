"""A2A 에이전트 호출을 위한 도구 함수들"""
import json
import os
from typing import Dict, Any
from datetime import datetime
from a2a.client import A2AClient
from a2a.types import Message, TextPart, DataPart, Part


async def call_planning_agent(topic: str, depth: str = "comprehensive") -> str:
    """Planning Agent를 호출하여 연구 계획 수립
    
    Args:
        topic (str): 연구 주제
        depth (str): 연구 깊이 (basic/comprehensive/expert)
    
    Returns:
        str: 연구 계획
    """
    # 환경 변수에서 URL 읽기, 기본값은 Docker 서비스명 사용
    planning_url = os.getenv('PLANNING_AGENT_URL', 'http://planning-agent:8003/')
    print(f"Planning Agent URL: {planning_url}")
    
    try:
        client = A2AClient(planning_url)
        message = Message(
            role="user",
            parts=[Part(root=TextPart(text=f"{topic}에 대해 {depth} 수준의 연구 계획을 수립해주세요"))]
        )
        
        response = await client.send_message(message)
        
        result = ""
        for part in response.parts:
            if isinstance(part.root, TextPart):
                result += part.root.text
                
        return result
    except Exception as e:
        error_msg = f"Planning Agent 호출 실패: {str(e)}"
        print(error_msg)
        return error_msg
    finally:
        try:
            await client.close()
        except:
            pass


async def call_research_agent(query: str) -> str:
    """Research Agent를 호출하여 정보 수집
    
    Args:
        query (str): 조사할 내용
    
    Returns:
        str: 조사 결과
    """
    # 환경 변수에서 URL 읽기, 기본값은 Docker 서비스명 사용
    research_url = os.getenv('RESEARCH_AGENT_URL', 'http://research-agent:8001/')
    print(f"Research Agent URL: {research_url}")
    
    try:
        client = A2AClient(research_url)
        message = Message(
            role="user",
            parts=[Part(root=TextPart(text=query))]
        )
        
        response = await client.send_message(message)
        
        result = ""
        data = {}
        for part in response.parts:
            if isinstance(part.root, TextPart):
                result += part.root.text
            elif isinstance(part.root, DataPart):
                data = part.root.data
                
        if data:
            result += f"\n\n추가 데이터: {json.dumps(data, ensure_ascii=False, indent=2)}"
            
        return result
    except Exception as e:
        error_msg = f"Research Agent 호출 실패: {str(e)}"
        print(error_msg)
        return error_msg
    finally:
        try:
            await client.close()
        except:
            pass


async def call_report_writing_agent(topic: str, research_data: str) -> str:
    """Report Writing Agent를 호출하여 보고서 작성
    
    Args:
        topic (str): 보고서 주제
        research_data (str): 연구 데이터
    
    Returns:
        str: 작성된 보고서
    """
    # 환경 변수에서 URL 읽기, 기본값은 Docker 서비스명 사용
    report_url = os.getenv('REPORT_WRITING_AGENT_URL', 'http://report-writing-agent:8004/')
    print(f"Report Writing Agent URL: {report_url}")
    
    try:
        client = A2AClient(report_url)
        context = {
            "topic": topic,
            "research_data": research_data
        }
        
        message = Message(
            role="user",
            parts=[
                Part(root=TextPart(text=f"{topic}에 대한 전문적인 보고서를 작성해주세요")),
                Part(root=DataPart(data=context))
            ]
        )
        
        response = await client.send_message(message)
        
        result = ""
        for part in response.parts:
            if isinstance(part.root, TextPart):
                result += part.root.text
                
        return result
    except Exception as e:
        error_msg = f"Report Writing Agent 호출 실패: {str(e)}"
        print(error_msg)
        return error_msg
    finally:
        try:
            await client.close()
        except:
            pass


async def orchestrate_research(topic: str, depth: str = "comprehensive") -> str:
    """전체 연구 프로세스를 조정하여 실행
    
    Args:
        topic (str): 연구 주제
        depth (str): 연구 깊이
    
    Returns:
        str: 최종 연구 보고서
    """
    results = {}
    
    # 환경 변수에서 URL 읽기
    planning_url = os.getenv('PLANNING_AGENT_URL', 'http://planning-agent:8003/')
    research_url = os.getenv('RESEARCH_AGENT_URL', 'http://research-agent:8001/')
    report_url = os.getenv('REPORT_WRITING_AGENT_URL', 'http://report-writing-agent:8004/')
    
    print(f"Using Agent URLs:")
    print(f"- Planning: {planning_url}")
    print(f"- Research: {research_url}")
    print(f"- Report Writing: {report_url}")
    
    try:
        # 1단계: 연구 계획 수립
        print("\n1단계: 연구 계획 수립 중...")
        planning_client = A2AClient(planning_url)
        plan_message = Message(
            role="user",
            parts=[Part(root=TextPart(text=f"{topic}에 대한 {depth} 수준의 연구 계획을 수립해주세요"))]
        )
        plan_response = await planning_client.send_message(plan_message)
        
        plan_text = ""
        for part in plan_response.parts:
            if isinstance(part.root, TextPart):
                plan_text += part.root.text
        results["plan"] = plan_text
        await planning_client.close()
        print("계획 수립 완료")
        
        # 2단계: 연구 수행
        print("\n2단계: 연구 수행 중...")
        research_client = A2AClient(research_url)
        
        # 계획에서 추출한 쿼리 또는 기본 쿼리 사용
        queries = [topic, f"{topic} 최신 동향", f"{topic} 주요 특징"]
        research_results = []
        
        for query in queries[:2]:  # 처음 2개 쿼리만 실행
            research_message = Message(
                role="user",
                parts=[Part(root=TextPart(text=query))]
            )
            research_response = await research_client.send_message(research_message)
            
            research_text = ""
            for part in research_response.parts:
                if isinstance(part.root, TextPart):
                    research_text += part.root.text
            research_results.append(research_text)
            print(f"조사 완료: {query}")
        
        results["research"] = "\n\n---\n\n".join(research_results)
        await research_client.close()
        
        # 3단계: 보고서 작성
        print("\n3단계: 보고서 작성 중...")
        report_client = A2AClient(report_url)
        
        report_context = {
            "topic": topic,
            "plan": results["plan"],
            "research_results": results["research"]
        }
        
        report_message = Message(
            role="user",
            parts=[
                Part(root=TextPart(text=f"{topic}에 대한 종합 보고서를 작성해주세요")),
                Part(root=DataPart(data=report_context))
            ]
        )
        
        report_response = await report_client.send_message(report_message)
        
        report_text = ""
        for part in report_response.parts:
            if isinstance(part.root, TextPart):
                report_text += part.root.text
        
        results["report"] = report_text
        await report_client.close()
        print("보고서 작성 완료!")
        
        # 최종 보고서 구성
        final_report = f"""# {topic} 연구 보고서

## 연구 계획
{results["plan"]}

## 연구 결과
{results["research"]}

## 종합 보고서
{results["report"]}

---
생성일시: {datetime.now().isoformat()}
"""
        
        return final_report
        
    except Exception as e:
        error_detail = f"오케스트레이션 중 오류 발생: {type(e).__name__}: {str(e)}"
        print(error_detail)
        import traceback
        traceback.print_exc()
        return f"연구 수행 중 오류가 발생했습니다:\n{error_detail}"