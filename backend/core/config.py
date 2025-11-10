"""
Configuration management for the application
Centralizes all settings from environment variables with validation
"""

import os
from typing import List, Optional
from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # ========================================================================
    # ENVIRONMENT & DEBUG
    # ========================================================================
    
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # ========================================================================
    # API CONFIGURATION
    # ========================================================================
    
    API_TITLE: str = os.getenv("API_TITLE", "Real-Time System Monitoring API")
    API_VERSION: str = os.getenv("API_VERSION", "1.0.0")
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/app.log")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")
    
    # ========================================================================
    # API KEYS (REQUIRED - User must provide)
    # ========================================================================
    
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    HUGGINGFACE_API_TOKEN: str = os.getenv("HUGGINGFACE_API_TOKEN", "")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    
    # ========================================================================
    # DATABASE CONFIGURATION
    # ========================================================================
    
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/system_monitoring"
    )
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "20"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "3600"))
    
    # Time-series database
    INFLUXDB_URL: str = os.getenv("INFLUXDB_URL", "http://localhost:8086")
    INFLUXDB_TOKEN: str = os.getenv("INFLUXDB_TOKEN", "")
    INFLUXDB_ORG: str = os.getenv("INFLUXDB_ORG", "")
    INFLUXDB_BUCKET: str = os.getenv("INFLUXDB_BUCKET", "system_metrics")
    
    # ========================================================================
    # CACHE & MESSAGE QUEUE
    # ========================================================================
    
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD", None)
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))
    CACHE_MAX_SIZE: int = int(os.getenv("CACHE_MAX_SIZE", "1000"))
    
    # ========================================================================
    # ML MODEL CONFIGURATION
    # ========================================================================
    
    # GROQ Configuration
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama2-70b-4096")
    
    # Ollama Configuration (Local LLM)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama2")
    
    # Hugging Face Models
    HF_MODEL_NAME: str = os.getenv(
        "HF_MODEL_NAME",
        "distilbert-base-uncased-finetuned-sst-2-english"
    )
    HF_MODEL_DEVICE: str = os.getenv("HF_MODEL_DEVICE", "cpu")
    
    # Anomaly Detection
    ANOMALY_MODEL: str = os.getenv("ANOMALY_MODEL", "isolation_forest")
    ANOMALY_THRESHOLD: float = float(os.getenv("ANOMALY_THRESHOLD", "0.7"))
    
    # ========================================================================
    # DATA PIPELINE CONFIGURATION
    # ========================================================================
    
    DATA_COLLECTION_INTERVAL: int = int(os.getenv("DATA_COLLECTION_INTERVAL", "5"))
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "100"))
    RETENTION_DAYS: int = int(os.getenv("RETENTION_DAYS", "30"))
    
    # Kafka (for large-scale deployments)
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv(
        "KAFKA_BOOTSTRAP_SERVERS",
        "localhost:9092"
    )
    KAFKA_TOPIC: str = os.getenv("KAFKA_TOPIC", "system_metrics")
    
    # ========================================================================
    # SECURITY & AUTHENTICATION
    # ========================================================================
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    
    # CORS
    CORS_ORIGINS_STR: str = "http://localhost:8501"
    CORS_ORIGINS: List[str] = []
    
    def model_post_init(self, __context):
        """Post-initialization hook to set CORS origins from string"""
        self.CORS_ORIGINS = [origin.strip() for origin in self.CORS_ORIGINS_STR.split(",")]
    
    @property
    def cors_origins(self) -> List[str]:
        """Get CORS origins"""
        return self.CORS_ORIGINS
    
    # ========================================================================
    # FEATURE FLAGS
    # ========================================================================
    
    ENABLE_ANOMALY_DETECTION: bool = (
        os.getenv("ENABLE_ANOMALY_DETECTION", "true").lower() == "true"
    )
    ENABLE_PREDICTIVE_ALERTS: bool = (
        os.getenv("ENABLE_PREDICTIVE_ALERTS", "true").lower() == "true"
    )
    ENABLE_LLM_ANALYSIS: bool = (
        os.getenv("ENABLE_LLM_ANALYSIS", "true").lower() == "true"
    )
    ENABLE_ADVANCED_VISUALIZATIONS: bool = (
        os.getenv("ENABLE_ADVANCED_VISUALIZATIONS", "true").lower() == "true"
    )
    ENABLE_REAL_TIME_UPDATES: bool = (
        os.getenv("ENABLE_REAL_TIME_UPDATES", "true").lower() == "true"
    )
    
    # ========================================================================
    # NOTIFICATION SETTINGS
    # ========================================================================
    
    SLACK_WEBHOOK_URL: Optional[str] = os.getenv("SLACK_WEBHOOK_URL", None)
    PAGERDUTY_API_KEY: Optional[str] = os.getenv("PAGERDUTY_API_KEY", None)
    
    # ========================================================================
    # PERFORMANCE TUNING
    # ========================================================================
    
    NUM_WORKERS: int = int(os.getenv("NUM_WORKERS", "4"))
    WORKER_TIMEOUT: int = int(os.getenv("WORKER_TIMEOUT", "300"))
    
    # ========================================================================
    # MONITORING & METRICS
    # ========================================================================
    
    PROMETHEUS_PORT: int = int(os.getenv("PROMETHEUS_PORT", "9090"))
    ENABLE_METRICS: bool = os.getenv("ENABLE_METRICS", "true").lower() == "true"
    
    class Config:
        env_file = "../.env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()


def validate_required_settings():
    """Validate that all required settings are provided"""
    required_keys = [
        "GROQ_API_KEY",
        "HUGGINGFACE_API_TOKEN",
    ]
    
    missing = []
    for key in required_keys:
        if not getattr(settings, key, ""):
            missing.append(key)
    
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            f"Please set these in your .env file or system environment."
        )


if __name__ == "__main__":
    # Print current settings (mask sensitive data)
    print("Current Settings:")
    for key, value in settings.dict().items():
        if any(sensitive in key.upper() for sensitive in ["KEY", "TOKEN", "PASSWORD", "URL"]):
            value = "***MASKED***"
        print(f"  {key}: {value}")
