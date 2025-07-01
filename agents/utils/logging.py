"""
로깅 유틸리티 모듈
"""
import logging
import sys
from typing import Optional
from pathlib import Path
from agents.utils.constants import LOG_FORMAT, LOG_DATE_FORMAT
from agents.utils.config import get_settings


def setup_logger(
    name: str,
    level: Optional[str] = None,
    log_file: Optional[Path] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    로거 설정
    
    Args:
        name: 로거 이름
        level: 로그 레벨 (기본값: 설정에서 가져옴)
        log_file: 로그 파일 경로 (선택사항)
        format_string: 로그 포맷 문자열 (선택사항)
    
    Returns:
        logging.Logger: 설정된 로거
    """
    settings = get_settings()
    
    # 로거 생성
    logger = logging.getLogger(name)
    
    # 레벨 설정
    if level is None:
        level = settings.log_level.upper()
    logger.setLevel(getattr(logging, level))
    
    # 핸들러가 이미 있으면 제거 (중복 방지)
    logger.handlers.clear()
    
    # 포맷터 생성
    formatter = logging.Formatter(
        format_string or LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT
    )
    
    # 콘솔 핸들러 추가
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러 추가 (선택사항)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    기본 설정으로 로거 가져오기
    
    Args:
        name: 로거 이름
    
    Returns:
        logging.Logger: 로거 인스턴스
    """
    return setup_logger(name)


class LogContext:
    """로깅 컨텍스트 매니저"""
    
    def __init__(self, logger: logging.Logger, operation: str, **kwargs):
        self.logger = logger
        self.operation = operation
        self.context = kwargs
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(
            f"{self.operation} 시작",
            extra={"context": self.context}
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type:
            self.logger.error(
                f"{self.operation} 실패 (소요시간: {duration:.2f}초)",
                exc_info=(exc_type, exc_val, exc_tb),
                extra={"context": self.context, "duration": duration}
            )
        else:
            self.logger.info(
                f"{self.operation} 완료 (소요시간: {duration:.2f}초)",
                extra={"context": self.context, "duration": duration}
            )
        
        return False  # 예외를 전파


def log_agent_communication(
    logger: logging.Logger,
    agent_name: str,
    message_type: str,
    message: str,
    metadata: Optional[dict] = None
):
    """
    에이전트 간 통신 로깅
    
    Args:
        logger: 로거 인스턴스
        agent_name: 에이전트 이름
        message_type: 메시지 타입 (request/response/error)
        message: 메시지 내용
        metadata: 추가 메타데이터
    """
    log_data = {
        "agent": agent_name,
        "message_type": message_type,
        "message": message[:200] + "..." if len(message) > 200 else message,
        "timestamp": datetime.now().isoformat()
    }
    
    if metadata:
        log_data.update(metadata)
    
    if message_type == "error":
        logger.error(f"[{agent_name}] {message_type}", extra=log_data)
    else:
        logger.info(f"[{agent_name}] {message_type}", extra=log_data)


# 전역 로거 인스턴스
root_logger = get_logger("ttimes_guide")
