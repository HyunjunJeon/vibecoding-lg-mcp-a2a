"""
애플리케이션 상수 정의
"""

# Agent Ports
ORCHESTRATOR_PORT = 8000
WEB_SEARCH_AGENT_PORT = 8001
VECTOR_SEARCH_AGENT_PORT = 8002
PLANNING_AGENT_PORT = 8003
REPORT_WRITING_AGENT_PORT = 8004
MEMORY_AGENT_PORT = 8005

# Timeout Settings (seconds)
DEFAULT_TIMEOUT = 30
AGENT_TIMEOUT = 300  # 5 minutes
SEARCH_TIMEOUT = 60  # 1 minute

# Retry Settings
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

# Search Settings
DEFAULT_SEARCH_LIMIT = 20
MAX_SEARCH_RESULTS = 100
DEFAULT_VECTOR_TOP_K = 5
MIN_RELEVANCE_SCORE = 0.6

# Report Settings
MIN_REPORT_LENGTH = 500  # characters
MAX_REPORT_LENGTH = 10000  # characters
DEFAULT_REPORT_LENGTH = 3000  # characters

# Memory Settings
MAX_MEMORY_ENTRIES = 100
MEMORY_IMPORTANCE_THRESHOLD = 0.7
CONVERSATION_SUMMARY_THRESHOLD = 10  # messages

# LLM Settings
DEFAULT_TEMPERATURE = 0.7
MAX_TOKENS = 4000
DEFAULT_MODEL = "gpt-4o-mini"

# Embedding Settings
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536
EMBEDDING_BATCH_SIZE = 100

# Cache Settings
CACHE_TTL = 3600  # 1 hour
CACHE_MAX_SIZE = 1000

# Database Settings
DB_POOL_SIZE = 20
DB_MAX_OVERFLOW = 40
DB_POOL_TIMEOUT = 30

# API Rate Limits
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 60  # seconds

# File Settings
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_TYPES = [".txt", ".md", ".pdf", ".docx", ".html"]

# Logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Error Messages
ERROR_INVALID_REQUEST = "잘못된 요청입니다."
ERROR_AGENT_UNAVAILABLE = "에이전트를 사용할 수 없습니다."
ERROR_TIMEOUT = "요청 시간이 초과되었습니다."
ERROR_INTERNAL = "내부 서버 오류가 발생했습니다."
ERROR_RATE_LIMIT = "요청 한도를 초과했습니다."

# Success Messages
SUCCESS_REPORT_CREATED = "보고서가 성공적으로 생성되었습니다."
SUCCESS_SEARCH_COMPLETED = "검색이 완료되었습니다."
SUCCESS_MEMORY_SAVED = "메모리가 저장되었습니다."
