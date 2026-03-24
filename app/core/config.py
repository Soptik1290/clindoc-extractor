from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str = ""
    model: str = "gpt-5.4-nano"
    openai_timeout: float = 10.0
    openai_max_retries: int = 2
    
    # App
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # Extrakce
    use_llm: bool = True          # False → vždy regex fallback
    confidence_threshold: float = 0.5
    
    redis_url: str = "redis://localhost:6379"
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
