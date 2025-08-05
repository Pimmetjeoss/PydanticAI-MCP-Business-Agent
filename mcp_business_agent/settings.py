"""
Configuration management for MCP Business Automation Agent using pydantic-settings.
"""

import os
from typing import Optional, Union
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, ConfigDict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings with environment variable support for MCP Business Agent."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # MCP Configuration
    mcp_server_url: str = Field(..., description="MCP server URL")
    github_access_token: str = Field(..., description="GitHub OAuth token")
    
    # LLM Configuration
    llm_provider: str = Field(default="openai", description="LLM provider")
    llm_api_key: str = Field(..., description="API key for the LLM provider")
    llm_model: str = Field(default="gpt-4o", description="Model name to use")
    llm_base_url: str = Field(
        default="https://api.openai.com/v1", 
        description="Base URL for the LLM API"
    )
    
    # Anthropic Fallback
    anthropic_api_key: str = Field(default="", description="Anthropic API key for fallback")
    anthropic_model: str = Field(
        default="claude-3-5-sonnet-20241022", 
        description="Anthropic fallback model"
    )
    
    # Application Configuration
    app_env: str = Field(default="development", description="Application environment")
    log_level: str = Field(default="INFO", description="Logging level")
    debug: bool = Field(default=False, description="Debug mode flag")
    
    # MCP Client Configuration
    mcp_timeout: int = Field(default=30, description="MCP request timeout in seconds")
    mcp_retry_count: int = Field(default=3, description="MCP request retry count")
    mcp_rate_limit: int = Field(default=10, description="MCP requests per second limit")
    
    # Security Configuration
    max_db_results: int = Field(default=1000, description="Maximum database query results")
    allowed_email_domains: Union[str, list[str]] = Field(
        default="@company.com", 
        description="Comma-separated allowed email domains for sending"
    )
    
    @field_validator("mcp_server_url")
    @classmethod
    def validate_mcp_url(cls, v):
        """Ensure MCP server URL is valid."""
        if not v or not v.startswith(("http://", "https://")):
            raise ValueError("MCP server URL must be a valid HTTP/HTTPS URL")
        return v
    
    @field_validator("llm_api_key", "github_access_token")
    @classmethod
    def validate_required_keys(cls, v):
        """Ensure required API keys are not empty."""
        if not v or v.strip() == "":
            raise ValueError("Required API key cannot be empty")
        return v
    
    @field_validator("mcp_timeout")
    @classmethod
    def validate_timeout(cls, v):
        """Ensure timeout is reasonable."""
        if v < 1 or v > 300:
            raise ValueError("MCP timeout must be between 1 and 300 seconds")
        return v
    
    @field_validator("allowed_email_domains")
    @classmethod
    def validate_email_domains(cls, v):
        """Convert comma-separated string to list of domains."""
        if isinstance(v, str):
            if v.strip() == "":
                return ["@company.com"]  # Return default value
            # Split by comma and strip whitespace
            domains = [domain.strip() for domain in v.split(",") if domain.strip()]
            return domains if domains else ["@company.com"]
        return v


def load_settings() -> Settings:
    """Load settings with proper error handling and environment loading."""
    # Load environment variables from .env file
    load_dotenv()
    
    try:
        return Settings()
    except Exception as e:
        error_msg = f"Failed to load settings: {e}"
        if "llm_api_key" in str(e).lower():
            error_msg += "\nMake sure to set LLM_API_KEY in your .env file"
        if "mcp_server_url" in str(e).lower():
            error_msg += "\nMake sure to set MCP_SERVER_URL in your .env file"
        if "github_access_token" in str(e).lower():
            error_msg += "\nMake sure to set GITHUB_ACCESS_TOKEN in your .env file"
        raise ValueError(error_msg) from e


# Global settings instance
try:
    settings = load_settings()
except Exception:
    # For testing, create settings with dummy values
    import os
    os.environ.setdefault("LLM_API_KEY", "test_key")
    os.environ.setdefault("MCP_SERVER_URL", "https://test-mcp-server.com")
    os.environ.setdefault("GITHUB_ACCESS_TOKEN", "test_token")
    settings = Settings()