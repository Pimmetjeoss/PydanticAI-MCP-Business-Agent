"""
OAuth flow manager for browser-based GitHub authentication with MCP server.
Handles OAuth redirect, cookie extraction, and session management.
"""

import json
import time
import uuid
import asyncio
import webbrowser
import urllib.parse
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, Dict, Any
from threading import Thread
import logging

import httpx
from cryptography.fernet import Fernet
try:
    from .settings import settings
except ImportError:
    # Handle relative import issues during testing
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    from settings import settings

logger = logging.getLogger(__name__)


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback from GitHub."""
    
    def __init__(self, oauth_manager, *args, **kwargs):
        self.oauth_manager = oauth_manager
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle OAuth callback GET request."""
        try:
            logger.info(f"OAuth callback received: {self.path}")
            
            # Parse callback URL
            parsed_url = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            
            if 'code' in query_params:
                # Success - got authorization code
                auth_code = query_params['code'][0]
                logger.info(f"OAuth authorization code received: {auth_code[:10]}...")
                self.oauth_manager.auth_code = auth_code
                
                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                success_html = """
                <html>
                <head><title>OAuth Success</title></head>
                <body>
                <h2>✅ Authentication Successful!</h2>
                <p>You can now close this window and return to the application.</p>
                <script>setTimeout(() => window.close(), 3000);</script>
                </body>
                </html>
                """
                self.wfile.write(success_html.encode())
                
            elif 'error' in query_params:
                # Error in OAuth flow
                error = query_params['error'][0]
                error_description = query_params.get('error_description', ['Unknown error'])[0]
                logger.error(f"OAuth error received: {error} - {error_description}")
                
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                error_html = f"""
                <html>
                <head><title>OAuth Error</title></head>
                <body>
                <h2>❌ Authentication Failed</h2>
                <p><strong>Error:</strong> {error}</p>
                <p><strong>Description:</strong> {error_description}</p>
                </body>
                </html>
                """
                self.wfile.write(error_html.encode())
                
        except Exception as e:
            logger.error(f"OAuth callback error: {e}")
            self.send_response(500)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Log HTTP server messages."""
        logger.info("OAuth Server: " + format % args)


class OAuthManager:
    """
    Manages OAuth flow with GitHub for MCP server authentication.
    Handles browser launch, callback server, and cookie management.
    """
    
    def __init__(self):
        self.callback_port = 8796
        self.redirect_uri = f"http://localhost:{self.callback_port}/callback"
        self.auth_code: Optional[str] = None
        self.session_data: Optional[Dict[str, Any]] = None
        self.cookie_file_path = Path.home() / ".mcp_business_agent" / "session_cookies.json"
        self.encryption_key = self._get_or_create_encryption_key()
        
        # Create directory if it doesn't exist
        self.cookie_file_path.parent.mkdir(exist_ok=True)
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for cookie storage."""
        key_file = Path.home() / ".mcp_business_agent" / "encryption.key"
        key_file.parent.mkdir(exist_ok=True)
        
        if key_file.exists():
            return key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            return key
    
    def _encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data for storage."""
        fernet = Fernet(self.encryption_key)
        return fernet.encrypt(data.encode()).decode()
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt stored sensitive data."""
        fernet = Fernet(self.encryption_key)
        return fernet.decrypt(encrypted_data.encode()).decode()
    
    def save_session_cookies(self, cookies: Dict[str, str]) -> None:
        """Save session cookies to encrypted storage."""
        try:
            session_data = {
                "cookies": cookies,
                "timestamp": time.time(),
                "mcp_server_url": settings.mcp_server_url,
                "user_agent": "MCP-Business-Agent/1.0"
            }
            
            # Encrypt the session data
            encrypted_data = self._encrypt_data(json.dumps(session_data))
            
            # Save to file
            with open(self.cookie_file_path, 'w') as f:
                json.dump({"session": encrypted_data}, f)
            
            self.session_data = session_data
            logger.info("Session cookies saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save session cookies: {e}")
            raise
    
    def load_session_cookies(self) -> Optional[Dict[str, str]]:
        """Load session cookies from encrypted storage."""
        try:
            if not self.cookie_file_path.exists():
                return None
            
            with open(self.cookie_file_path, 'r') as f:
                data = json.load(f)
            
            if "session" not in data:
                return None
            
            # Decrypt session data
            decrypted_data = self._decrypt_data(data["session"])
            session_data = json.loads(decrypted_data)
            
            # Check if session is still valid (24 hours)
            if time.time() - session_data["timestamp"] > 86400:
                logger.info("Session cookies expired")
                return None
            
            # Verify MCP server URL matches
            if session_data.get("mcp_server_url") != settings.mcp_server_url:
                logger.info("MCP server URL changed, invalidating session")
                return None
            
            self.session_data = session_data
            return session_data["cookies"]
            
        except Exception as e:
            logger.error(f"Failed to load session cookies: {e}")
            return None
    
    def clear_session_cookies(self) -> None:
        """Clear stored session cookies."""
        try:
            if self.cookie_file_path.exists():
                self.cookie_file_path.unlink()
            self.session_data = None
            logger.info("Session cookies cleared")
        except Exception as e:
            logger.error(f"Failed to clear session cookies: {e}")
    
    async def validate_session(self, cookies: Dict[str, str]) -> bool:
        """Validate session cookies with MCP server."""
        try:
            async with httpx.AsyncClient(
                cookies=cookies,
                timeout=10.0,
                follow_redirects=False
            ) as client:
                # Validate against SSE endpoint
                base_server_url = settings.mcp_server_url.rstrip('/').replace('/mcp', '')
                response = await client.get(f"{base_server_url}/sse")
                
                # Check if we get redirected to login (indicates invalid session)
                if response.status_code == 302 and 'login' in response.headers.get('location', ''):
                    return False
                
                # 401 means invalid session
                if response.status_code == 401:
                    return False
                
                # Any other response likely means valid session
                return True
                
        except Exception as e:
            logger.error(f"Session validation failed: {e}")
            return False
    
    def start_oauth_flow(self) -> bool:
        """
        Start the OAuth flow by opening browser and starting callback server.
        
        Returns:
            True if OAuth flow completed successfully, False otherwise
        """
        try:
            # Generate state parameter for security
            state = str(uuid.uuid4())
            
            # Get MCP server base URL
            base_server_url = settings.mcp_server_url.replace('/mcp', '').replace('/sse', '')
            
            # Construct MCP server OAuth URL - this will handle GitHub OAuth internally
            # The MCP server will redirect to GitHub, then handle the callback
            oauth_url = (
                f"{base_server_url}/authorize"
                f"?client_id=98yTBHdCIvw75gcJ"  # Local server registered client ID
                f"&redirect_uri={urllib.parse.quote(self.redirect_uri)}"
                f"&state={state}"
                f"&response_type=code"
                f"&scope=read"  # Basic MCP access scope
            )
            
            logger.info(f"Starting OAuth flow...")
            logger.info(f"OAuth URL: {oauth_url}")
            
            # Start callback server
            server = HTTPServer(
                ('localhost', self.callback_port),
                lambda *args, **kwargs: OAuthCallbackHandler(self, *args, **kwargs)
            )
            
            # Start server in separate thread
            server_thread = Thread(target=server.serve_forever, daemon=True)
            server_thread.start()
            
            # Give server time to start
            time.sleep(1)
            logger.info(f"OAuth callback server started on http://localhost:{self.callback_port}")
            
            try:
                # Open browser
                logger.info("Opening browser for OAuth...")
                webbrowser.open(oauth_url)
                
                # Wait for OAuth callback (max 300 seconds)
                timeout = 300
                start_time = time.time()
                
                while self.auth_code is None and (time.time() - start_time) < timeout:
                    time.sleep(1)
                
                if self.auth_code is None:
                    logger.error("OAuth flow timed out")
                    return False
                
                logger.info("OAuth authorization code received")
                
                # Now we need to extract cookies from the MCP server
                # The auth code indicates successful GitHub OAuth, but we need
                # to make a request to the MCP server to get session cookies
                cookies = self._extract_session_cookies()
                
                if cookies:
                    self.save_session_cookies(cookies)
                    return True
                else:
                    logger.error("Failed to extract session cookies")
                    return False
                
            finally:
                server.shutdown()
                server.server_close()
                
        except Exception as e:
            logger.error(f"OAuth flow failed: {e}")
            return False
    
    def _extract_session_cookies(self) -> Optional[Dict[str, str]]:
        """
        Extract session cookies from successful OAuth authentication using proper MCP OAuth flow.
        Uses the MCP server's OAuth discovery configuration for correct authentication.
        """
        if not self.auth_code:
            logger.warning("No authorization code available for token exchange")
            return None

        import requests
        base_server_url = settings.mcp_server_url.replace('/mcp', '').replace('/sse', '')
        
        try:
            # First, get the OAuth discovery configuration from the MCP server
            discovery_url = f"{base_server_url}/.well-known/oauth-authorization-server"
            logger.info(f"Getting OAuth configuration from: {discovery_url}")
            
            discovery_response = requests.get(discovery_url, timeout=10)
            if discovery_response.status_code != 200:
                logger.error(f"Failed to get OAuth discovery: {discovery_response.status_code}")
                return None
                
            oauth_config = discovery_response.json()
            token_endpoint = oauth_config.get('token_endpoint')
            
            if not token_endpoint:
                logger.error("No token endpoint found in OAuth discovery")
                return None
                
            logger.info(f"Using token endpoint: {token_endpoint}")
            
            # Perform proper OAuth 2.0 authorization code exchange
            token_data = {
                'grant_type': 'authorization_code',
                'code': self.auth_code,
                'redirect_uri': self.redirect_uri,
                'client_id': '98yTBHdCIvw75gcJ',  # Local server registered client ID
                'client_secret': 'vxwVk1YYg4dyKTpaB05bmyMibbDZjFV6',  # Local server client secret
            }
            
            # Use form-encoded data as per OAuth 2.0 spec
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            
            logger.info("Exchanging authorization code for access token")
            response = requests.post(
                token_endpoint,
                data=token_data,
                headers=headers,
                timeout=15
            )
            
            logger.info(f"Token endpoint response: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                # Success! Parse the OAuth token response
                try:
                    token_result = response.json()
                    logger.info(f"OAuth token exchange successful")
                    logger.debug(f"Token response keys: {list(token_result.keys())}")
                    
                    # Extract the access token
                    access_token = token_result.get('access_token')
                    if access_token:
                        logger.info("✅ Successfully obtained MCP access token")
                        # Return as a Bearer token for Authorization header
                        return {'mcp_access_token': access_token}
                    else:
                        logger.error("No access_token in response")
                        return None
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse token response: {e}")
                    logger.debug(f"Raw response: {response.text}")
                    return None
            
            elif response.status_code == 400:
                # Bad request - likely invalid code or client credentials
                try:
                    error_info = response.json()
                    error_desc = error_info.get('error_description', error_info.get('error', 'Unknown error'))
                    logger.error(f"OAuth token exchange failed: {error_desc}")
                except:
                    logger.error(f"OAuth token exchange failed: {response.text}")
                return None
                
            elif response.status_code == 401:
                logger.error("OAuth client authentication failed - check client credentials")
                return None
                
            else:
                logger.error(f"Unexpected token endpoint response: {response.status_code} - {response.text}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Network error during OAuth token exchange: {e}")
            return None
        
        except Exception as e:
            logger.error(f"Unexpected error during OAuth flow: {e}")
            return None
    
    def _exchange_code_for_token(self) -> Optional[str]:
        """Exchange GitHub authorization code for access token."""
        try:
            import requests
            
            # GitHub token exchange endpoint
            token_url = "https://github.com/login/oauth/access_token"
            
            # Your MCP server's GitHub OAuth app credentials
            github_client_id = "Ov23liYZYMWR0AEExM9z"
            github_client_secret = "bb49b3cca8bc70e98bcd641e07e721dd6264ebe8"
            
            # Exchange code for token
            response = requests.post(
                token_url,
                data={
                    'client_id': github_client_id,
                    'client_secret': github_client_secret,
                    'code': self.auth_code,
                    'redirect_uri': self.redirect_uri
                },
                headers={'Accept': 'application/json'}
            )
            
            logger.info(f"GitHub token exchange response: {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get('access_token')
                
                if access_token:
                    logger.info("Successfully obtained GitHub access token")
                    return access_token
                else:
                    logger.error(f"No access token in response: {token_data}")
                    return None
            else:
                logger.error(f"GitHub token exchange failed: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to exchange code for token: {e}")
            return None
    
    async def get_valid_session_cookies(self) -> Optional[Dict[str, str]]:
        """
        Get valid session cookies, initiating OAuth flow if necessary.
        
        Returns:
            Dictionary of valid session cookies, or None if authentication failed
        """
        # Try to load existing cookies
        cookies = self.load_session_cookies()
        
        if cookies:
            # Validate existing session
            if await self.validate_session(cookies):
                logger.info("Using existing valid session")
                return cookies
            else:
                logger.info("Existing session invalid, clearing")
                self.clear_session_cookies()
        
        # Need to do OAuth flow
        logger.info("Starting new OAuth authentication flow")
        print("\n🔐 Authentication Required")
        print("Opening browser for GitHub OAuth...")
        print("Please complete the authentication in your browser.")
        print("This window will wait for you to complete the process.\n")
        
        if self.start_oauth_flow():
            # Return the newly saved cookies
            return self.load_session_cookies()
        else:
            logger.error("OAuth flow failed")
            return None
    
    def get_session_info(self) -> Optional[Dict[str, Any]]:
        """Get information about current session."""
        if not self.session_data:
            cookies = self.load_session_cookies()
            if not cookies:
                return None
        
        return {
            "has_session": self.session_data is not None,
            "timestamp": self.session_data.get("timestamp") if self.session_data else None,
            "mcp_server_url": self.session_data.get("mcp_server_url") if self.session_data else None,
            "cookies_count": len(self.session_data.get("cookies", {})) if self.session_data else 0
        }


# Global OAuth manager instance
oauth_manager = OAuthManager()