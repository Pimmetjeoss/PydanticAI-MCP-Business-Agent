"""
Main Business Automation Agent with comprehensive MCP tool integration.
Provides conversational interface for database, email, web research, and strategic thinking.
"""

import logging
import re
from typing import Optional, List, Dict, Any
from pydantic_ai import Agent, RunContext

from .providers import get_llm_model
from .dependencies import MCPAgentDependencies
from .workflow_manager import WorkflowManager
from .models import (
    DatabaseQueryParams, EmailParams, WebScrapingParams, 
    WebSearchParams, ThinkingParams
)

logger = logging.getLogger(__name__)

# Create agent with fallback model support
business_agent = Agent(
    get_llm_model(),  # Uses fallback model from providers.py
    deps_type=MCPAgentDependencies,
    system_prompt="""
You are a Business Automation & Research Agent with access to powerful enterprise tools through an MCP server. Your role is to help users with sophisticated business workflows and analysis.

## Your Capabilities:

### 🗄️ Data Analysis & Insights
Use database tools to query business data, identify trends, generate reports, and provide actionable insights. Always validate SQL queries and present results clearly with business context.

### 📧 Communication & Reporting
Craft professional emails, reports, and summaries. Use appropriate tone and formatting. Always confirm email recipients and content before sending.

### 🔍 Research & Intelligence
Leverage web scraping and search tools to gather competitive intelligence, market research, and industry insights. Verify information from multiple sources and provide citations.

### 🧠 Strategic Decision Support
Guide users through complex problem-solving using structured thinking tools. Break down problems, explore alternatives, and provide reasoned recommendations with clear reasoning chains.

### ⚙️ Workflow Automation
Chain multiple tools together to create efficient workflows. Examples:
- Analyze data → Generate insights → Create report → Email stakeholders
- Research competitors → Scrape pricing → Analyze strategy → Update database
- Monitor trends → Identify opportunities → Draft recommendations → Schedule follow-ups

## Key Operating Principles:

### Security & Permissions
- Always prioritize data security and respect user permissions
- Confirm destructive database operations before execution
- Validate email recipients and content before sending
- Never expose sensitive information in logs or responses

### Data Quality & Validation
- Validate SQL queries for syntax and security
- Cross-reference information from multiple sources
- Provide confidence levels for analysis and recommendations
- Clearly distinguish between facts and inferences

### Professional Communication
- Use clear, professional language appropriate for business context
- Structure responses with headings, bullet points, and summaries
- Provide actionable recommendations with clear next steps
- Maintain appropriate tone for the audience (executives, teams, etc.)

### Confirmation Handling
When users provide confirmations for actions (like sending emails or database operations), recognize these patterns:
- "confirm", "confirmed", "confirmation granted", "yes", "proceed", "go ahead"
- "confirm: true", "confirm=true", "confirm yes"
- Any clear affirmative response after requesting confirmation

**IMPORTANT**: When you see these confirmation patterns, immediately call the relevant tool again with the `confirm=True` parameter. Do NOT ask for additional confirmation.

Examples:
- User says "confirm: true" after email preview → Call send_email with confirm=True
- User says "yes, send it" after email preview → Call send_email with confirm=True  
- User says "confirmed" after database operation preview → Call execute_database with confirm=True

### Workflow Excellence
- Break complex tasks into clear, logical steps
- Explain your approach before proceeding with multi-step processes
- Provide progress updates for long-running operations
- Offer alternative approaches when initial methods encounter issues

### Rate Limits & Resources
- Respect website robots.txt and rate limits during scraping
- Monitor MCP server response times and adjust accordingly
- Batch operations efficiently to minimize API calls
- Provide estimates for time-intensive operations

## When handling user requests:

1. **Understand**: Clarify the business objective and success criteria
2. **Plan**: Outline your approach for complex multi-step tasks
3. **Execute**: Use appropriate tools with proper error handling
4. **Analyze**: Interpret results in business context
5. **Communicate**: Present findings clearly with actionable recommendations
6. **Follow-up**: Suggest next steps or related analyses

You excel at transforming raw data into business insights, automating routine processes, and supporting strategic decision-making through comprehensive research and analysis.
""",
    # Use string output by default (no result_type specified)
)

# =============================================================================
# DATABASE TOOLS
# =============================================================================

@business_agent.tool
async def list_tables(ctx: RunContext[MCPAgentDependencies]) -> str:
    """
    List all tables in the database with their schema information.
    Provides comprehensive overview of available data sources.
    """
    try:
        logger.info("Listing database tables")
        response = await ctx.deps.mcp_client.call_tool("listTables", {})
        
        if response.success:
            tables_data = response.data
            if isinstance(tables_data, dict) and "tables" in tables_data:
                tables = tables_data["tables"]
                formatted_output = "📊 **Database Schema Overview**\n\n"
                
                for table in tables:
                    table_name = table.get("name", "Unknown")
                    columns = table.get("columns", [])
                    row_count = table.get("row_count", "Unknown")
                    
                    formatted_output += f"**{table_name}** ({row_count} rows)\n"
                    for col in columns:
                        col_name = col.get("name", "")  
                        col_type = col.get("type", "")
                        formatted_output += f"  • {col_name} ({col_type})\n"
                    formatted_output += "\n"
                
                return formatted_output
            else:
                return f"Database tables:\n{response.data}"
        
        return f"❌ Failed to list tables: {response.error}"
        
    except Exception as e:
        logger.error(f"Error listing tables: {e}")
        return f"❌ Error accessing database: {str(e)}"


@business_agent.tool
async def query_database(
    ctx: RunContext[MCPAgentDependencies], 
    sql: str,
    max_results: int = 1000
) -> str:
    """
    Execute a read-only SQL query and return formatted results.
    
    Args:
        sql: SQL SELECT query to execute
        max_results: Maximum number of results to return (default 1000)
    """
    try:
        # Validate user permissions
        if not ctx.deps.has_permission("can_read_database"):
            return "❌ Error: You don't have permission to read from the database"
        
        # Basic SQL injection prevention
        forbidden_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "CREATE", "ALTER", "TRUNCATE"]
        sql_upper = sql.upper()
        
        if any(keyword in sql_upper for keyword in forbidden_keywords):
            return "❌ Error: Only SELECT queries are allowed for read operations"
        
        # Enforce result limits
        user_max = ctx.deps.permissions.max_query_results if ctx.deps.permissions else 1000
        actual_max = min(max_results, user_max)
        
        # Add LIMIT clause if not present
        if "LIMIT" not in sql_upper and actual_max < 10000:
            sql = f"{sql.rstrip(';')} LIMIT {actual_max}"
        
        logger.info(f"Executing database query (max results: {actual_max})")
        
        response = await ctx.deps.mcp_client.call_tool(
            "queryDatabase", 
            {"sql": sql, "max_results": actual_max}
        )
        
        if response.success:
            result_data = response.data
            
            if isinstance(result_data, dict):
                rows = result_data.get("rows", [])
                row_count = len(rows)
                execution_time = result_data.get("execution_time_ms", 0)
                
                formatted_output = f"📊 **Query Results** ({row_count} rows, {execution_time}ms)\n\n"
                
                if rows:
                    # Format as table
                    if row_count <= 10:
                        # Show full results for small datasets
                        formatted_output += "```\n"
                        if rows:
                            headers = list(rows[0].keys())
                            # Simple table formatting
                            formatted_output += " | ".join(headers) + "\n"
                            formatted_output += "-" * (len(" | ".join(headers))) + "\n"
                            
                            for row in rows:
                                values = [str(row.get(h, "")) for h in headers]
                                formatted_output += " | ".join(values) + "\n"
                        formatted_output += "```\n"
                    else:
                        # Summarize large datasets
                        formatted_output += f"Large dataset with {row_count} rows. First 5 rows:\n```\n"
                        headers = list(rows[0].keys())
                        formatted_output += " | ".join(headers) + "\n"
                        formatted_output += "-" * (len(" | ".join(headers))) + "\n"
                        
                        for i, row in enumerate(rows[:5]):
                            values = [str(row.get(h, "")) for h in headers]
                            formatted_output += " | ".join(values) + "\n"
                        
                        formatted_output += f"... and {row_count - 5} more rows\n```\n"
                else:
                    formatted_output += "No results found.\n"
                
                return formatted_output
            else:
                return f"Query results:\n{response.data}"
        
        return f"❌ Query failed: {response.error}"
        
    except Exception as e:
        logger.error(f"Database query error: {e}")
        return f"❌ Database query error: {str(e)}"


@business_agent.tool  
async def execute_database(
    ctx: RunContext[MCPAgentDependencies],
    sql: str,
    confirm: bool = False
) -> str:
    """
    Execute write operations on the database (INSERT/UPDATE/DELETE).
    
    Args:
        sql: SQL statement to execute
        confirm: Must be True to proceed with write operations
    """
    try:
        # Check user permissions
        if not ctx.deps.has_permission("can_write_database"):
            return "❌ Error: You don't have permission to modify the database"
        
        # Require explicit confirmation for write operations
        if not confirm:
            return ("⚠️ **Database Write Operation Requested**\n\n"
                   f"SQL: `{sql}`\n\n"
                   "**This will modify the database. To proceed, simply say 'confirm', 'yes', or 'proceed'.**")
        
        logger.info("Executing database write operation")
        
        response = await ctx.deps.mcp_client.call_tool(
            "executeDatabase",
            {"sql": sql}
        )
        
        if response.success:
            result = response.data
            if isinstance(result, dict):
                affected_rows = result.get("affected_rows", 0)
                execution_time = result.get("execution_time_ms", 0)
                return f"✅ **Database Updated Successfully**\n\nAffected rows: {affected_rows}\nExecution time: {execution_time}ms"
            else:
                return f"✅ Database updated successfully: {response.data}"
        
        return f"❌ Database update failed: {response.error}"
        
    except Exception as e:
        logger.error(f"Database execution error: {e}")
        return f"❌ Database execution error: {str(e)}"

# =============================================================================
# EMAIL TOOLS  
# =============================================================================

@business_agent.tool
async def send_email(
    ctx: RunContext[MCPAgentDependencies],
    to: str,
    subject: str, 
    body: str,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
    importance: str = "normal",
    html_body: Optional[str] = None,
    confirm: bool = False
) -> str:
    """
    Send an email via Microsoft Graph API.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body content (plain text)
        cc: CC recipient (optional)
        bcc: BCC recipient (optional) 
        importance: Email importance (low/normal/high)
        html_body: HTML email body (optional)
        confirm: Must be True to send the email
    """
    try:
        # Check permissions
        if not ctx.deps.has_permission("can_send_email"):
            return "❌ Error: You don't have permission to send emails"
        
        # Validate email addresses
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, to):
            return f"❌ Invalid recipient email address: {to}"
        
        if cc and not re.match(email_pattern, cc):
            return f"❌ Invalid CC email address: {cc}"
            
        if bcc and not re.match(email_pattern, bcc):
            return f"❌ Invalid BCC email address: {bcc}"
        
        # Check allowed domains if configured
        if ctx.deps.permissions and ctx.deps.permissions.allowed_email_domains:
            allowed_domains = ctx.deps.permissions.allowed_email_domains
            to_domain = f"@{to.split('@')[1]}"
            
            if not any(to_domain.endswith(domain) for domain in allowed_domains):
                return f"❌ Error: Email domain not allowed. Allowed domains: {', '.join(allowed_domains)}"
        
        # Require confirmation
        if not confirm:
            preview = f"""📧 **Email Ready to Send**

**To:** {to}
**Subject:** {subject}
**Body Preview:** {body[:200]}{'...' if len(body) > 200 else ''}
"""
            if cc:
                preview += f"**CC:** {cc}\n"
            if bcc:
                preview += f"**BCC:** {bcc}\n"
            
            preview += "\n\n**To send this email, simply say 'confirm', 'yes', or 'send it'.**"
            return preview
        
        # Build email parameters
        params = {
            "to": to,
            "subject": subject,
            "body": body,
            "importance": importance
        }
        
        if cc:
            params["cc"] = cc
        if bcc:
            params["bcc"] = bcc
        if html_body:
            params["html_body"] = html_body
        
        logger.info(f"Sending email to {to}")
        
        response = await ctx.deps.mcp_client.call_tool("sendEmail", params)
        
        if response.success:
            return f"✅ **Email Sent Successfully**\n\nRecipient: {to}\nSubject: {subject}"
        
        return f"❌ Failed to send email: {response.error}"
        
    except Exception as e:
        logger.error(f"Email error: {e}")
        return f"❌ Email error: {str(e)}"

# =============================================================================
# WEB RESEARCH TOOLS
# =============================================================================

@business_agent.tool
async def scrape_page(
    ctx: RunContext[MCPAgentDependencies],
    url: str,
    extract_links: bool = False,
    extract_images: bool = False
) -> str:
    """
    Scrape content from a single web page.
    
    Args:
        url: URL to scrape
        extract_links: Extract links from the page
        extract_images: Extract image URLs from the page
    """
    try:
        if not ctx.deps.has_permission("can_scrape_web"):
            return "❌ Error: You don't have permission to scrape web content"
        
        logger.info(f"Scraping page: {url}")
        
        params = {"url": url}
        if extract_links:
            params["extract_links"] = True
        if extract_images:
            params["extract_images"] = True
        
        response = await ctx.deps.mcp_client.call_tool("scrapePage", params)
        
        if response.success:
            data = response.data
            
            if isinstance(data, dict):
                title = data.get("title", "No title")
                content = data.get("content", "")
                links = data.get("links", [])
                images = data.get("images", [])
                
                formatted_output = f"🌐 **Page Content: {title}**\n\n"
                formatted_output += f"**URL:** {url}\n\n"
                
                if content:
                    # Truncate very long content
                    if len(content) > 2000:
                        formatted_output += f"**Content Preview:**\n{content[:2000]}...\n\n"
                    else:
                        formatted_output += f"**Content:**\n{content}\n\n"
                
                if extract_links and links:
                    formatted_output += f"**Links Found ({len(links)}):**\n"
                    for i, link in enumerate(links[:10]):  # Show first 10 links
                        formatted_output += f"{i+1}. {link}\n"
                    if len(links) > 10:
                        formatted_output += f"... and {len(links) - 10} more links\n"
                    formatted_output += "\n"
                
                if extract_images and images:
                    formatted_output += f"**Images Found ({len(images)}):**\n"
                    for i, img in enumerate(images[:5]):  # Show first 5 images
                        formatted_output += f"{i+1}. {img}\n"
                    if len(images) > 5:
                        formatted_output += f"... and {len(images) - 5} more images\n"
                
                return formatted_output
            else:
                return f"Page content from {url}:\n{response.data}"
        
        return f"❌ Failed to scrape page: {response.error}"
        
    except Exception as e:
        logger.error(f"Scraping error: {e}")
        return f"❌ Scraping error: {str(e)}"


@business_agent.tool
async def search_web(
    ctx: RunContext[MCPAgentDependencies],
    query: str,
    max_results: int = 10
) -> str:
    """
    Search the web and return relevant results with content extraction.
    
    Args:
        query: Search query
        max_results: Maximum number of results to return (1-50)
    """
    try:
        if not ctx.deps.has_permission("can_scrape_web"):
            return "❌ Error: You don't have permission to perform web searches"
        
        # Validate parameters
        max_results = min(max(max_results, 1), 50)  # Clamp between 1-50
        
        logger.info(f"Searching web for: {query}")
        
        response = await ctx.deps.mcp_client.call_tool(
            "searchWeb",
            {"query": query, "max_results": max_results}
        )
        
        if response.success:
            data = response.data
            
            if isinstance(data, dict) and "results" in data:
                results = data["results"]
                
                formatted_output = f"🔍 **Search Results for: \"{query}\"**\n\n"
                formatted_output += f"Found {len(results)} results:\n\n"
                
                for i, result in enumerate(results, 1):
                    title = result.get("title", "No title")
                    url = result.get("url", "")
                    description = result.get("description", "No description")
                    relevance = result.get("relevance_score", 0)
                    
                    formatted_output += f"**{i}. {title}**\n"
                    formatted_output += f"🔗 {url}\n"
                    formatted_output += f"📝 {description}\n"
                    if relevance:
                        formatted_output += f"📊 Relevance: {relevance:.2f}\n"
                    formatted_output += "\n"
                
                return formatted_output
            else:
                return f"Search results for '{query}':\n{response.data}"
        
        return f"❌ Search failed: {response.error}"
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return f"❌ Search error: {str(e)}"


@business_agent.tool
async def crawl_website(
    ctx: RunContext[MCPAgentDependencies],
    url: str,
    max_pages: int = 10
) -> str:
    """
    Start crawling a website and return job ID for tracking.
    
    Args:
        url: Base URL to crawl
        max_pages: Maximum number of pages to crawl (1-100)
    """
    try:
        if not ctx.deps.has_permission("can_scrape_web"):
            return "❌ Error: You don't have permission to crawl websites"
        
        # Validate parameters
        max_pages = min(max(max_pages, 1), 100)  # Clamp between 1-100
        
        logger.info(f"Starting website crawl: {url}")
        
        params = {"url": url, "max_pages": max_pages}
        
        response = await ctx.deps.mcp_client.call_tool("crawlWebsite", params)
        
        if response.success:
            data = response.data
            
            if isinstance(data, dict) and "job_id" in data:
                job_id = data["job_id"]
                
                # Store job ID in temp variables for later reference
                ctx.deps.set_temp_variable(f"crawl_job_{job_id}", {
                    "url": url,
                    "max_pages": max_pages,
                    "started_at": str(ctx.deps.session.last_activity) if ctx.deps.session else "unknown"
                })
                
                return f"🕷️ **Website Crawl Started**\n\nURL: {url}\nMax pages: {max_pages}\nJob ID: `{job_id}`\n\nUse `get_crawl_status(job_id='{job_id}')` to check progress."
            else:
                return f"Crawl started for {url}: {response.data}"
        
        return f"❌ Failed to start crawl: {response.error}"
        
    except Exception as e:
        logger.error(f"Crawl error: {e}")
        return f"❌ Crawl error: {str(e)}"


@business_agent.tool
async def get_crawl_status(
    ctx: RunContext[MCPAgentDependencies],
    job_id: str
) -> str:
    """
    Check the status of a website crawling job.
    
    Args:
        job_id: Crawling job ID from crawl_website
    """
    try:
        logger.info(f"Checking crawl status: {job_id}")
        
        response = await ctx.deps.mcp_client.call_tool(
            "getCrawlStatus",
            {"job_id": job_id}
        )
        
        if response.success:
            data = response.data
            
            if isinstance(data, dict):
                status = data.get("status", "unknown")
                progress = data.get("progress", 0)
                pages_crawled = data.get("pages_crawled", 0)
                results = data.get("results", [])
                
                formatted_output = f"🕷️ **Crawl Status: {job_id}**\n\n"
                formatted_output += f"**Status:** {status.title()}\n"
                formatted_output += f"**Progress:** {progress}%\n"
                formatted_output += f"**Pages Crawled:** {pages_crawled}\n\n"
                
                if status == "completed" and results:
                    formatted_output += f"**Results Summary:**\n"
                    formatted_output += f"Found {len(results)} pages:\n\n"
                    
                    for i, result in enumerate(results[:10], 1):  # Show first 10 results
                        title = result.get("title", "No title")
                        url = result.get("url", "")
                        content_length = len(result.get("content", ""))
                        
                        formatted_output += f"{i}. **{title}**\n"
                        formatted_output += f"   🔗 {url}\n"
                        formatted_output += f"   📄 {content_length:,} characters\n\n"
                    
                    if len(results) > 10:
                        formatted_output += f"... and {len(results) - 10} more pages\n"
                
                elif status == "in_progress":
                    formatted_output += "Crawling in progress. Check again in a few moments.\n"
                
                elif status == "failed":
                    error = data.get("error", "Unknown error")
                    formatted_output += f"**Error:** {error}\n"
                
                return formatted_output
            else:
                return f"Crawl status for {job_id}: {response.data}"
        
        return f"❌ Failed to get crawl status: {response.error}"
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return f"❌ Status check error: {str(e)}"

# =============================================================================
# STRATEGIC THINKING TOOLS
# =============================================================================

@business_agent.tool
async def start_thinking(
    ctx: RunContext[MCPAgentDependencies],
    problem: str,
    context: Optional[str] = None
) -> str:
    """
    Initialize a structured thinking session for complex problem solving.
    
    Args:
        problem: Problem or question to analyze
        context: Additional context for the analysis
    """
    try:
        logger.info(f"Starting thinking session for: {problem[:100]}...")
        
        params = {"problem": problem}
        if context:
            params["context"] = context
        
        response = await ctx.deps.mcp_client.call_tool("startThinking", params)
        
        if response.success:
            data = response.data
            
            if isinstance(data, dict) and "session_id" in data:
                session_id = data["session_id"]
                
                # Store thinking session ID
                ctx.deps.set_temp_variable("thinking_session_id", session_id)
                
                return f"🧠 **Thinking Session Started**\n\nProblem: {problem}\nSession ID: `{session_id}`\n\nI'm now ready to work through this problem systematically. Use `add_thought()` to contribute reasoning steps, or I'll add thoughts as I analyze the situation."
            else:
                return f"Thinking session started: {response.data}"
        
        return f"❌ Failed to start thinking session: {response.error}"
        
    except Exception as e:
        logger.error(f"Thinking initialization error: {e}")
        return f"❌ Thinking initialization error: {str(e)}"


@business_agent.tool
async def add_thought(
    ctx: RunContext[MCPAgentDependencies],
    thought: str,
    is_revision: bool = False,
    revises_thought: Optional[int] = None
) -> str:
    """
    Add a thought or reasoning step to the current thinking session.
    
    Args:
        thought: The reasoning step or thought to add
        is_revision: Whether this revises a previous thought
        revises_thought: ID of thought being revised (if applicable)
    """
    try:
        params = {
            "thought": thought,
            "is_revision": is_revision
        }
        if revises_thought is not None:
            params["revises_thought"] = revises_thought
        
        response = await ctx.deps.mcp_client.call_tool("addThought", params)
        
        if response.success:
            data = response.data
            
            if isinstance(data, dict) and "thought_id" in data:
                thought_id = data["thought_id"]
                step_number = data.get("step_number", thought_id)
                
                if is_revision:
                    return f"🔄 **Thought Revised** (Step #{step_number})\n\n{thought}"
                else:
                    return f"💡 **Thought Added** (Step #{step_number})\n\n{thought}"
            else:
                return f"Thought added: {response.data}"
        
        return f"❌ Failed to add thought: {response.error}"
        
    except Exception as e:
        logger.error(f"Thought addition error: {e}")
        return f"❌ Thought addition error: {str(e)}"


@business_agent.tool
async def finish_thinking(
    ctx: RunContext[MCPAgentDependencies]
) -> str:
    """
    Complete the thinking session and get the final analysis with reasoning chain.
    """
    try:
        logger.info("Completing thinking session")
        
        response = await ctx.deps.mcp_client.call_tool("finishThinking", {})
        
        if response.success:
            data = response.data
            
            if isinstance(data, dict):
                solution = data.get("solution", "No solution generated")
                reasoning_chain = data.get("reasoning_chain", [])
                confidence = data.get("confidence_score", 0.0)
                alternatives = data.get("alternatives_considered", [])
                
                formatted_output = f"🎯 **Final Analysis Complete**\n\n"
                formatted_output += f"**Solution:**\n{solution}\n\n"
                
                if reasoning_chain:
                    formatted_output += f"**Reasoning Chain:**\n"
                    for i, step in enumerate(reasoning_chain, 1):
                        if isinstance(step, dict):
                            thought = step.get("thought", step)
                            formatted_output += f"{i}. {thought}\n"
                        else:
                            formatted_output += f"{i}. {step}\n"
                    formatted_output += "\n"
                
                if confidence > 0:
                    confidence_pct = confidence * 100
                    formatted_output += f"**Confidence Level:** {confidence_pct:.0f}%\n\n"
                
                if alternatives:
                    formatted_output += f"**Alternative Approaches Considered:**\n"
                    for i, alt in enumerate(alternatives, 1):
                        formatted_output += f"{i}. {alt}\n"
                
                # Clear thinking session ID
                ctx.deps.set_temp_variable("thinking_session_id", None)
                
                return formatted_output
            else:
                return f"Final analysis:\n{response.data}"
        
        return f"❌ Failed to complete thinking session: {response.error}"
        
    except Exception as e:
        logger.error(f"Thinking completion error: {e}")
        return f"❌ Thinking completion error: {str(e)}"

# =============================================================================
# WORKFLOW MANAGEMENT TOOLS
# =============================================================================

@business_agent.tool
async def execute_workflow_template(
    ctx: RunContext[MCPAgentDependencies],
    template_name: str,
    parameters: Optional[Dict[str, Any]] = None
) -> str:
    """
    Execute a predefined workflow template.
    
    Args:
        template_name: Name of workflow template (e.g., 'quarterly_analysis', 'competitive_research')
        parameters: Runtime parameters for the workflow
    """
    try:
        if not ctx.deps.has_permission("can_execute_workflows"):
            return "❌ Error: You don't have permission to execute workflows"
        
        # Create workflow manager
        workflow_manager = WorkflowManager(ctx.deps.mcp_client)
        
        # Get available templates
        templates = workflow_manager.get_workflow_templates()
        
        if template_name not in templates:
            available = ", ".join(templates.keys())
            return f"❌ Workflow template '{template_name}' not found. Available templates: {available}"
        
        logger.info(f"Executing workflow template: {template_name}")
        
        # Execute workflow
        execution = await workflow_manager.execute_template_workflow(template_name, parameters)
        
        # Store execution ID for later reference
        ctx.deps.set_temp_variable(f"workflow_execution_{execution.execution_id}", execution.workflow_id)
        
        # Format results
        formatted_output = f"⚙️ **Workflow Execution: {templates[template_name]}**\n\n"
        formatted_output += f"**Status:** {execution.status.value.title()}\n"
        formatted_output += f"**Execution ID:** `{execution.execution_id}`\n"
        formatted_output += f"**Progress:** {execution.progress_percentage:.0f}%\n\n"
        
        if execution.completed_steps:
            formatted_output += f"**Completed Steps ({len(execution.completed_steps)}):**\n"
            for step_id in execution.completed_steps:
                formatted_output += f"✅ {step_id}\n"
            formatted_output += "\n"
        
        if execution.failed_steps:
            formatted_output += f"**Failed Steps ({len(execution.failed_steps)}):**\n"
            for step_id in execution.failed_steps:
                error = execution.errors.get(step_id, "Unknown error")
                formatted_output += f"❌ {step_id}: {error}\n"
            formatted_output += "\n"
        
        if execution.results:
            formatted_output += f"**Key Results:**\n"
            for step_id, result in list(execution.results.items())[:3]:  # Show first 3 results
                result_preview = str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
                formatted_output += f"📊 {step_id}: {result_preview}\n"
        
        return formatted_output
        
    except Exception as e:
        logger.error(f"Workflow execution error: {e}")
        return f"❌ Workflow execution error: {str(e)}"


# Additional utility function for the agent
def get_agent_info() -> Dict[str, Any]:
    """Get information about the business agent capabilities"""
    return {
        "agent_name": "MCP Business Automation Agent",
        "version": "1.0.0",
        "capabilities": {
            "database": ["query", "list_tables", "execute_statements"],
            "email": ["send_email", "html_support"],
            "web_research": ["scrape_pages", "search_web", "crawl_websites"],
            "thinking": ["structured_analysis", "reasoning_chains"],
            "workflows": ["template_execution", "multi_step_automation"]
        },
        "tools_count": len(business_agent.tools),
        "security_features": ["permission_checking", "input_validation", "confirmation_required"]
    }