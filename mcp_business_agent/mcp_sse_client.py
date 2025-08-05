"""
MCP SSE Client for proper Server-Sent Events transport with authentication.
Replaces the old HTTP-based client with proper MCP SDK integration.
"""

import asyncio
import logging
import httpx
from typing import Any, Dict, Optional, List
from dataclasses import dataclass
from contextlib import asynccontextmanager

from mcp import ClientSession
from mcp.client.sse import sse_client

logger = logging.getLogger(__name__)


class MCPSSEError(Exception):
    """Base exception for MCP SSE-related errors"""
    pass


class MCPSSEAuthError(MCPSSEError):
    """Authentication error with MCP SSE server"""
    pass


class MCPSSETimeoutError(MCPSSEError):
    """Timeout error when calling MCP SSE server"""
    pass


@dataclass
class MCPSSEResponse:
    """Standardized MCP SSE response structure"""
    success: bool
    data: Any
    error: Optional[str] = None
    tool_name: Optional[str] = None


class BearerAuth(httpx.Auth):
    """HTTPX Auth handler for Bearer token authentication"""
    
    def __init__(self, token: str):
        self.token = token
    
    def auth_flow(self, request):
        request.headers["Authorization"] = f"Bearer {self.token}"
        request.headers["User-Agent"] = "MCP-Business-Agent/1.0"
        yield request


class MCPSSEClient:
    """
    MCP SSE client using the official MCP SDK with authentication.
    
    Features:
    - Server-Sent Events transport
    - Bearer token authentication
    - Proper MCP SDK integration
    - Tool listing and execution
    """
    
    def __init__(
        self, 
        server_url: str,
        access_token: str,
        timeout: int = 30
    ):
        """
        Initialize MCP SSE client with authentication.
        
        Args:
            server_url: MCP SSE server URL (should end with /sse)
            access_token: OAuth access token for Bearer authentication
            timeout: Request timeout in seconds
        """
        self.server_url = server_url
        self.access_token = access_token
        self.timeout = timeout
        self._session: Optional[ClientSession] = None
        self._auth_handler = BearerAuth(access_token)
    
    @asynccontextmanager
    async def connect(self):
        """
        Async context manager for MCP SSE connection.
        
        Usage:
            async with client.connect() as session:
                tools = await session.list_tools()
        """
        try:
            logger.info(f"Connecting to MCP SSE server at {self.server_url}")
            
            # Connect using SSE client with authentication
            async with sse_client(self.server_url, auth=self._auth_handler) as (read, write):
                logger.info("✅ Connected to MCP server via SSE!")
                
                # Create MCP client session
                async with ClientSession(read, write) as session:
                    logger.info("✅ MCP Client Session created!")
                    
                    # Initialize the session
                    await session.initialize()
                    logger.info("✅ MCP Session initialized!")
                    
                    self._session = session
                    yield session
                    
        except Exception as e:
            logger.error(f"Failed to connect to MCP SSE server: {e}")
            raise MCPSSEError(f"Connection failed: {e}")
        finally:
            self._session = None
    
    async def list_available_tools(self) -> MCPSSEResponse:
        """
        List all available tools on the MCP server.
        
        Returns:
            MCPSSEResponse with available tools list
        """
        try:
            async with self.connect() as session:
                result = await session.list_tools()
                
                tools_info = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema
                    }
                    for tool in result.tools
                ]
                
                return MCPSSEResponse(
                    success=True,
                    data={"tools": tools_info, "count": len(tools_info)}
                )
                
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return MCPSSEResponse(
                success=False,
                data=None,
                error=f"Failed to list tools: {str(e)}"
            )
    
    async def call_tool(
        self, 
        tool_name: str, 
        params: Dict[str, Any]
    ) -> MCPSSEResponse:
        """
        Call an MCP tool with parameters.
        
        Args:
            tool_name: Name of the MCP tool to call
            params: Parameters to pass to the tool
            
        Returns:
            MCPSSEResponse with tool execution results
        """
        try:
            async with self.connect() as session:
                logger.info(f"Calling MCP tool: {tool_name} with params: {params}")
                
                response = await session.call_tool(tool_name, params)
                
                logger.info(f"✅ Tool call successful: {tool_name}")
                
                return MCPSSEResponse(
                    success=True,
                    data=response,
                    tool_name=tool_name
                )
                
        except Exception as e:
            logger.error(f"Tool call failed for {tool_name}: {e}")
            return MCPSSEResponse(
                success=False,
                data=None,
                error=f"Tool call failed: {str(e)}",
                tool_name=tool_name
            )
    
    async def health_check(self) -> MCPSSEResponse:
        """
        Perform a health check on the MCP server.
        
        Returns:
            MCPSSEResponse indicating server health
        """
        try:
            async with self.connect() as session:
                # Try to list tools as a health check
                result = await session.list_tools()
                
                return MCPSSEResponse(
                    success=True,
                    data={"status": "healthy", "tools_count": len(result.tools)}
                )
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return MCPSSEResponse(
                success=False,
                data=None,
                error=f"Health check failed: {str(e)}"
            )


async def create_mcp_sse_client(
    server_url: str,
    access_token: str,
    **kwargs
) -> MCPSSEClient:
    """
    Factory function to create MCP SSE client with OAuth authentication.
    
    Args:
        server_url: MCP SSE server URL
        access_token: OAuth access token
        **kwargs: Additional client configuration
    
    Returns:
        Configured MCPSSEClient
    """
    return MCPSSEClient(server_url, access_token, **kwargs)