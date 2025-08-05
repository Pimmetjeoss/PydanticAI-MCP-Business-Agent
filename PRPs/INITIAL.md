## FEATURE:
Build a comprehensive business automation and research agent using Pydantic AI that integrates with your existing MCP (Model Context Protocol) server. This agent will serve as a powerful business assistant capable of:

- **Database Operations**: Execute SQL queries, analyze business data, and extract insights from your PostgreSQL database
- **Email Automation**: Send professional emails, reports, and notifications via Microsoft Graph API integration  
- **Web Research**: Scrape websites, crawl entire domains, map site structures, and perform targeted web searches using Firecrawl
- **Strategic Thinking**: Guide complex problem-solving and decision-making processes through structured sequential thinking workflows
- **Multi-step Workflows**: Chain operations together (e.g., analyze data → generate report → email stakeholders)

The agent communicates via natural language and can handle complex multi-step business workflows like \"Analyze our Q4 sales performance, identify trends, and email a detailed report to the management team\" or \"Research our competitor's new pricing strategy, update our competitive analysis database, and suggest strategic responses.\"

## 📖 COMPLETE IMPLEMENTATION GUIDE

**For comprehensive implementation details**: See [prp_pydantic_ai_base.md](./prp_pydantic_ai_base.md)

This document contains the complete Project Requirements & Planning including:
- MCP Integration Architecture & Authentication Patterns
- PydanticAI Agent Structure & Tool Wrappers  
- Testing Strategies (TestModel, MockMCPClient, Integration Tests)
- Production Security & Deployment Configuration
- Research Requirements & Implementation Blueprint
- Validation Loops & Anti-Patterns

## TOOLS:

### Database Tools
- **`list_tables()`** → Returns comprehensive database schema including table names, column details, data types, and relationships
- **`query_database(sql: str)`** → Executes read-only SQL queries and returns structured data with proper formatting for analysis
- **`execute_database(sql: str)`** → Performs write operations (INSERT/UPDATE/DELETE) for authorized users with built-in SQL injection protection

### Email Communication Tools  
- **`send_email(to: str, subject: str, body: str, cc: Optional[str] = None, bcc: Optional[str] = None, importance: Optional[str] = \"normal\", html_body: Optional[str] = None)`** → Sends emails via Microsoft Graph API with HTML support, priority settings, and multiple recipients

### Web Research & Scraping Tools
- **`scrape_page(url: str, options: Optional[dict] = None)`** → Extracts content from single web pages with configurable extraction options
- **`crawl_website(url: str, max_pages: Optional[int] = None, options: Optional[dict] = None)`** → Initiates comprehensive website crawling and returns job tracking ID
- **`get_crawl_status(job_id: str)`** → Monitors crawling job progress and retrieves completed results
- **`map_website(url: str)`** → Generates detailed sitemaps for URL discovery and site structure analysis  
- **`search_web(query: str, max_results: Optional[int] = 10)`** → Performs targeted web searches with content extraction and relevance ranking

### Strategic Thinking Tools
- **`start_thinking(problem: str, context: Optional[str] = None)`** → Initiates structured problem-solving session with defined scope
- **`add_thought(thought: str, is_revision: bool = False, revises_thought: Optional[int] = None)`** → Contributes reasoning steps to ongoing thinking process
- **`branch_thinking(from_thought: int, new_direction: str)`** → Creates alternative reasoning paths for complex decisions
- **`finish_thinking()`** → Completes analysis and returns comprehensive solution with reasoning chain

## DEPENDENCIES

### MCP Server Integration
- **`MCP_SERVER_URL`** - URL of your deployed Cloudflare Workers MCP server (e.g., `https://your-worker.workers.dev`)
- **`MCP_AUTH_TOKEN`** - GitHub OAuth token for MCP server authentication
- **HTTP Client** - `httpx` or `aiohttp` for async communication with MCP endpoints

### Authentication & Sessions  
- **`GITHUB_ACCESS_TOKEN`** - Personal access token for GitHub OAuth flow
- **`SESSION_ENCRYPTION_KEY`** - Key for encrypting session data (if maintaining local sessions)

### Optional Direct Integrations
- **`FIRECRAWL_API_KEY`** - Direct Firecrawl access (alternative to MCP routing)
- **`MICROSOFT_CLIENT_ID`** & **`MICROSOFT_CLIENT_SECRET`** - For direct Microsoft Graph API access

### System Dependencies
- **`pydantic-ai`** - Core agent framework
- **`httpx`** - Async HTTP client for MCP communication  
- **`pydantic`** - Data validation and structured responses
- **`python-dotenv`** - Environment variable management

## SYSTEM PROMPT(S)
You are a Business Automation & Research Agent with access to powerful enterprise tools through an MCP server. Your role is to help users with:

### Data Analysis & Insights: 
Use database tools to query business data, identify trends, generate reports, and provide actionable insights. Always validate SQL queries and present results clearly.

### Communication & Reporting: 
Craft professional emails, reports, and summaries. Use appropriate tone and formatting. Always confirm before sending emails.

### Research & Intelligence: 
Leverage web scraping and search tools to gather competitive intelligence, market research, and industry insights. Verify information from multiple sources.

### Strategic Decision Support: 
Guide users through complex problem-solving using structured thinking tools. Break down problems, explore alternatives, and provide reasoned recommendations.

### Workflow Automation: 
Chain multiple tools together to create efficient workflows. For example: analyze data → generate insights → create report → email stakeholders.

### Key Principles:

- Always prioritize data security and user permissions
- Confirm destructive database operations before execution
- Validate email recipients and content before sending
- Respect website robots.txt and rate limits during scraping
- Provide clear explanations of your reasoning process
- Offer multiple options for complex decisions
- Maintain context across multi-step workflows

When users request complex tasks, break them down into clear steps and explain your approach before proceeding.

## EXAMPLES:

### Multi-Source Research Report
User: \"Create an industry trends report for our upcoming board meeting\"

1. `search_web(\"industry trends 2024 market analysis\")`
2. `crawl_website(\"https://industry-reports.com\")`
3. `get_crawl_status(job_id)`
4. `query_database(\"SELECT * FROM market_data WHERE date > '2024-01-01'\")`
5. `start_thinking(\"Industry trends analysis combining external research with internal data\")`
6. `send_email(to=\"board@company.com\", subject=\"Industry Trends Report - Board Meeting\", body=\"[Comprehensive report]\")`

### Competitive Analysis Workflow
User: \"Research competitor pricing and update our competitive analysis\"

1. `search_web(\"competitor XYZ pricing 2024\")`
2. `scrape_page(\"https://competitor.com/pricing\")` 
3. `start_thinking(\"Competitive pricing strategy analysis\")`
4. `execute_database(\"INSERT INTO competitive_analysis (competitor, product, price, date_updated) VALUES (...)\")`
5. `send_email(to=\"product-team@company.com\", subject=\"Competitive Pricing Update\", body=\"[Analysis summary]\")`

### Comprehensive Business Analysis Workflow
User: \"Analyze our Q4 performance and email insights to the executive team\"

1. `list_tables()` # Discover available data
2. `query_database(\"SELECT month, SUM(revenue), COUNT(orders) FROM sales WHERE quarter = 4 GROUP BY month\")`
3. `query_database(\"SELECT product_category, SUM(revenue) FROM sales WHERE quarter = 4 GROUP BY product_category\")`
4. `start_thinking(\"Q4 performance analysis based on sales data\")`
5. `add_thought(\"Revenue trends show 15% growth in December, driven primarily by consumer electronics\")`
6. `finish_thinking()`
7. `send_email(to=\"executives@company.com\", subject=\"Q4 Performance Analysis\", body=\"[Generated report]\")`

## DOCUMENTATION:

### Project-Specific Documentation
1. **Project Requirements & Planning**: [prp_pydantic_ai_base.md](./prp_pydantic_ai_base.md) - Complete implementation guide with MCP integration patterns, testing strategies, and production deployment considerations

1. Pydantic AI Official Documentation: https://ai.pydantic.dev/
2. MCP Protocol Specification: https://modelcontextprotocol.io/
3. Agent Creation Guide: https://ai.pydantic.dev/agents/
4. Tool Integration Patterns: https://ai.pydantic.dev/tools/
5. Testing with Pydantic AI: https://ai.pydantic.dev/testing/
6. Your MCP Server Repository: https://github.com/Pimmetjeoss/MCP_Server
7. Cloudflare Workers Documentation: https://developers.cloudflare.com/workers/
8. Microsoft Graph API: https://docs.microsoft.com/en-us/graph/
9. Firecrawl API Documentation: https://docs.firecrawl.dev/

## OTHER CONSIDERATIONS:

- Use environment variables for API key configuration instead of hardcoded model strings
- Keep agents simple - default to string output unless structured output is specifically needed
- Follow the main_agent_reference patterns for configuration and providers
- Always include comprehensive testing with TestModel for development`
