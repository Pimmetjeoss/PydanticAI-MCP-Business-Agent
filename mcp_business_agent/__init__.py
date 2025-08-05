"""
MCP Business Automation Agent

A sophisticated AI agent that integrates with MCP (Model Context Protocol) servers
to provide comprehensive business automation capabilities including:

- Database analysis and reporting
- Email communication and notifications  
- Web research and competitive intelligence
- Strategic thinking and decision support
- Multi-step workflow automation

Built with PydanticAI for robust agent architecture and type safety.
"""

from .agent import business_agent, get_agent_info
from .dependencies import get_mcp_dependencies, mcp_context
from .settings import settings, load_settings
from .providers import get_llm_model, validate_llm_configuration
from .models import (
    WorkflowStatus, 
    WorkflowDefinition, 
    WorkflowExecution,
    DatabaseQueryParams,
    EmailParams,
    WebScrapingParams,
    ThinkingParams
)
from .workflow_manager import WorkflowManager
from .mcp_client import MCPClient, MCPError

__version__ = "1.0.0"
__author__ = "MCP Business Agent Team"

# Main exports
__all__ = [
    # Core agent
    "business_agent",
    "get_agent_info",
    
    # Dependencies and context
    "get_mcp_dependencies", 
    "mcp_context",
    
    # Configuration
    "settings",
    "load_settings",
    "get_llm_model",
    "validate_llm_configuration",
    
    # Models and types
    "WorkflowStatus",
    "WorkflowDefinition", 
    "WorkflowExecution",
    "DatabaseQueryParams",
    "EmailParams", 
    "WebScrapingParams",
    "ThinkingParams",
    
    # Core components
    "WorkflowManager",
    "MCPClient",
    "MCPError",
    
    # Package info
    "__version__",
]

# Package metadata
PACKAGE_INFO = {
    "name": "mcp-business-agent",
    "version": __version__,
    "description": "AI-powered business automation agent with MCP integration",
    "capabilities": {
        "database": "Query, analyze, and report on business data",
        "email": "Send notifications, reports, and communications",
        "web_research": "Gather competitive intelligence and market data", 
        "thinking": "Structured problem solving and strategic analysis",
        "workflows": "Multi-step business process automation"
    },
    "supported_providers": ["openai", "anthropic"],
    "mcp_tools": [
        "listTables", "queryDatabase", "executeDatabase",
        "sendEmail", "scrapePage", "crawlWebsite", "searchWeb",
        "startThinking", "addThought", "finishThinking"
    ]
}