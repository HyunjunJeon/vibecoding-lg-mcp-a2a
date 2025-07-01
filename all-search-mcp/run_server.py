#!/usr/bin/env python
"""All-Search MCP Server 실행 스크립트"""
import os
import sys
import argparse
import asyncio
import signal
from pathlib import Path

import yaml
import uvloop
from fastmcp import FastMCP
from dotenv import load_dotenv

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 현재 디렉토리에서 server.py의 mcp 인스턴스 import
sys.path.insert(0, str(Path(__file__).parent))
from server import mcp


def load_config(config_path: str) -> dict:
    """설정 파일 로드"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # 환경 변수 치환
    def replace_env_vars(obj):
        if isinstance(obj, str):
            # ${VAR_NAME:-default} 패턴 처리
            import re
            pattern = r'\$\{([^}:]+)(?::-([^}]*))?\}'
            
            def replacer(match):
                var_name = match.group(1)
                default_value = match.group(2) or ""
                return os.getenv(var_name, default_value)
            
            return re.sub(pattern, replacer, obj)
        elif isinstance(obj, dict):
            return {k: replace_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [replace_env_vars(item) for item in obj]
        return obj
    
    return replace_env_vars(config)


def run_mcp_server_http(mcp_server: FastMCP, port: int = 8090):
    """FastMCP 2.x Streamable HTTP 서버 실행"""
    print(f"FastMCP Streamable HTTP 서버를 포트 {port}에서 시작합니다...", file=sys.stderr)
    # FastMCP 2.x의 권장 Streamable HTTP 방식 (port 파라미터 포함)
    mcp_server.run(
        transport="http",
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )


def setup_signal_handlers():
    """시그널 핸들러 설정"""
    def signal_handler(sig, frame):
        print("\n서버 종료 중...", file=sys.stderr)
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="All-Search MCP Server")
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="설정 파일 경로 (기본값: config.yaml)"
    )
    parser.add_argument(
        "--env",
        default=".env",
        help="환경 변수 파일 경로 (기본값: .env)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8090,
        help="HTTP 서버 포트 (기본값: 8090)"
    )
    
    args = parser.parse_args()
    
    # 환경 변수 로드
    if os.path.exists(args.env):
        load_dotenv(args.env)
        print(f"환경 변수 로드: {args.env}", file=sys.stderr)
    
    # 설정 로드
    config_path = Path(__file__).parent / args.config
    if config_path.exists():
        config = load_config(str(config_path))
        print(f"설정 파일 로드: {config_path}", file=sys.stderr)
    else:
        config = {}
        print("설정 파일 없음, 기본 설정 사용", file=sys.stderr)
    
    # uvloop 설정
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    
    # 시그널 핸들러 설정
    setup_signal_handlers()
    
    # FastMCP 2.x HTTP 서버 실행
    print("FastMCP HTTP 서버를 시작합니다...", file=sys.stderr)
    run_mcp_server_http(mcp, args.port)


if __name__ == "__main__":
    main()