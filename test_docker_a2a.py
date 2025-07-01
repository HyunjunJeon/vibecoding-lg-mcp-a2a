#!/usr/bin/env python3
"""Docker 환경에서 A2A 통신 테스트 스크립트"""
import asyncio
import aiohttp
import json
import os
from datetime import datetime

# 환경 변수에서 URL 읽기 (Docker 내부에서 실행 시)
PLANNING_URL = os.getenv('PLANNING_AGENT_URL', 'http://localhost:8003/')
RESEARCH_URL = os.getenv('RESEARCH_AGENT_URL', 'http://localhost:8001/')
REPORT_URL = os.getenv('REPORT_WRITING_AGENT_URL', 'http://localhost:8004/')


async def test_a2a_agent(agent_name: str, agent_url: str, message: str):
    """개별 A2A 에이전트 테스트"""
    print(f"\n{'='*60}")
    print(f"Testing {agent_name} at {agent_url}")
    print(f"{'='*60}")
    
    payload = {
        "jsonrpc": "2.0",
        "id": f"test-{datetime.now().timestamp()}",
        "method": "message/send",
        "params": {
            "message": {
                "messageId": f"msg-{datetime.now().timestamp()}",
                "role": "user",
                "parts": [
                    {
                        "text": message
                    }
                ]
            }
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print(f"Sending request to {agent_url}...")
            async with session.post(agent_url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                print(f"Response status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    print(f"Response received:")
                    print(json.dumps(result, ensure_ascii=False, indent=2))
                    
                    # 결과에서 텍스트 추출
                    if 'result' in result and 'message' in result['result']:
                        message = result['result']['message']
                        if 'parts' in message:
                            for part in message['parts']:
                                if 'text' in part:
                                    print(f"\nAgent response: {part['text'][:200]}...")
                else:
                    error_text = await response.text()
                    print(f"Error response: {error_text}")
                    
    except asyncio.TimeoutError:
        print(f"❌ Timeout error - Agent did not respond within 30 seconds")
    except aiohttp.ClientError as e:
        print(f"❌ Connection error: {type(e).__name__}: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {str(e)}")


async def test_health_check(service_name: str, health_url: str):
    """헬스 체크 테스트"""
    print(f"\nChecking health of {service_name} at {health_url}...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(health_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    print(f"✅ {service_name} is healthy")
                else:
                    print(f"❌ {service_name} health check failed with status {response.status}")
    except Exception as e:
        print(f"❌ {service_name} health check error: {type(e).__name__}: {str(e)}")


async def main():
    """메인 테스트 함수"""
    print("A2A Protocol Communication Test")
    print("=" * 80)
    
    # 헬스 체크
    await test_health_check("Planning Agent", PLANNING_URL.rstrip('/') + "/health")
    await test_health_check("Research Agent", RESEARCH_URL.rstrip('/') + "/health")
    await test_health_check("Report Writing Agent", REPORT_URL.rstrip('/') + "/health")
    
    # 개별 에이전트 테스트
    await test_a2a_agent(
        "Planning Agent",
        PLANNING_URL,
        "LangGraph 멀티 에이전트 시스템에 대한 연구 계획을 수립해주세요"
    )
    
    await test_a2a_agent(
        "Research Agent",
        RESEARCH_URL,
        "LangGraph의 주요 특징을 조사해주세요"
    )
    
    # Report Writing Agent는 특별한 데이터 구조가 필요할 수 있음
    print(f"\n{'='*60}")
    print(f"Testing Report Writing Agent (with context)")
    print(f"{'='*60}")
    
    report_payload = {
        "jsonrpc": "2.0",
        "id": f"test-report-{datetime.now().timestamp()}",
        "method": "message/send",
        "params": {
            "message": {
                "messageId": f"msg-report-{datetime.now().timestamp()}",
                "role": "user",
                "parts": [
                    {
                        "text": "LangGraph 시스템에 대한 보고서를 작성해주세요"
                    },
                    {
                        "data": {
                            "project_name": "LangGraph 테스트",
                            "execution_plan": {"step1": "분석", "step2": "구현"},
                            "research_summary": "LangGraph는 상태 기반 AI 에이전트 프레임워크입니다."
                        }
                    }
                ]
            }
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(REPORT_URL, json=report_payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                print(f"Response status: {response.status}")
                if response.status == 200:
                    result = await response.json()
                    print("Report generated successfully!")
                else:
                    print(f"Error: {await response.text()}")
    except Exception as e:
        print(f"❌ Report Writing Agent error: {type(e).__name__}: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())