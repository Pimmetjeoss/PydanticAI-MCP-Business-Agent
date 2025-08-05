"""
HTTP client for MCP server communication with comprehensive error handling and retry logic.
"""

import httpx
import asyncio
import logging
import uuid
import time
from typing import Any, Dict, Optional, List
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)


class MCPError(Exception):
    """Base exception for MCP-related errors"""
    pass


class MCPAuthError(MCPError):
    """Authentication error with MCP server"""
    pass


class MCPTimeoutError(MCPError):
    """Timeout error when calling MCP server"""
    pass


class MCPToolError(MCPError):
    """Error executing MCP tool"""
    pass


class MCPRateLimitError(MCPError):
    """Rate limit exceeded error"""
    pass


class MCPServerError(MCPError):
    """Server-side error from MCP server"""
    pass


class MCPRequestStatus(Enum):
    """Status of an MCP request"""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    AUTH_ERROR = "auth_error"
    SERVER_ERROR = "server_error"


@dataclass
class MCPResponse:
    """Standardized MCP response structure"""
    success: bool
    data: Any
    error: Optional[str] = None
    tool_name: Optional[str] = None
    status: MCPRequestStatus = MCPRequestStatus.SUCCESS
    response_time_ms: Optional[int] = None
    retry_count: int = 0


@dataclass
class MCPRequestMetrics:
    """Metrics for tracking MCP request performance"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    timeout_requests: int = 0
    retry_requests: int = 0
    avg_response_time_ms: float = 0.0
    rate_limit_hits: int = 0


class MCPClient:
    """
    HTTP client for MCP server communication with retry logic and comprehensive error handling.
    
    Features:
    - Automatic retry with exponential backoff
    - Rate limiting protection
    - Request metrics tracking
    - Comprehensive error categorization
    - Async context manager support
    """
    
    def __init__(
        self, 
        base_url: str, 
        timeout: int = 30,
        retry_count: int = 3,
        rate_limit_per_second: int = 10,
        cookies: Optional[Dict[str, str]] = None,
        access_token: Optional[str] = None
    ):
        """
        Initialize MCP client with cookie-based authentication.
        
        Args:
            base_url: Base URL of the MCP server
            timeout: Request timeout in seconds
            retry_count: Number of retries for failed requests
            rate_limit_per_second: Maximum requests per second
            cookies: OAuth session cookies for authentication
            access_token: OAuth access token for Bearer authentication
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.retry_count = retry_count
        self.rate_limit_per_second = rate_limit_per_second
        self.cookies = cookies or {}
        self.access_token = access_token
        self._client: Optional[httpx.AsyncClient] = None
        self._last_request_time = 0.0
        self.metrics = MCPRequestMetrics()
    
    async def __aenter__(self):
        """Async context manager entry - Set up authenticated HTTP client"""
        # Prepare headers for MCP communication
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "MCP-Business-Agent/1.0"
        }
        
        # Add Authorization header if we have an access token
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        # Use the base URL directly for MCP endpoint (not SSE)
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            cookies=self.cookies,  # Use OAuth session cookies
            timeout=httpx.Timeout(self.timeout),
            follow_redirects=True
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def _rate_limit_check(self):
        """Implement rate limiting to respect server limits"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        min_interval = 1.0 / self.rate_limit_per_second
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            await asyncio.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    async def call_tool(
        self, 
        tool_name: str, 
        params: Dict[str, Any],
        retry_count: Optional[int] = None
    ) -> MCPResponse:
        """
        Call an MCP tool with comprehensive error handling and retry logic.
        
        Args:
            tool_name: Name of the MCP tool to call
            params: Parameters to pass to the tool
            retry_count: Override default retry count
        
        Returns:
            MCPResponse with tool execution results
        
        Raises:
            MCPError: Various MCP-specific errors based on failure type
        """
        if not self._client:
            raise MCPError("MCP client not initialized. Use async context manager.")
        
        retry_attempts = retry_count or self.retry_count
        start_time = time.time()
        last_exception = None
        
        self.metrics.total_requests += 1
        
        for attempt in range(retry_attempts + 1):
            try:
                # Rate limiting
                await self._rate_limit_check()
                
                # Prepare MCP JSON-RPC request
                request_start = time.time()
                
                # Generate a unique request ID
                request_id = str(uuid.uuid4())
                
                # Build JSON-RPC request for MCP protocol
                json_rpc_request = {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": params
                    },
                    "id": request_id
                }
                
                logger.debug(f"Calling MCP tool: {tool_name} (attempt {attempt + 1})")
                
                # Make request to the MCP endpoint
                response = await self._client.post("", json=json_rpc_request)
                request_time_ms = int((time.time() - request_start) * 1000)
                
                # Handle different response codes
                if response.status_code == 200:
                    # Parse JSON-RPC response
                    data = response.json()
                    
                    # Check for JSON-RPC error
                    if "error" in data:
                        error = data["error"]
                        error_code = error.get("code", -32000)
                        error_message = error.get("message", "Unknown error")
                        
                        # Handle specific error codes
                        if error_code == -32601:  # Method not found
                            self.metrics.failed_requests += 1
                            return MCPResponse(
                                success=False,
                                data=None,
                                error=f"Tool '{tool_name}' not found",
                                tool_name=tool_name,
                                status=MCPRequestStatus.FAILED,
                                response_time_ms=request_time_ms,
                                retry_count=attempt
                            )
                        else:
                            self.metrics.failed_requests += 1
                            return MCPResponse(
                                success=False,
                                data=None,
                                error=error_message,
                                tool_name=tool_name,
                                status=MCPRequestStatus.FAILED,
                                response_time_ms=request_time_ms,
                                retry_count=attempt
                            )
                    
                    # Success - extract result
                    result = data.get("result")
                    self.metrics.successful_requests += 1
                    self._update_avg_response_time(request_time_ms)
                    
                    return MCPResponse(
                        success=True,
                        data=result,
                        tool_name=tool_name,
                        status=MCPRequestStatus.SUCCESS,
                        response_time_ms=request_time_ms,
                        retry_count=attempt
                    )
                
                elif response.status_code == 401:
                    # Authentication error - don't retry
                    self.metrics.failed_requests += 1
                    raise MCPAuthError(
                        f"Authentication failed: Invalid GitHub OAuth token for tool {tool_name}"
                    )
                
                elif response.status_code == 429:
                    # Rate limited - exponential backoff
                    self.metrics.rate_limit_hits += 1
                    if attempt < retry_attempts:
                        wait_time = min(2 ** attempt, 60)  # Max 60 seconds
                        logger.warning(f"Rate limited calling {tool_name}, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise MCPRateLimitError(f"Rate limit exceeded for tool {tool_name}")
                
                elif response.status_code >= 500:
                    # Server error - retry
                    error_data = self._safe_json_parse(response)
                    error_msg = error_data.get("error", f"Server error: {response.status_code}")
                    
                    if attempt < retry_attempts:
                        wait_time = min(2 ** attempt, 30)
                        logger.warning(f"Server error for {tool_name}, retrying in {wait_time}s: {error_msg}")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise MCPServerError(f"Server error calling {tool_name}: {error_msg}")
                
                else:
                    # Client error (4xx) - don't retry
                    error_data = self._safe_json_parse(response)
                    error_msg = error_data.get("error", f"Client error: {response.status_code}")
                    self.metrics.failed_requests += 1
                    
                    return MCPResponse(
                        success=False,
                        data=None,
                        error=error_msg,
                        tool_name=tool_name,
                        status=MCPRequestStatus.FAILED,
                        response_time_ms=request_time_ms,
                        retry_count=attempt
                    )
            
            except httpx.TimeoutException as e:
                last_exception = e
                self.metrics.timeout_requests += 1
                
                if attempt < retry_attempts:
                    wait_time = min(2 ** attempt, 30)
                    logger.warning(f"Timeout calling {tool_name}, retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise MCPTimeoutError(f"Timeout calling {tool_name} after {retry_attempts} retries")
            
            except httpx.ConnectError as e:
                last_exception = e
                if attempt < retry_attempts:
                    wait_time = min(2 ** attempt, 30)
                    logger.warning(f"Connection error calling {tool_name}, retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise MCPError(f"Connection failed to MCP server for tool {tool_name}: {str(e)}")
            
            except Exception as e:
                last_exception = e
                if attempt < retry_attempts:
                    wait_time = min(2 ** attempt, 30)
                    logger.warning(f"Unexpected error calling {tool_name}, retrying in {wait_time}s: {str(e)}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise MCPToolError(f"Unexpected error calling {tool_name}: {str(e)}")
            
            # Track retry attempts
            if attempt > 0:
                self.metrics.retry_requests += 1
        
        # If we get here, all retries failed
        self.metrics.failed_requests += 1
        if last_exception:
            raise MCPToolError(f"All retry attempts failed for {tool_name}: {str(last_exception)}")
        else:
            raise MCPToolError(f"All retry attempts failed for {tool_name}")
    
    def _safe_json_parse(self, response: httpx.Response) -> Dict[str, Any]:
        """Safely parse JSON response with fallback"""
        try:
            return response.json()
        except (json.JSONDecodeError, ValueError):
            return {"error": response.text or "Unknown error"}
    
    def _update_avg_response_time(self, response_time_ms: int):
        """Update average response time metric"""
        if self.metrics.successful_requests == 1:
            self.metrics.avg_response_time_ms = response_time_ms
        else:
            # Exponential moving average
            alpha = 0.1
            self.metrics.avg_response_time_ms = (
                alpha * response_time_ms + 
                (1 - alpha) * self.metrics.avg_response_time_ms
            )
    
    async def health_check(self) -> MCPResponse:
        """
        Perform a health check on the MCP server.
        
        Returns:
            MCPResponse indicating server health
        """
        try:
            return await self.call_tool("health", {})
        except Exception as e:
            return MCPResponse(
                success=False,
                data=None,
                error=f"Health check failed: {str(e)}",
                tool_name="health",
                status=MCPRequestStatus.FAILED
            )
    
    async def list_available_tools(self) -> MCPResponse:
        """
        List all available tools on the MCP server.
        
        Returns:
            MCPResponse with available tools list
        """
        try:
            return await self.call_tool("list_tools", {})
        except Exception as e:
            return MCPResponse(
                success=False,
                data=None,
                error=f"Failed to list tools: {str(e)}",
                tool_name="list_tools",
                status=MCPRequestStatus.FAILED
            )
    
    def get_metrics(self) -> MCPRequestMetrics:
        """Get current request metrics"""
        return self.metrics
    
    def reset_metrics(self):
        """Reset request metrics"""
        self.metrics = MCPRequestMetrics()


async def create_mcp_client(
    server_url: str, 
    **kwargs
) -> MCPClient:
    """
    Factory function to create MCP client with OAuth authentication.
    
    Args:
        server_url: MCP server URL
        **kwargs: Additional client configuration
    
    Returns:
        Configured MCP client
    """
    return MCPClient(server_url, **kwargs)