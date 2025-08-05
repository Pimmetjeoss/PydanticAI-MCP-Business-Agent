"""
OAuth authentication CLI commands for MCP Business Agent.
Provides login, logout, and status commands for managing OAuth sessions.
"""

import asyncio
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.status import Status
from datetime import datetime
from typing import Optional

from .oauth_manager import oauth_manager
from .settings import settings

console = Console()


@click.group()
def auth():
    """OAuth authentication management commands."""
    pass


@auth.command()  
@click.option('--force', is_flag=True, help='Force new login even if session exists')
def login(force: bool):
    """
    Authenticate with MCP server using GitHub OAuth.
    
    Opens browser for GitHub OAuth flow and saves session cookies.
    """
    async def do_login():
        console.print("🔐 [bold blue]MCP Server Authentication[/bold blue]")
        console.print(f"Server: {settings.mcp_server_url}")
        
        if not force:
            # Check existing session
            session_info = oauth_manager.get_session_info()
            if session_info and session_info["has_session"]:
                console.print("✅ Existing session found. Use --force to create new session.")
                return
        
        if force:
            console.print("🔄 Clearing existing session...")
            oauth_manager.clear_session_cookies()
        
        with Status("Starting OAuth flow...", spinner="dots"):
            try:
                success = oauth_manager.start_oauth_flow()
                
                if success:
                    console.print(Panel.fit(
                        "✅ [bold green]Authentication Successful![/bold green]\n"
                        "Session cookies saved. You can now use the MCP agent.",
                        title="Success"
                    ))
                else:
                    console.print(Panel.fit(
                        "❌ [bold red]Authentication Failed[/bold red]\n"
                        "OAuth flow was not completed successfully.",
                        title="Error"
                    ))
                    
            except Exception as e:
                console.print(Panel.fit(
                    f"❌ [bold red]Authentication Error[/bold red]\n"
                    f"Error: {str(e)}",
                    title="Error"
                ))
    
    asyncio.run(do_login())


@auth.command()
def logout():
    """
    Clear saved OAuth session cookies.
    
    Removes stored session data, requiring new login for next use.
    """
    console.print("🔓 [bold blue]Clearing OAuth Session[/bold blue]")
    
    session_info = oauth_manager.get_session_info()
    if not session_info or not session_info["has_session"]:
        console.print("ℹ️  No active session found.")
        return
    
    try:
        oauth_manager.clear_session_cookies()
        console.print("✅ Session cleared successfully.")
    except Exception as e:
        console.print(f"❌ Error clearing session: {str(e)}")


@auth.command()
def status():
    """
    Show current OAuth authentication status.
    
    Displays session information and validates current authentication.
    """
    async def do_status():
        console.print("🔍 [bold blue]OAuth Authentication Status[/bold blue]")
        
        # Create status table
        table = Table(title="Session Information")
        table.add_column("Property", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")
        
        # Get session info
        session_info = oauth_manager.get_session_info()
        
        if session_info and session_info["has_session"]:
            table.add_row("Status", "✅ Active Session")
            
            # Format timestamp
            if session_info["timestamp"]:
                timestamp = datetime.fromtimestamp(session_info["timestamp"])
                table.add_row("Created", timestamp.strftime("%Y-%m-%d %H:%M:%S"))
            
            table.add_row("MCP Server", session_info.get("mcp_server_url", "Unknown"))
            table.add_row("Cookies", str(session_info.get("cookies_count", 0)))
            
            # Test session validity
            console.print(table)
            
            with Status("Validating session...", spinner="dots"):
                cookies = oauth_manager.load_session_cookies()
                if cookies:
                    is_valid = await oauth_manager.validate_session(cookies)
                    if is_valid:
                        console.print("✅ Session is valid and active")
                    else:
                        console.print("⚠️  Session appears to be expired or invalid")
                        console.print("   Run 'auth login --force' to refresh")
                else:
                    console.print("❌ Could not load session cookies")
        else:
            table.add_row("Status", "❌ No Active Session")
            table.add_row("MCP Server", settings.mcp_server_url)
            console.print(table)
            console.print("\n💡 Run 'auth login' to authenticate")
    
    asyncio.run(do_status())


@auth.command()
@click.option('--show-cookies', is_flag=True, help='Show cookie details (sensitive)')
def debug(show_cookies: bool):
    """
    Debug OAuth session with detailed information.
    
    Shows detailed session information for troubleshooting.
    """
    console.print("🔧 [bold blue]OAuth Debug Information[/bold blue]")
    
    session_info = oauth_manager.get_session_info()
    
    # Basic info table
    table = Table(title="Debug Information")
    table.add_column("Property", style="cyan", no_wrap=True)  
    table.add_column("Value", style="white")
    
    # Settings info
    table.add_row("MCP Server URL", settings.mcp_server_url)
    table.add_row("Cookie File", str(oauth_manager.cookie_file_path))
    table.add_row("File Exists", str(oauth_manager.cookie_file_path.exists()))
    table.add_row("Callback Port", str(oauth_manager.callback_port))
    table.add_row("Redirect URI", oauth_manager.redirect_uri)
    
    if session_info and session_info["has_session"]:
        table.add_row("Session Loaded", "✅ Yes")
        table.add_row("Timestamp", str(session_info.get("timestamp")))
        table.add_row("Cookie Count", str(session_info.get("cookies_count", 0)))
        
        if show_cookies:
            cookies = oauth_manager.load_session_cookies()
            if cookies:
                console.print(table)
                console.print("\n🍪 [bold yellow]Cookie Details (Sensitive!):[/bold yellow]")
                cookie_table = Table()
                cookie_table.add_column("Name", style="cyan")
                cookie_table.add_column("Value", style="yellow")
                
                for name, value in cookies.items():
                    # Truncate long values for display
                    display_value = value[:50] + "..." if len(value) > 50 else value
                    cookie_table.add_row(name, display_value)
                
                console.print(cookie_table)
            else:
                table.add_row("Cookie Load", "❌ Failed")
    else:
        table.add_row("Session Loaded", "❌ No")
    
    console.print(table)


if __name__ == "__main__":
    auth()