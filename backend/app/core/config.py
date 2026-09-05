from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "PayPilot API"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "sqlite:///./paypilot.db"

    # Supabase (Optional)
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # CORS
    ALLOWED_ORIGINS: Union[str, List[str]] = (
        "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://localhost:8080,http://127.0.0.1:8080"
    )

    # LLM Reasoning Configuration
    LLM_PROVIDER: str = "ollama"  # "ollama", "openai", or "deterministic"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "gemma4:latest"
    OLLAMA_TIMEOUT_SECONDS: float = 120.0

    # OpenAI Configuration (Alternative Provider)
    OPENAI_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TIMEOUT_SECONDS: float = 8.0

    # Razorpay Configuration
    RAZORPAY_MODE: str = "mock"  # "mock" or "test"
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = "test_webhook_secret_paypilot"

    # Default Guardian Policy Defaults
    DEFAULT_MAX_DISCOUNT_PERCENT: float = 15.0
    DEFAULT_MAX_CAMPAIGN_BUDGET: float = 10000.0
    DEFAULT_MAX_CUSTOMER_COUNT: int = 500
    DEFAULT_MIN_AI_CONFIDENCE: float = 0.75
    DEFAULT_REQUIRE_APPROVAL_ABOVE_AMOUNT: float = 5000.0

    @property
    def cors_origins(self) -> List[str]:
        if isinstance(self.ALLOWED_ORIGINS, list):
            return self.ALLOWED_ORIGINS
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]
        return ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
