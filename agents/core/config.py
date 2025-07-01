"""
애플리케이션 설정 관리 모듈
"""
from typing import Optional
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """애플리케이션 설정"""
    tavily_api_key: str | None = None
    
    azure_openai_api_key: SecretStr | None = None
    azure_openai_endpoint: str | None = None
    azure_openai_api_version: str = "2025-02-01-preview"
    azure_openai_deployment_name: str = "gpt-4.1"
    
    # Database Configuration
    postgres_host: str | None = "localhost"
    postgres_port: int | None = 5432
    postgres_user: str | None = "ttimes"
    postgres_password: str | None = None
    postgres_db: str | None = "ttimes_guide"
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    
    # LangChain Configuration
    langchain_api_key: Optional[str] = None
    langchain_tracing_v2: bool = False
    langchain_project: str = "ttimes-guide-coding"
    
    # Server Configuration
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    reload: bool = False
    log_level: str = "info"
    
    # Environment
    environment: str = "development"
    
    # Agent URLs
    web_search_agent_url: str = "http://localhost:8001"
    vector_search_agent_url: str = "http://localhost:8002"
    planning_agent_url: str = "http://localhost:8003"
    report_writing_agent_url: str = "http://localhost:8004"
    memory_agent_url: str = "http://localhost:8005"
    orchestrator_url: str = "http://localhost:8000"
    
    # Agent Configuration
    agent_response_timeout: int = 300  # 5 minutes
    agent_max_retries: int = 3
    
    # Vector DB Configuration
    vector_collection_name: str = "ttimes_documents"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536
    
    # Report Configuration
    max_report_length: int = 10000  # characters
    default_report_format: str = "markdown"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    @property
    def postgres_url(self) -> str:
        """PostgreSQL 연결 URL"""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
    
    @property
    def redis_url(self) -> str:
        """Redis 연결 URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}"
        return f"redis://{self.redis_host}:{self.redis_port}"
    
    @property
    def is_production(self) -> bool:
        """프로덕션 환경 여부"""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """개발 환경 여부"""
        return self.environment.lower() == "development"


@lru_cache()
def get_settings() -> Settings:
    """
    설정 싱글톤 반환
    
    Returns:
        Settings: 애플리케이션 설정
    """
    return Settings()
