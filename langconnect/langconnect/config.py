import json

from langchain_core.embeddings import Embeddings
from starlette.config import Config

env = Config()

IS_TESTING = env("IS_TESTING", cast=str, default="").lower() == "true"

# API Key for simple authentication (instead of Supabase)
LANGCONNECT_API_KEY = env("LANGCONNECT_API_KEY", cast=str, default="test-api-key")


def get_embeddings() -> Embeddings:
    """Get the embeddings instance based on the environment."""
    if IS_TESTING:
        from langchain_core.embeddings import DeterministicFakeEmbedding

        return DeterministicFakeEmbedding(size=512)
    from langchain_openai import AzureOpenAIEmbeddings

    # Azure OpenAI configuration
    return AzureOpenAIEmbeddings(
        azure_endpoint=env("AZURE_OPENAI_ENDPOINT", cast=str, default=""),
        api_key=env("AZURE_OPENAI_API_KEY", cast=str, default=""),
        api_version=env("AZURE_OPENAI_API_VERSION", cast=str, default="2025-02-01-preview"),
        deployment=env("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT", cast=str, default="text-embedding-ada-002")
    )


DEFAULT_EMBEDDINGS = get_embeddings()
DEFAULT_COLLECTION_NAME = "default_collection"


# Database configuration
POSTGRES_HOST = env("POSTGRES_HOST", cast=str, default="localhost")
POSTGRES_PORT = env("POSTGRES_PORT", cast=int, default="5432")
POSTGRES_USER = env("POSTGRES_USER", cast=str, default="langchain")
POSTGRES_PASSWORD = env("POSTGRES_PASSWORD", cast=str, default="langchain")
POSTGRES_DB = env("POSTGRES_DB", cast=str, default="langchain_test")

# Read allowed origins from environment variable
ALLOW_ORIGINS_JSON = env("ALLOW_ORIGINS", cast=str, default="")

if ALLOW_ORIGINS_JSON:
    ALLOWED_ORIGINS = json.loads(ALLOW_ORIGINS_JSON.strip())
    print(f"ALLOW_ORIGINS environment variable set to: {ALLOW_ORIGINS_JSON}")
else:
    ALLOWED_ORIGINS = "http://localhost:3000"
    print("ALLOW_ORIGINS environment variable not set.")
