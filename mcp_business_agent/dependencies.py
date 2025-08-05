"""
Dependency injection setup for MCP Business Automation Agent.
Manages MCP client creation, authentication, and agent dependencies.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from .mcp_sse_client import MCPSSEClient, create_mcp_sse_client, MCPSSEError as MCPError
from .settings import settings
from .models import UserPermissions, AgentSession, WorkflowExecution
from .auth_manager import GitHubAuthManager

logger = logging.getLogger(__name__)


@dataclass
class MCPAgentDependencies:
    """
    Dependencies for MCP-integrated agent.
    
    This class contains all the external dependencies that the agent needs,
    including MCP client, authentication, user permissions, and session state.
    """
    # Core MCP Integration
    mcp_client: MCPSSEClient
    github_token: str
    
    # User and Session Management
    user_id: str = "default_user"
    session: Optional[AgentSession] = None
    permissions: Optional[UserPermissions] = None
    
    # Workflow State
    active_workflows: Dict[str, WorkflowExecution] = field(default_factory=dict)
    workflow_results: Dict[str, Any] = field(default_factory=dict)
    
    # Security and Rate Limiting
    rate_limiter: Optional[Any] = None
    security_context: Dict[str, Any] = field(default_factory=dict)
    
    # Agent Configuration
    agent_config: Dict[str, Any] = field(default_factory=dict)
    debug_mode: bool = False
    
    # Temporary State (for multi-step operations)
    temp_variables: Dict[str, Any] = field(default_factory=dict)
    confirmed_operations: List[str] = field(default_factory=list)
    
    def is_operation_confirmed(self, operation: str) -> bool:
        """Check if a potentially dangerous operation has been confirmed"""
        return operation in self.confirmed_operations
    
    def confirm_operation(self, operation: str):
        """Confirm a potentially dangerous operation"""
        if operation not in self.confirmed_operations:
            self.confirmed_operations.append(operation)
    
    def clear_confirmations(self):
        """Clear all operation confirmations"""
        self.confirmed_operations.clear()
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        if not self.permissions:
            return False
        return getattr(self.permissions, permission, False)
    
    def get_temp_variable(self, key: str, default: Any = None) -> Any:
        """Get temporary variable for multi-step operations"""
        return self.temp_variables.get(key, default)
    
    def set_temp_variable(self, key: str, value: Any):
        """Set temporary variable for multi-step operations"""
        self.temp_variables[key] = value
    
    def clear_temp_variables(self):
        """Clear all temporary variables"""
        self.temp_variables.clear()


class DependencyManager:
    """
    Manages creation and lifecycle of agent dependencies.
    
    This class handles:
    - MCP client creation and validation
    - User authentication and permissions
    - Session management
    - Resource cleanup
    """
    
    def __init__(self):
        self._mcp_client: Optional[MCPSSEClient] = None
        self._auth_manager: Optional[GitHubAuthManager] = None
        self._active_sessions: Dict[str, AgentSession] = {}
    
    async def create_dependencies(
        self,
        user_id: str = "default_user",
        session_id: Optional[str] = None,
        permissions: Optional[UserPermissions] = None
    ) -> MCPAgentDependencies:
        """
        Create and initialize agent dependencies.
        
        Args:
            user_id: User identifier
            session_id: Optional session identifier
            permissions: User permissions (will create default if None)
        
        Returns:
            Configured MCPAgentDependencies instance
        
        Raises:
            MCPError: If MCP client creation fails
            ValueError: If configuration is invalid
        """
        logger.info(f"Creating dependencies for user: {user_id}")
        
        # Create MCP client
        mcp_client = await self._create_mcp_client()
        
        # Set up authentication
        auth_manager = await self._create_auth_manager()
        github_token = await auth_manager.get_valid_token()
        
        # Create or retrieve session
        session = await self._get_or_create_session(user_id, session_id)
        
        # Set up user permissions
        if permissions is None:
            permissions = self._create_default_permissions(user_id)
        
        # Create agent configuration
        agent_config = self._create_agent_config()
        
        dependencies = MCPAgentDependencies(
            mcp_client=mcp_client,
            github_token=github_token,
            user_id=user_id,
            session=session,
            permissions=permissions,
            agent_config=agent_config,
            debug_mode=settings.debug
        )
        
        logger.info(f"Dependencies created successfully for user: {user_id}")
        return dependencies
    
    async def _create_mcp_client(self) -> MCPSSEClient:
        """Create and validate MCP SSE client with OAuth authentication"""
        if self._mcp_client is None:
            try:
                # Get OAuth session cookies first
                from .oauth_manager import oauth_manager
                logger.info("🔐 Attempting OAuth authentication for MCP server...")
                cookies = await oauth_manager.get_valid_session_cookies()
                
                if not cookies:
                    raise MCPError(
                        "Failed to obtain valid OAuth session cookies. "
                        "Please ensure the MCP server is running and OAuth is configured correctly."
                    )
                
                logger.info("✅ OAuth authentication successful - using session cookies")
                
                # Extract access token from cookies
                access_token = cookies.get('mcp_access_token')
                if not access_token:
                    raise MCPError("No access token found in OAuth session cookies")
                
                # Convert server URL to SSE endpoint if needed
                server_url = settings.mcp_server_url
                if server_url.endswith('/mcp'):
                    server_url = server_url.replace('/mcp', '/sse')
                elif not server_url.endswith('/sse'):
                    server_url = f"{server_url.rstrip('/')}/sse"
                
                self._mcp_client = MCPSSEClient(
                    server_url=server_url,
                    access_token=access_token,
                    timeout=settings.mcp_timeout
                )
                
                logger.info(f"✅ MCP SSE client created successfully for {server_url}")
                
            except Exception as e:
                logger.error(f"❌ Failed to create authenticated MCP SSE client: {e}")
                raise MCPError(f"MCP SSE client creation failed: {e}")
        
        return self._mcp_client
    
    async def _create_auth_manager(self) -> GitHubAuthManager:
        """Create authentication manager"""
        if self._auth_manager is None:
            self._auth_manager = GitHubAuthManager(settings.github_access_token)
        return self._auth_manager
    
    async def _get_or_create_session(
        self, 
        user_id: str, 
        session_id: Optional[str]
    ) -> AgentSession:
        """Get existing session or create new one"""
        if session_id and session_id in self._active_sessions:
            session = self._active_sessions[session_id]
            # Update last activity
            from datetime import datetime
            session.last_activity = datetime.now()
            return session
        
        # Create new session
        import uuid
        from datetime import datetime
        
        if not session_id:
            session_id = str(uuid.uuid4())
        
        session = AgentSession(
            session_id=session_id,
            user_id=user_id,
            started_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        self._active_sessions[session_id] = session
        logger.info(f"Created new session: {session_id} for user: {user_id}")
        
        return session
    
    def _create_default_permissions(self, user_id: str) -> UserPermissions:
        """Create default user permissions"""
        return UserPermissions(
            user_id=user_id,
            can_read_database=True,
            can_write_database=False,  # Require explicit grant
            can_send_email=True,
            can_scrape_web=True,
            can_execute_workflows=True,
            allowed_email_domains=settings.allowed_email_domains,
            max_query_results=settings.max_db_results,
            rate_limit_per_hour=100
        )
    
    def _create_agent_config(self) -> Dict[str, Any]:
        """Create agent configuration"""
        return {
            "max_conversation_length": 50,
            "default_timeout_seconds": settings.mcp_timeout,
            "enable_workflow_persistence": True,
            "enable_metrics_collection": True,
            "log_level": settings.log_level,
            "rate_limit_enabled": True,
            "debug_mode": settings.debug
        }
    
    async def cleanup_session(self, session_id: str):
        """Clean up resources for a session"""
        if session_id in self._active_sessions:
            session = self._active_sessions[session_id]
            
            # Clean up any active workflows
            for workflow_id in session.active_workflows:
                logger.info(f"Cleaning up workflow: {workflow_id}")
            
            # Remove session
            del self._active_sessions[session_id]
            logger.info(f"Session cleaned up: {session_id}")
    
    async def cleanup_all(self):
        """Clean up all resources"""
        logger.info("Cleaning up all dependency manager resources")
        
        # Clean up all sessions
        for session_id in list(self._active_sessions.keys()):
            await self.cleanup_session(session_id)
        
        # Close MCP client
        if self._mcp_client:
            # The MCP client will be closed when used in async context
            self._mcp_client = None
        
        logger.info("All resources cleaned up")


# Global dependency manager instance
_dependency_manager = DependencyManager()


async def get_mcp_dependencies(
    user_id: str = "default_user",
    session_id: Optional[str] = None,
    permissions: Optional[UserPermissions] = None
) -> MCPAgentDependencies:
    """
    Factory function to get configured MCP agent dependencies.
    
    Args:
        user_id: User identifier
        session_id: Optional session identifier
        permissions: User permissions (will create default if None)
    
    Returns:
        Configured MCPAgentDependencies instance
    """
    return await _dependency_manager.create_dependencies(
        user_id=user_id,
        session_id=session_id,
        permissions=permissions
    )


@asynccontextmanager
async def mcp_context(
    user_id: str = "default_user",
    session_id: Optional[str] = None,
    permissions: Optional[UserPermissions] = None
):
    """
    Async context manager for MCP agent dependencies.
    
    Usage:
        async with mcp_context(user_id="user123") as deps:
            result = await agent.run("Query the database", deps=deps)
    """
    deps = None
    try:
        deps = await get_mcp_dependencies(user_id, session_id, permissions)
        
        # MCP SSE client doesn't need context manager for dependency creation
        # Connection is managed per tool call
        yield deps
    
    finally:
        if deps and deps.session:
            # Clean up session if needed
            await _dependency_manager.cleanup_session(deps.session.session_id)


async def validate_dependencies() -> Dict[str, bool]:
    """
    Validate that all dependencies can be created successfully.
    
    Returns:
        Dictionary with validation results
    """
    results = {
        "mcp_client": False,
        "auth_manager": False,
        "settings": False,
        "overall": False
    }
    
    try:
        # Test settings
        results["settings"] = bool(settings.mcp_server_url and settings.github_access_token)
        
        # Test MCP client creation
        mcp_client = await _dependency_manager._create_mcp_client()
        results["mcp_client"] = mcp_client is not None
        
        # Test auth manager
        auth_manager = await _dependency_manager._create_auth_manager()
        results["auth_manager"] = auth_manager is not None
        
    except Exception as e:
        logger.error(f"Dependency validation failed: {e}")
    
    results["overall"] = all(results.values())
    return results


async def cleanup_dependencies():
    """Clean up global dependency resources"""
    await _dependency_manager.cleanup_all()