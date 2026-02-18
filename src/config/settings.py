"""
src/config/settings.py

Production-ready configuration management for a Blockchain-Based Decentralized Voting Platform.
This file uses Pydantic for environment-specific settings, secrets management, and validation.
"""

from pydantic import BaseSettings, Field, validator
from typing import Optional, List
import os


class Settings(BaseSettings):
    """
    Base configuration class for the application.
    Environment-specific settings are loaded from environment variables.
    """

    # Application settings
    APP_NAME: str = Field("DecentralizedVotingPlatform", description="The name of the application.")
    ENVIRONMENT: str = Field("dev", description="Application environment: dev, staging, or prod.")
    DEBUG: bool = Field(True, description="Enable or disable debug mode.")

    # Server settings
    HOST: str = Field("0.0.0.0", description="Host address for the application server.")
    PORT: int = Field(8000, description="Port for the application server.")
    WORKERS: int = Field(2, description="Number of worker processes for the server.")

    # Database settings
    DATABASE_URL: str = Field(..., env="DATABASE_URL", description="Database connection URL.")
    DATABASE_POOL_SIZE: int = Field(10, description="Database connection pool size.")
    DATABASE_TIMEOUT: int = Field(30, description="Database connection timeout in seconds.")

    # Security settings
    SECRET_KEY: str = Field(..., env="SECRET_KEY", description="Secret key for cryptographic operations.")
    ALLOWED_HOSTS: List[str] = Field(["localhost"], description="List of allowed hosts for the application.")
    CORS_ORIGINS: List[str] = Field(["*"], description="Allowed origins for CORS.")

    # Blockchain settings
    BLOCKCHAIN_NODE_URL: str = Field(..., env="BLOCKCHAIN_NODE_URL", description="URL of the blockchain node.")
    BLOCKCHAIN_NETWORK_ID: int = Field(..., env="BLOCKCHAIN_NETWORK_ID", description="Blockchain network ID.")

    # Logging settings
    LOG_LEVEL: str = Field("INFO", description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL.")
    LOG_FORMAT: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Format for log messages.",
    )

    # Email settings
    EMAIL_HOST: str = Field(..., env="EMAIL_HOST", description="SMTP server host.")
    EMAIL_PORT: int = Field(587, description="SMTP server port.")
    EMAIL_USERNAME: str = Field(..., env="EMAIL_USERNAME", description="SMTP username.")
    EMAIL_PASSWORD: str = Field(..., env="EMAIL_PASSWORD", description="SMTP password.")
    EMAIL_USE_TLS: bool = Field(True, description="Use TLS for email communication.")

    # Resource limits
    MAX_REQUESTS_PER_MINUTE: int = Field(1000, description="Maximum number of requests per minute.")
    MAX_PAYLOAD_SIZE_MB: int = Field(10, description="Maximum payload size in megabytes.")

    # Validation
    @validator("ENVIRONMENT")
    def validate_environment(cls, value):
        if value not in {"dev", "staging", "prod"}:
            raise ValueError("ENVIRONMENT must be one of: dev, staging, prod.")
        return value

    @validator("ALLOWED_HOSTS", pre=True)
    def validate_allowed_hosts(cls, value):
        if isinstance(value, str):
            return [host.strip() for host in value.split(",")]
        return value

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Load settings
settings = Settings()

# Example usage
if __name__ == "__main__":
    print("Current Environment:", settings.ENVIRONMENT)
    print("Database URL:", settings.DATABASE_URL)
    print("Allowed Hosts:", settings.ALLOWED_HOSTS)