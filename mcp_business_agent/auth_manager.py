"""
GitHub OAuth management for MCP Business Automation Agent.
Handles token validation, refresh, and authentication state.
"""

import httpx
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)


class AuthError(Exception):
    """Base authentication error"""
    pass


class TokenExpiredError(AuthError):
    """Token has expired"""
    pass


class TokenInvalidError(AuthError):
    """Token is invalid"""
    pass


class TokenRefreshError(AuthError):
    """Failed to refresh token"""
    pass


@dataclass
class TokenInfo:
    """Information about a GitHub OAuth token"""
    token: str
    expires_at: Optional[datetime] = None
    scopes: list[str] = None
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[datetime] = None
    user_login: Optional[str] = None
    user_id: Optional[int] = None
    last_validated: Optional[datetime] = None


class GitHubAuthManager:
    """
    Manages GitHub OAuth tokens for MCP server authentication.
    
    Features:
    - Token validation
    - Rate limit tracking
    - Token refresh (if using GitHub App)
    - User information caching
    """
    
    def __init__(self, initial_token: str):
        """
        Initialize GitHub auth manager.
        
        Args:
            initial_token: Initial GitHub OAuth token
        """
        self.token_info = TokenInfo(token=initial_token)
        self._client: Optional[httpx.AsyncClient] = None
        self._validation_cache_ttl = timedelta(minutes=5)
    
    async def __aenter__(self):
        """Async context manager entry"""
        self._client = httpx.AsyncClient(
            base_url="https://api.github.com",
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "MCP-Business-Agent/1.0"
            },
            timeout=httpx.Timeout(30.0)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def get_valid_token(self) -> str:
        """
        Get a valid GitHub token, refreshing if necessary.
        
        Returns:
            Valid GitHub OAuth token
        
        Raises:
            TokenInvalidError: If token is invalid and cannot be refreshed
            TokenExpiredError: If token is expired and cannot be refreshed
        """
        # Check if we need to validate the token
        if self._should_validate_token():
            await self._validate_token()
        
        return self.token_info.token
    
    def _should_validate_token(self) -> bool:
        """Check if token should be validated"""
        if not self.token_info.last_validated:
            return True
        
        time_since_validation = datetime.now() - self.token_info.last_validated
        return time_since_validation > self._validation_cache_ttl
    
    async def _validate_token(self):
        """Validate the current token with GitHub API"""
        if not self._client:
            async with self:
                await self._validate_token()
                return
        
        try:
            logger.debug("Validating GitHub token")
            
            response = await self._client.get(
                "/user",
                headers={"Authorization": f"Bearer {self.token_info.token}"}
            )
            
            if response.status_code == 200:
                user_data = response.json()
                await self._update_token_info(response, user_data)
                logger.debug("Token validation successful")
                
            elif response.status_code == 401:
                logger.error("Token validation failed: Unauthorized")
                raise TokenInvalidError("GitHub token is invalid or expired")
                
            elif response.status_code == 403:
                # Check if it's a rate limit issue
                if "rate limit" in response.text.lower():
                    await self._handle_rate_limit(response)
                    # Retry validation after rate limit
                    await asyncio.sleep(1)
                    await self._validate_token()
                else:
                    raise TokenInvalidError("GitHub token lacks required permissions")
                    
            else:
                logger.warning(f"Unexpected response from GitHub API: {response.status_code}")
                raise AuthError(f"Token validation failed with status {response.status_code}")
        
        except httpx.RequestError as e:
            logger.error(f"Network error during token validation: {e}")
            raise AuthError(f"Network error during token validation: {e}")
    
    async def _update_token_info(self, response: httpx.Response, user_data: Dict[str, Any]):
        """Update token information from API response"""
        self.token_info.last_validated = datetime.now()
        self.token_info.user_login = user_data.get("login")
        self.token_info.user_id = user_data.get("id")
        
        # Update rate limit information
        await self._update_rate_limit_info(response)
        
        # Update scopes if available
        scopes_header = response.headers.get("X-OAuth-Scopes")
        if scopes_header:
            self.token_info.scopes = [scope.strip() for scope in scopes_header.split(",")]
    
    async def _update_rate_limit_info(self, response: httpx.Response):
        """Update rate limit information from response headers"""
        rate_limit_remaining = response.headers.get("X-RateLimit-Remaining")
        if rate_limit_remaining:
            self.token_info.rate_limit_remaining = int(rate_limit_remaining)
        
        rate_limit_reset = response.headers.get("X-RateLimit-Reset")
        if rate_limit_reset:
            reset_timestamp = int(rate_limit_reset)
            self.token_info.rate_limit_reset = datetime.fromtimestamp(reset_timestamp)
    
    async def _handle_rate_limit(self, response: httpx.Response):
        """Handle rate limit response"""
        reset_header = response.headers.get("X-RateLimit-Reset")
        if reset_header:
            reset_time = datetime.fromtimestamp(int(reset_header))
            wait_seconds = (reset_time - datetime.now()).total_seconds()
            logger.warning(f"GitHub API rate limit hit, reset in {wait_seconds:.0f} seconds")
            
            # Update rate limit info
            self.token_info.rate_limit_remaining = 0
            self.token_info.rate_limit_reset = reset_time
        else:
            logger.warning("GitHub API rate limit hit, no reset time provided")
    
    async def check_permissions(self, required_scopes: list[str] = None) -> Dict[str, bool]:
        """
        Check if token has required permissions.
        
        Args:
            required_scopes: List of required OAuth scopes
        
        Returns:
            Dictionary with permission check results
        """
        if required_scopes is None:
            required_scopes = ["repo", "user:email"]
        
        # Ensure token is validated
        await self.get_valid_token()
        
        results = {
            "valid": self.token_info.last_validated is not None,
            "has_user_info": bool(self.token_info.user_login),
            "rate_limit_ok": self._is_rate_limit_ok(),
            "required_scopes": {}
        }
        
        # Check individual scopes
        if self.token_info.scopes:
            for scope in required_scopes:
                results["required_scopes"][scope] = scope in self.token_info.scopes
        else:
            # If we can't get scope info, assume they're available if token is valid
            for scope in required_scopes:
                results["required_scopes"][scope] = results["valid"]
        
        results["all_permissions_ok"] = all([
            results["valid"],
            results["rate_limit_ok"],
            all(results["required_scopes"].values())
        ])
        
        return results
    
    def _is_rate_limit_ok(self) -> bool:
        """Check if we're within rate limits"""
        if self.token_info.rate_limit_remaining is None:
            return True  # Unknown, assume OK
        
        if self.token_info.rate_limit_remaining <= 0:
            # Check if rate limit has reset
            if self.token_info.rate_limit_reset:
                return datetime.now() > self.token_info.rate_limit_reset
            return False
        
        return self.token_info.rate_limit_remaining > 10  # Keep some buffer
    
    async def get_user_info(self) -> Dict[str, Any]:
        """
        Get GitHub user information.
        
        Returns:
            Dictionary with user information
        """
        await self.get_valid_token()
        
        return {
            "login": self.token_info.user_login,
            "id": self.token_info.user_id,
            "scopes": self.token_info.scopes or [],
            "rate_limit_remaining": self.token_info.rate_limit_remaining,
            "rate_limit_reset": self.token_info.rate_limit_reset,
            "last_validated": self.token_info.last_validated
        }
    
    async def wait_for_rate_limit_reset(self):
        """Wait for GitHub API rate limit to reset"""
        if not self.token_info.rate_limit_reset:
            logger.warning("No rate limit reset time available")
            return
        
        now = datetime.now()
        if now >= self.token_info.rate_limit_reset:
            logger.info("Rate limit already reset")
            return
        
        wait_seconds = (self.token_info.rate_limit_reset - now).total_seconds()
        logger.info(f"Waiting {wait_seconds:.0f} seconds for rate limit reset")
        
        await asyncio.sleep(wait_seconds)
        
        # Clear rate limit info to force re-validation
        self.token_info.rate_limit_remaining = None
        self.token_info.rate_limit_reset = None
    
    def get_auth_header(self) -> Dict[str, str]:
        """
        Get authorization header for HTTP requests.
        
        Returns:
            Dictionary with Authorization header
        """
        return {"Authorization": f"Bearer {self.token_info.token}"}
    
    async def test_connectivity(self) -> Dict[str, Any]:
        """
        Test connectivity to GitHub API.
        
        Returns:
            Dictionary with connectivity test results
        """
        results = {
            "connected": False,
            "authenticated": False,
            "user_info": None,
            "permissions": None,
            "rate_limit_ok": False,
            "error": None
        }
        
        try:
            async with self:
                # Test basic connectivity
                response = await self._client.get("/")
                results["connected"] = response.status_code == 200
                
                if results["connected"]:
                    # Test authentication
                    await self._validate_token()
                    results["authenticated"] = True
                    results["user_info"] = await self.get_user_info()
                    results["permissions"] = await self.check_permissions()
                    results["rate_limit_ok"] = self._is_rate_limit_ok()
        
        except Exception as e:
            results["error"] = str(e)
            logger.error(f"GitHub connectivity test failed: {e}")
        
        return results


# Utility functions
async def validate_github_token(token: str) -> Dict[str, Any]:
    """
    Validate a GitHub token and return information about it.
    
    Args:
        token: GitHub OAuth token to validate
    
    Returns:
        Dictionary with validation results
    """
    auth_manager = GitHubAuthManager(token)
    
    try:
        await auth_manager.get_valid_token()
        user_info = await auth_manager.get_user_info()
        permissions = await auth_manager.check_permissions()
        
        return {
            "valid": True,
            "user_info": user_info,
            "permissions": permissions,
            "error": None
        }
    
    except Exception as e:
        return {
            "valid": False,
            "user_info": None,
            "permissions": None,
            "error": str(e)
        }


async def check_github_api_status() -> Dict[str, Any]:
    """
    Check GitHub API status and availability.
    
    Returns:
        Dictionary with API status information
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://www.githubstatus.com/api/v2/status.json")
            
            if response.status_code == 200:
                status_data = response.json()
                return {
                    "available": True,
                    "status": status_data.get("status", {}).get("description", "Unknown"),
                    "updated_at": status_data.get("page", {}).get("updated_at"),
                    "error": None
                }
            else:
                return {
                    "available": False,
                    "status": "Unknown",
                    "updated_at": None,
                    "error": f"Status API returned {response.status_code}"
                }
    
    except Exception as e:
        return {
            "available": False,
            "status": "Unknown",
            "updated_at": None,
            "error": str(e)
        }