"""
Interactive CLI interface for MCP Business Automation Agent.
Provides a rich conversational interface with command help and debugging features.
"""

import asyncio
import click
import sys
import logging
from typing import Optional
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.live import Live
from rich.status import Status
from rich.table import Table

from .agent import business_agent
from .dependencies import get_mcp_dependencies, mcp_context
from .settings import settings
from .providers import validate_llm_configuration, get_model_info
from .auth_manager import validate_github_token
from .models import UserPermissions
from .auth_cli import auth

console = Console()
logger = logging.getLogger(__name__)


class CLIAgent:
    """CLI wrapper for the MCP Business Automation Agent"""
    
    def __init__(self, debug: bool = False, user_id: str = "cli_user"):
        self.debug = debug
        self.user_id = user_id
        self.session_id = None
        self.message_count = 0
        self.conversation_history = []
        
        if debug:
            logging.basicConfig(level=logging.DEBUG)
    
    async def start_session(self):
        """Initialize agent session and validate configuration"""
        console.print(Panel.fit(
            "[bold green]🤖 MCP Business Automation Agent[/bold green]\n"
            "Intelligent business workflows with database, email, and web research capabilities",
            title="Welcome"
        ))
        
        # Validate configuration
        with Status("Validating configuration...", console=console) as status:
            try:
                # Check LLM configuration
                llm_config = validate_llm_configuration()
                if not llm_config["overall_valid"]:
                    console.print("❌ LLM configuration invalid:")
                    for error in llm_config.get('errors', []):
                        console.print(f"   • {error}")
                    console.print("\n💡 Please check your .env file and ensure LLM_API_KEY is set correctly.")
                    return False
                
                # Check GitHub token (direct token validation)
                github_validation = await validate_github_token(settings.github_access_token)
                if not github_validation["valid"]:
                    console.print(f"❌ GitHub token invalid: {github_validation['error']}")
                    console.print("\n💡 Please check your GITHUB_ACCESS_TOKEN in the .env file.")
                    console.print("   • Make sure the token starts with 'ghp_'")
                    console.print("   • Ensure it has 'repo' and 'user:email' scopes")
                    return False
                
                # Check MCP dependencies (optional - don't fail if MCP server is down)
                try:
                    from .dependencies import validate_dependencies
                    deps_validation = await validate_dependencies()
                    if not deps_validation["overall"]:
                        console.print("⚠️  MCP server connection issues detected")
                        console.print("   This may affect some advanced features")
                        if self.debug:
                            console.print(f"   Details: {deps_validation}")
                except Exception as e:
                    console.print(f"⚠️  Could not validate MCP connectivity: {e}")
                    console.print("   Basic GitHub functionality should still work")
                
                status.update("Configuration validated ✅")
                
            except Exception as e:
                console.print(f"❌ Configuration validation failed: {e}")
                console.print("\n💡 Common fixes:")
                console.print("   • Ensure your .env file exists in the mcp_business_agent directory")
                console.print("   • Check that all required environment variables are set")
                console.print("   • Run 'python -m mcp_business_agent validate' for detailed diagnostics")
                return False
        
        # Display system info
        if self.debug:
            self.show_system_info()
        
        return True
    
    def show_system_info(self):
        """Display system configuration information"""
        model_info = get_model_info()
        
        table = Table(title="System Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("LLM Provider", model_info["llm_provider"])
        table.add_row("LLM Model", model_info["llm_model"])
        table.add_row("MCP Server", model_info["mcp_server_url"])
        table.add_row("Anthropic Fallback", "✅" if model_info["anthropic_fallback"] else "❌")
        table.add_row("Debug Mode", "✅" if model_info["debug"] else "❌")
        table.add_row("Environment", model_info["app_env"])
        
        console.print(table)
        console.print()
    
    def show_help(self):
        """Display help information"""
        help_content = """
# 🤖 MCP Business Automation Agent Commands

## Core Capabilities

### 📊 Database Operations
- `list tables` - Show all database tables and schemas
- `query [SQL]` - Execute SELECT queries (e.g., "query SELECT * FROM sales")  
- `analyze sales data` - Get insights from sales performance
- `generate quarterly report` - Create comprehensive business reports

### 📧 Email & Communication
- `send email to [address]` - Send professional emails and notifications
- `email the team about [topic]` - Draft and send team communications
- `notify executives about [update]` - Send executive summaries

### 🔍 Research & Intelligence  
- `search for [topic]` - Web search with content extraction
- `scrape [URL]` - Extract content from web pages
- `research competitors` - Gather competitive intelligence
- `find industry trends` - Market research and analysis

### 🧠 Strategic Thinking
- `help me think through [problem]` - Structured problem analysis
- `analyze the situation with [context]` - Strategic decision support  
- `what are the options for [scenario]` - Alternative exploration

### ⚙️ Workflow Automation
- `run quarterly analysis` - Execute predefined business workflows
- `execute competitive research` - Multi-step research automation
- `automate [process description]` - Custom workflow creation

## Special Commands
- `help` - Show this help message
- `status` - Show agent and system status
- `debug on/off` - Toggle debug mode
- `clear` - Clear conversation history
- `exit` - Exit the agent

## Example Conversations
- "Analyze our Q4 sales performance and email a summary to the leadership team"
- "Research our top 3 competitors' pricing strategies and update our competitive analysis database"  
- "Help me think through whether we should expand into the European market"
- "Query the customer database to find our highest value clients this quarter"

The agent can chain multiple operations together and maintain context across complex multi-step workflows.
"""
        console.print(Markdown(help_content))
    
    def show_status(self):
        """Display current agent status"""
        table = Table(title="Agent Status")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Session Active", "✅")
        table.add_row("User ID", self.user_id)
        table.add_row("Messages", str(self.message_count))
        table.add_row("Debug Mode", "✅" if self.debug else "❌")
        
        console.print(table)
    
    async def run_conversation(self):
        """Main conversation loop"""
        if not await self.start_session():
            return
        
        console.print("\n💬 Ready for conversation! Type 'help' for commands or 'exit' to quit.\n")
        
        try:
            async with mcp_context(user_id=self.user_id) as deps:
                while True:
                    try:
                        # Get user input
                        user_input = Prompt.ask(
                            "[bold blue]You[/bold blue]",
                            console=console
                        ).strip()
                        
                        if not user_input:
                            continue
                        
                        # Handle special commands
                        if user_input.lower() == 'exit':
                            console.print("👋 Goodbye!")
                            break
                        elif user_input.lower() == 'help':
                            self.show_help()
                            continue
                        elif user_input.lower() == 'status':
                            self.show_status()
                            continue
                        elif user_input.lower() == 'clear':
                            self.conversation_history.clear()
                            self.message_count = 0
                            console.clear()
                            console.print("🧹 Conversation history cleared!")
                            continue
                        elif user_input.lower() == 'debug on':
                            self.debug = True
                            console.print("🐛 Debug mode enabled")
                            continue
                        elif user_input.lower() == 'debug off':
                            self.debug = False
                            console.print("🔇 Debug mode disabled")
                            continue
                        
                        # Process with agent
                        with Status("🤖 Thinking...", console=console) as status:
                            try:
                                result = await business_agent.run(user_input, deps=deps)
                                response = result.data
                                
                                # Track conversation
                                self.conversation_history.append({
                                    "user": user_input,
                                    "agent": response,
                                    "timestamp": deps.session.last_activity if deps.session else None
                                })
                                self.message_count += 1
                                
                            except Exception as e:
                                logger.error(f"Agent execution error: {e}")
                                response = f"❌ I encountered an error: {str(e)}"
                        
                        # Display response
                        console.print(f"\n[bold green]🤖 Agent[/bold green]: {response}\n")
                        
                        # Show debug info if enabled
                        if self.debug and hasattr(result, 'usage'):
                            usage = result.usage()
                            if usage:
                                console.print(f"[dim]💰 Tokens: {usage}[/dim]")
                    
                    except KeyboardInterrupt:
                        console.print("\n👋 Conversation interrupted. Type 'exit' to quit or continue chatting.")
                        continue
                    except Exception as e:
                        console.print(f"\n❌ Unexpected error: {str(e)}")
                        if self.debug:
                            import traceback
                            console.print(f"[dim]{traceback.format_exc()}[/dim]")
                        
        except Exception as e:
            console.print(f"❌ Session error: {str(e)}")
            if self.debug:
                import traceback
                console.print(f"[dim]{traceback.format_exc()}[/dim]")


@click.group()
@click.option('--debug', is_flag=True, help='Enable debug mode with detailed logging')
@click.pass_context
def cli(ctx, debug: bool):
    """
    MCP Business Automation Agent - CLI Interface
    
    A sophisticated AI agent for business automation with database analysis,
    email communication, web research, and strategic thinking capabilities.
    """
    ctx.ensure_object(dict)
    ctx.obj['debug'] = debug
    
    if debug:
        logging.basicConfig(level=logging.DEBUG)


# Add auth sub-commands
cli.add_command(auth)


@cli.command()
@click.option('--user-id', default='cli_user', help='User identifier for the session')
@click.pass_context
def chat(ctx, user_id: str):
    """Start interactive chat session with the agent."""
    debug = ctx.obj.get('debug', False)
    _run_chat_session(debug, user_id)


@cli.command()
@click.option('--user-id', default='cli_user', help='User identifier for the session')
@click.pass_context
def validate(ctx, user_id: str):
    """Validate configuration and dependencies."""
    debug = ctx.obj.get('debug', False)
    _validate_configuration(debug, user_id)


@cli.command()
@click.option('--user-id', default='cli_user', help='User identifier for the session')
@click.pass_context
def status(ctx, user_id: str):
    """Show system status information."""
    debug = ctx.obj.get('debug', False)
    _show_system_status(debug, user_id)


def _run_chat_session(debug: bool, user_id: str):
    """Run the main chat session."""
    async def run():
        cli_agent = CLIAgent(debug=debug, user_id=user_id)
        session_started = await cli_agent.start_session()
        if session_started:
            await cli_agent.run_conversation()
        else:
            console.print("❌ Could not start session due to configuration issues.")
            console.print("💡 Run 'python -m mcp_business_agent validate' to check your configuration.")
    
    asyncio.run(run())


def _validate_configuration(debug: bool, user_id: str):
    """Validate configuration and exit."""
    async def validate():
        console.print("🔍 Validating Configuration...")
        
        # Check LLM config
        llm_config = validate_llm_configuration()
        if llm_config["overall_valid"]:
            console.print("✅ LLM Configuration: Valid")
        else:
            console.print("❌ LLM Configuration: Invalid")
            for error in llm_config.get("errors", []):
                console.print(f"   - {error}")
        
        # Check GitHub token
        try:
            token_valid = await validate_github_token(settings.github_access_token)
            if token_valid:
                console.print("✅ GitHub Token: Valid")
            else:
                console.print("❌ GitHub Token: Invalid")
        except Exception as e:
            console.print(f"❌ GitHub Token: Error - {e}")
        
        console.print("Validation complete.")
    
    asyncio.run(validate())


def _show_system_status(debug: bool, user_id: str):
    """Show system status and exit."""
    cli_agent = CLIAgent(debug=debug, user_id=user_id)
    console.print("🔍 System Status Check")
    cli_agent.show_system_info()


def main(debug: bool = False, user_id: str = 'cli_user', validate_only: bool = False, status: bool = False):
    """
    MCP Business Automation Agent - Interactive CLI
    
    A sophisticated AI agent for business automation with database analysis,
    email communication, web research, and strategic thinking capabilities.
    """
    
    if status:
        # Show status and exit
        cli_agent = CLIAgent(debug=debug, user_id=user_id)
        console.print("🔍 System Status Check")
        cli_agent.show_system_info()
        return
    
    if validate_only:
        # Validate configuration and exit
        async def validate():
            console.print("🔍 Validating Configuration...")
            
            # Check LLM config
            llm_config = validate_llm_configuration()
            if llm_config["overall_valid"]:
                console.print("✅ LLM Configuration: Valid")
            else:
                console.print(f"❌ LLM Configuration: {llm_config['errors']}")
            
            # Check GitHub token
            try:
                github_validation = await validate_github_token(settings.github_access_token)
                if github_validation["valid"]:
                    console.print("✅ GitHub Token: Valid")
                    user_info = github_validation.get("user_info", {})
                    if user_info and user_info.get("login"):
                        console.print(f"   • User: {user_info['login']}")
                else:
                    console.print(f"❌ GitHub Token: {github_validation['error']}")
                    console.print("   • Make sure token starts with 'ghp_'")
                    console.print("   • Ensure it has 'repo' and 'user:email' scopes")
            except Exception as e:
                console.print(f"❌ GitHub Token: {e}")
            
            # Check MCP connectivity (basic)
            try:
                from .dependencies import validate_dependencies
                deps_valid = await validate_dependencies()
                if deps_valid["overall"]:
                    console.print("✅ MCP Dependencies: Valid")
                else:
                    console.print("❌ MCP Dependencies: Issues detected")
            except Exception as e:
                console.print(f"❌ MCP Dependencies: {e}")
        
        asyncio.run(validate())
        return
    
    # Run interactive CLI
    cli_agent = CLIAgent(debug=debug, user_id=user_id)
    
    try:
        asyncio.run(cli_agent.run_conversation())
    except KeyboardInterrupt:
        console.print("\n👋 Agent session terminated.")
    except Exception as e:
        console.print(f"\n❌ Fatal error: {str(e)}")
        if debug:
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


def main():
    """Entry point for backwards compatibility."""
    cli()


if __name__ == "__main__":
    main()