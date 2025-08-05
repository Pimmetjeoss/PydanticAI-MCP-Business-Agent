"""
Pydantic models for MCP Business Automation Agent.
Defines data structures for workflows, tool parameters, and responses.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, EmailStr, HttpUrl, validator
from dataclasses import dataclass


class WorkflowStatus(str, Enum):
    """Status of a workflow execution"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"
    CANCELLED = "cancelled"


class ToolExecutionStatus(str, Enum):
    """Status of individual tool execution"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class EmailImportance(str, Enum):
    """Email importance levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class DatabaseOperationType(str, Enum):
    """Types of database operations"""
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    CREATE = "create"
    ALTER = "alter"
    DROP = "drop"


# Tool Parameter Models
class DatabaseQueryParams(BaseModel):
    """Parameters for database query operations"""
    sql: str = Field(..., description="SQL query to execute")
    max_results: int = Field(default=1000, ge=1, le=10000, description="Maximum number of results")
    timeout_seconds: int = Field(default=30, ge=1, le=300, description="Query timeout")
    
    @validator('sql')
    def validate_sql(cls, v):
        """Basic SQL validation"""
        if not v or not v.strip():
            raise ValueError("SQL query cannot be empty")
        return v.strip()


class EmailParams(BaseModel):
    """Parameters for sending emails"""
    to: EmailStr = Field(..., description="Recipient email address")
    subject: str = Field(..., min_length=1, max_length=200, description="Email subject")
    body: str = Field(..., min_length=1, description="Email body content")
    cc: Optional[EmailStr] = Field(None, description="CC recipient")
    bcc: Optional[EmailStr] = Field(None, description="BCC recipient")
    importance: EmailImportance = Field(default=EmailImportance.NORMAL, description="Email importance")
    html_body: Optional[str] = Field(None, description="HTML email body")
    
    @validator('subject')
    def validate_subject(cls, v):
        """Validate email subject"""
        if not v or not v.strip():
            raise ValueError("Email subject cannot be empty")
        return v.strip()


class WebScrapingParams(BaseModel):
    """Parameters for web scraping operations"""
    url: HttpUrl = Field(..., description="URL to scrape")
    max_pages: Optional[int] = Field(default=1, ge=1, le=100, description="Maximum pages to crawl")
    timeout_seconds: int = Field(default=30, ge=5, le=300, description="Scraping timeout")
    extract_links: bool = Field(default=False, description="Extract links from pages")
    extract_images: bool = Field(default=False, description="Extract image URLs")
    custom_headers: Optional[Dict[str, str]] = Field(None, description="Custom HTTP headers")


class WebSearchParams(BaseModel):
    """Parameters for web search operations"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    max_results: int = Field(default=10, ge=1, le=50, description="Maximum search results")
    country: Optional[str] = Field(default="US", description="Country code for search")
    language: Optional[str] = Field(default="en", description="Language code for search")
    
    @validator('query')
    def validate_query(cls, v):
        """Validate search query"""
        if not v or not v.strip():
            raise ValueError("Search query cannot be empty")
        return v.strip()


class ThinkingParams(BaseModel):
    """Parameters for structured thinking operations"""
    problem: str = Field(..., min_length=1, description="Problem to analyze")
    context: Optional[str] = Field(None, description="Additional context for analysis")
    thinking_steps: int = Field(default=5, ge=1, le=20, description="Number of thinking steps")
    explore_alternatives: bool = Field(default=True, description="Explore alternative solutions")


# Response Models
class DatabaseQueryResult(BaseModel):
    """Result from database query"""
    rows: List[Dict[str, Any]] = Field(default_factory=list, description="Query result rows")
    row_count: int = Field(default=0, description="Number of rows returned")
    columns: List[str] = Field(default_factory=list, description="Column names")
    execution_time_ms: int = Field(default=0, description="Query execution time")
    query: str = Field(..., description="Executed SQL query")


class EmailResult(BaseModel):
    """Result from email sending"""
    message_id: Optional[str] = Field(None, description="Email message ID")
    status: str = Field(..., description="Send status")
    recipient: str = Field(..., description="Email recipient")
    sent_at: datetime = Field(default_factory=datetime.now, description="Send timestamp")


class WebScrapingResult(BaseModel):
    """Result from web scraping"""
    url: str = Field(..., description="Scraped URL")
    title: Optional[str] = Field(None, description="Page title")
    content: str = Field(..., description="Extracted content")
    links: List[str] = Field(default_factory=list, description="Extracted links")
    images: List[str] = Field(default_factory=list, description="Extracted image URLs")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Page metadata")
    scraped_at: datetime = Field(default_factory=datetime.now, description="Scraping timestamp")


class WebSearchResult(BaseModel):
    """Individual web search result"""
    title: str = Field(..., description="Result title")
    url: str = Field(..., description="Result URL")
    description: str = Field(..., description="Result description")
    relevance_score: Optional[float] = Field(None, ge=0, le=1, description="Relevance score")


class ThinkingStep(BaseModel):
    """Individual step in thinking process"""
    step_number: int = Field(..., ge=1, description="Step number")
    thought: str = Field(..., description="Thought content")
    is_revision: bool = Field(default=False, description="Is this a revision of previous thought")
    revises_step: Optional[int] = Field(None, description="Step number being revised")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Confidence in this thought")


class ThinkingResult(BaseModel):
    """Result from thinking process"""
    problem: str = Field(..., description="Original problem")
    solution: str = Field(..., description="Final solution")
    reasoning_steps: List[ThinkingStep] = Field(default_factory=list, description="Reasoning steps")
    alternatives_considered: List[str] = Field(default_factory=list, description="Alternative solutions")
    confidence_score: float = Field(..., ge=0, le=1, description="Overall confidence")
    thinking_time_seconds: int = Field(default=0, description="Time spent thinking")


# Workflow Models
class WorkflowStep(BaseModel):
    """Individual step in a workflow"""
    step_id: str = Field(..., description="Unique step identifier")
    name: str = Field(..., description="Human-readable step name")
    tool_name: str = Field(..., description="MCP tool to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    depends_on: List[str] = Field(default_factory=list, description="Step dependencies")
    status: ToolExecutionStatus = Field(default=ToolExecutionStatus.PENDING, description="Execution status")
    result: Optional[Any] = Field(None, description="Step execution result")
    error: Optional[str] = Field(None, description="Error message if failed")
    started_at: Optional[datetime] = Field(None, description="Execution start time")
    completed_at: Optional[datetime] = Field(None, description="Execution completion time")
    retry_count: int = Field(default=0, description="Number of retries attempted")
    max_retries: int = Field(default=3, description="Maximum retry attempts")


class WorkflowDefinition(BaseModel):
    """Definition of a workflow"""
    workflow_id: str = Field(..., description="Unique workflow identifier")
    name: str = Field(..., description="Human-readable workflow name")
    description: str = Field(..., description="Workflow description")
    steps: List[WorkflowStep] = Field(..., description="Workflow steps")
    timeout_minutes: int = Field(default=30, ge=1, le=480, description="Workflow timeout")
    parallel_execution: bool = Field(default=False, description="Allow parallel step execution")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    created_by: Optional[str] = Field(None, description="Creator identifier")


class WorkflowExecution(BaseModel):
    """Execution state of a workflow"""
    execution_id: str = Field(..., description="Unique execution identifier")
    workflow_id: str = Field(..., description="Workflow definition ID")
    status: WorkflowStatus = Field(default=WorkflowStatus.PENDING, description="Execution status")
    current_step: Optional[str] = Field(None, description="Currently executing step")
    completed_steps: List[str] = Field(default_factory=list, description="Completed step IDs")
    failed_steps: List[str] = Field(default_factory=list, description="Failed step IDs")
    results: Dict[str, Any] = Field(default_factory=dict, description="Step results by ID")
    errors: Dict[str, str] = Field(default_factory=dict, description="Step errors by ID")
    started_at: Optional[datetime] = Field(None, description="Execution start time")
    completed_at: Optional[datetime] = Field(None, description="Execution completion time")
    progress_percentage: float = Field(default=0.0, ge=0, le=100, description="Completion percentage")


# User and Permission Models
class UserPermissions(BaseModel):
    """User permissions for MCP operations"""
    user_id: str = Field(..., description="User identifier")
    can_read_database: bool = Field(default=True, description="Database read permission")
    can_write_database: bool = Field(default=False, description="Database write permission")
    can_send_email: bool = Field(default=False, description="Email sending permission")
    can_scrape_web: bool = Field(default=True, description="Web scraping permission")
    can_execute_workflows: bool = Field(default=True, description="Workflow execution permission")
    allowed_email_domains: List[str] = Field(default_factory=list, description="Allowed email domains")
    max_query_results: int = Field(default=1000, description="Maximum query results allowed")
    rate_limit_per_hour: int = Field(default=100, description="Requests per hour limit")


# Agent Session Models
class AgentSession(BaseModel):
    """Agent conversation session"""
    session_id: str = Field(..., description="Unique session identifier")
    user_id: str = Field(..., description="User identifier")
    started_at: datetime = Field(default_factory=datetime.now, description="Session start time")
    last_activity: datetime = Field(default_factory=datetime.now, description="Last activity time")
    message_count: int = Field(default=0, description="Number of messages in session")
    active_workflows: List[str] = Field(default_factory=list, description="Active workflow IDs")
    context_variables: Dict[str, Any] = Field(default_factory=dict, description="Session context")
    permissions: Optional[UserPermissions] = Field(None, description="User permissions")


# Configuration Models
class AgentConfiguration(BaseModel):
    """Agent configuration settings"""
    agent_name: str = Field(default="MCP Business Agent", description="Agent name")
    max_conversation_length: int = Field(default=50, description="Maximum conversation messages")
    default_timeout_seconds: int = Field(default=30, description="Default operation timeout")
    enable_workflow_persistence: bool = Field(default=True, description="Persist workflow state")
    enable_metrics_collection: bool = Field(default=True, description="Collect usage metrics")
    log_level: str = Field(default="INFO", description="Logging level")
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")


# Predefined workflow templates
WORKFLOW_TEMPLATES = {
    "quarterly_analysis": {
        "name": "Quarterly Business Analysis",
        "description": "Comprehensive quarterly business performance analysis",
        "steps": [
            {
                "step_id": "fetch_sales_data",
                "name": "Fetch Sales Data",
                "tool_name": "query_database",
                "parameters": {"sql": "SELECT * FROM sales WHERE quarter = ?"}
            },
            {
                "step_id": "analyze_trends", 
                "name": "Analyze Trends",
                "tool_name": "start_thinking",
                "parameters": {"problem": "Analyze quarterly sales trends"},
                "depends_on": ["fetch_sales_data"]
            },
            {
                "step_id": "generate_report",
                "name": "Generate Report", 
                "tool_name": "finish_thinking",
                "parameters": {},
                "depends_on": ["analyze_trends"]
            },
            {
                "step_id": "email_report",
                "name": "Email Report",
                "tool_name": "send_email",
                "parameters": {
                    "to": "executives@company.com",
                    "subject": "Quarterly Analysis Report",
                    "body": "Please find the quarterly analysis attached."
                },
                "depends_on": ["generate_report"]
            }
        ]
    },
    "competitive_research": {
        "name": "Competitive Market Research",
        "description": "Research competitors and market trends",
        "steps": [
            {
                "step_id": "search_competitors",
                "name": "Search Competitors",
                "tool_name": "search_web",
                "parameters": {"query": "competitor pricing 2024", "max_results": 20}
            },
            {
                "step_id": "scrape_pricing",
                "name": "Scrape Pricing Pages",
                "tool_name": "scrape_page",
                "parameters": {"url": "https://competitor.com/pricing"},
                "depends_on": ["search_competitors"]
            },
            {
                "step_id": "analyze_competition",
                "name": "Analyze Competition",
                "tool_name": "start_thinking",
                "parameters": {"problem": "Competitive pricing strategy analysis"},
                "depends_on": ["scrape_pricing"]
            },
            {
                "step_id": "update_database",
                "name": "Update Database",
                "tool_name": "execute_database", 
                "parameters": {"sql": "INSERT INTO competitive_analysis ..."},
                "depends_on": ["analyze_competition"]
            }
        ]
    }
}