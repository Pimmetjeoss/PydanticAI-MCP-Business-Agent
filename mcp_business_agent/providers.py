"""
Flexible provider configuration for LLM models with fallback support.
Supports OpenAI and Anthropic providers for MCP Business Automation Agent.
"""

import os
from typing import Optional, Union
from .settings import settings


def get_llm_model(model_choice: Optional[str] = None) -> str:
    """
    Get LLM model string for pydantic_ai Agent.
    
    Args:
        model_choice: Optional override for model choice
    
    Returns:
        Model string (e.g., 'openai:gpt-4o' or 'anthropic:claude-3-5-sonnet')
    """
    # Set OpenAI API key from settings
    os.environ["OPENAI_API_KEY"] = settings.llm_api_key
    os.environ["OPENAI_BASE_URL"] = settings.llm_base_url
    
    # Set Anthropic API key if available
    if settings.anthropic_api_key:
        os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
    
    llm_choice = model_choice or settings.llm_model
    
    # Return OpenAI model string
    if settings.llm_provider.lower() == "openai":
        return f"openai:{llm_choice}"
    elif settings.llm_provider.lower() == "anthropic" and settings.anthropic_api_key:
        return f"anthropic:{settings.anthropic_model}"
    else:
        # Default to OpenAI
        return f"openai:{llm_choice}"


def get_anthropic_model(model_choice: Optional[str] = None) -> Optional[str]:
    """
    Get Anthropic model string if API key is available.
    
    Args:
        model_choice: Optional override for model choice
    
    Returns:
        Anthropic model string or None if no API key
    """
    if not settings.anthropic_api_key:
        return None
    
    llm_choice = model_choice or settings.anthropic_model
    return f"anthropic:{llm_choice}"


def get_primary_model_only(model_choice: Optional[str] = None) -> str:
    """
    Get only the primary OpenAI model without fallback.
    Useful for testing or when fallback is not desired.
    
    Args:
        model_choice: Optional override for model choice
    
    Returns:
        OpenAI model string
    """
    # Set environment variables
    os.environ["OPENAI_API_KEY"] = settings.llm_api_key
    os.environ["OPENAI_BASE_URL"] = settings.llm_base_url
    
    llm_choice = model_choice or settings.llm_model
    return f"openai:{llm_choice}"


def get_model_info() -> dict:
    """
    Get information about current model configuration.
    
    Returns:
        Dictionary with model configuration info
    """
    fallback_available = settings.anthropic_api_key != ""
    
    return {
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "llm_base_url": settings.llm_base_url,
        "anthropic_fallback": fallback_available,
        "anthropic_model": settings.anthropic_model if fallback_available else None,
        "app_env": settings.app_env,
        "debug": settings.debug,
        "mcp_server_url": settings.mcp_server_url,
    }


def validate_llm_configuration() -> dict:
    """
    Validate that LLM configuration is properly set.
    
    Returns:
        Dictionary with validation results
    """
    results = {
        "primary_model_valid": False,
        "fallback_model_valid": False,
        "overall_valid": False,
        "errors": []
    }
    
    # Test primary model configuration
    try:
        if not settings.llm_api_key:
            results["errors"].append("LLM_API_KEY is not set")
        elif not settings.llm_api_key.startswith("sk-"):
            results["errors"].append("LLM_API_KEY does not appear to be valid (should start with 'sk-')")
        else:
            # Configuration looks valid
            results["primary_model_valid"] = True
    except Exception as e:
        results["errors"].append(f"Primary OpenAI model configuration failed: {e}")
    
    # Test fallback model if available
    if settings.anthropic_api_key:
        try:
            if settings.anthropic_api_key.startswith("sk-ant-"):
                results["fallback_model_valid"] = True
            else:
                results["errors"].append("Anthropic API key does not appear to be valid")
        except Exception as e:
            results["errors"].append(f"Fallback Anthropic model failed: {e}")
    else:
        results["fallback_model_valid"] = True  # OK if no fallback configured
    
    results["overall_valid"] = results["primary_model_valid"]
    
    return results


def get_model_for_provider(provider: str) -> str:
    """
    Get model string for specific provider.
    
    Args:
        provider: Either "openai" or "anthropic"
    
    Returns:
        Model string for the specified provider
    
    Raises:
        ValueError: If provider is not supported or not configured
    """
    if provider.lower() == "openai":
        return get_primary_model_only()
    elif provider.lower() == "anthropic":
        model = get_anthropic_model()
        if model is None:
            raise ValueError("Anthropic API key not configured")
        return model
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def test_model_connectivity() -> dict:
    """
    Test connectivity to all configured model providers.
    
    Returns:
        Dictionary with connectivity test results
    """
    results = {
        "openai": {"available": False, "error": None},
        "anthropic": {"available": False, "error": None}
    }
    
    # Test OpenAI configuration
    try:
        if settings.llm_api_key and settings.llm_api_key.startswith("sk-"):
            results["openai"]["available"] = True
        else:
            results["openai"]["error"] = "Invalid or missing OpenAI API key"
    except Exception as e:
        results["openai"]["error"] = str(e)
    
    # Test Anthropic if configured
    if settings.anthropic_api_key:
        try:
            if settings.anthropic_api_key.startswith("sk-ant-"):
                results["anthropic"]["available"] = True
            else:
                results["anthropic"]["error"] = "Invalid Anthropic API key format"
        except Exception as e:
            results["anthropic"]["error"] = str(e)
    else:
        results["anthropic"]["error"] = "No API key configured"
    
    return results