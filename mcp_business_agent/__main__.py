"""
Entry point for running MCP Business Agent as a module.
Supports: python -m mcp_business_agent
"""

from .cli import cli

if __name__ == "__main__":
    cli()