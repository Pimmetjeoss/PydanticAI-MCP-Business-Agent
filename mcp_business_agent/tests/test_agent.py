"""
Comprehensive test suite for MCP Business Automation Agent using TestModel patterns.
Tests agent behavior, tool registration, and business logic validation.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Any, Dict, List

from pydantic_ai.models.test import TestModel

from ..agent import business_agent, get_agent_info
from ..dependencies import MCPAgentDependencies
from ..mcp_client import MCPClient, MCPResponse, MCPRequestStatus
from ..models import UserPermissions, AgentSession, WorkflowExecution
from ..workflow_manager import WorkflowManager
from ..settings import settings


@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP client for testing"""
    client = Mock(spec=MCPClient)
    
    # Mock successful responses by default
    client.call_tool = AsyncMock(side_effect=lambda tool, params: MCPResponse(
        success=True,
        data=_get_mock_tool_response(tool, params),
        tool_name=tool,
        status=MCPRequestStatus.SUCCESS
    ))
    
    return client


def _get_mock_tool_response(tool_name: str, params: Dict[str, Any]) -> Any:
    """Generate mock responses for different MCP tools"""
    if tool_name == "listTables":
        return {
            "tables": [
                {
                    "name": "sales", 
                    "columns": [
                        {"name": "id", "type": "INTEGER"},
                        {"name": "amount", "type": "DECIMAL"},
                        {"name": "date", "type": "DATE"}
                    ],
                    "row_count": 1500
                },
                {
                    "name": "customers",
                    "columns": [
                        {"name": "id", "type": "INTEGER"},
                        {"name": "name", "type": "VARCHAR"},
                        {"name": "email", "type": "VARCHAR"}
                    ],
                    "row_count": 250
                }
            ]
        }
    
    elif tool_name == "queryDatabase":
        return {
            "rows": [
                {"id": 1, "amount": 1000.50, "date": "2024-01-15"},
                {"id": 2, "amount": 750.25, "date": "2024-01-16"}
            ],
            "row_count": 2,
            "execution_time_ms": 45
        }
    
    elif tool_name == "sendEmail":
        return {
            "message_id": "msg_123456",
            "status": "sent",
            "recipient": params.get("to", "test@example.com")
        }
    
    elif tool_name == "scrapePage":
        return {
            "title": "Example Page Title",
            "content": "This is mock page content for testing purposes.",
            "url": params.get("url", "https://example.com"),
            "links": ["https://example.com/page1", "https://example.com/page2"],
            "images": ["https://example.com/image1.jpg"]
        }
    
    elif tool_name == "searchWeb":
        return {
            "results": [
                {
                    "title": "Search Result 1",
                    "url": "https://example.com/result1",
                    "description": "First search result description",
                    "relevance_score": 0.95
                },
                {
                    "title": "Search Result 2", 
                    "url": "https://example.com/result2",
                    "description": "Second search result description",
                    "relevance_score": 0.87
                }
            ]
        }
    
    elif tool_name == "startThinking":
        return {
            "session_id": "thinking_session_123",
            "problem": params.get("problem", "Test problem"),
            "status": "initialized"
        }
    
    elif tool_name == "addThought":
        return {
            "thought_id": "thought_456",
            "step_number": 1,
            "thought": params.get("thought", "Test thought")
        }
    
    elif tool_name == "finishThinking":
        return {
            "solution": "Mock solution for the problem",
            "reasoning_chain": [
                {"step": 1, "thought": "First reasoning step"},
                {"step": 2, "thought": "Second reasoning step"}
            ],
            "confidence_score": 0.85,
            "alternatives_considered": ["Alternative approach 1", "Alternative approach 2"]
        }
    
    else:
        return {"result": f"Mock result for {tool_name}"}


@pytest.fixture
def test_permissions():
    """Create test user permissions"""
    return UserPermissions(
        user_id="test_user",
        can_read_database=True,
        can_write_database=True,
        can_send_email=True,
        can_scrape_web=True,
        can_execute_workflows=True,
        allowed_email_domains=["@test.com", "@example.com"],
        max_query_results=1000,
        rate_limit_per_hour=100
    )


@pytest.fixture
def test_session():
    """Create test agent session"""
    return AgentSession(
        session_id="test_session_123",
        user_id="test_user",
        started_at=datetime.now(),
        last_activity=datetime.now(),
        message_count=5,
        active_workflows=[],
        context_variables={"test_key": "test_value"}
    )


@pytest.fixture
def test_dependencies(mock_mcp_client, test_permissions, test_session):
    """Create test dependencies"""
    return MCPAgentDependencies(
        mcp_client=mock_mcp_client,
        github_token="test_token_123",
        user_id="test_user",
        session=test_session,
        permissions=test_permissions,
        agent_config={
            "max_conversation_length": 50,
            "default_timeout_seconds": 30,
            "enable_workflow_persistence": True,
            "debug_mode": True
        },
        debug_mode=True
    )


class TestBusinessAgentCore:
    """Test core agent functionality and configuration"""
    
    def test_agent_initialization(self):
        """Test that the agent is properly initialized"""
        assert business_agent is not None
        assert business_agent.deps_type == MCPAgentDependencies
        assert len(business_agent.tools) > 0
        
    def test_agent_info(self):
        """Test agent information retrieval"""
        info = get_agent_info()
        
        assert info["agent_name"] == "MCP Business Automation Agent"
        assert "database" in info["capabilities"]
        assert "email" in info["capabilities"]
        assert "web_research" in info["capabilities"]
        assert "thinking" in info["capabilities"]
        assert "workflows" in info["capabilities"]
        assert info["tools_count"] > 10


class TestDatabaseTools:
    """Test database-related agent tools"""
    
    @pytest.mark.asyncio
    async def test_list_tables_success(self, test_dependencies):
        """Test successful table listing"""
        test_model = TestModel()
        
        with business_agent.override(model=test_model):
            result = await business_agent.run(
                "List all database tables",
                deps=test_dependencies
            )
            
            # Check that the tool was called
            assert test_model.function_tools
            assert any("listTables" in str(tool) for tool in test_model.function_tools)
            
            # Result should contain table information
            assert "Database Schema Overview" in result.data
            assert "sales" in result.data
            assert "customers" in result.data
    
    @pytest.mark.asyncio
    async def test_query_database_validation(self, test_dependencies):
        """Test SQL injection prevention"""
        test_model = TestModel()
        
        with business_agent.override(model=test_model):
            result = await business_agent.run(
                "Execute this SQL: DROP TABLE users",
                deps=test_dependencies
            )
            
            # Should be blocked due to dangerous SQL
            assert "Only SELECT queries are allowed" in result.data
    
    @pytest.mark.asyncio
    async def test_query_database_success(self, test_dependencies):
        """Test successful database query"""
        test_model = TestModel()
        
        with business_agent.override(model=test_model):
            result = await business_agent.run(
                "SELECT * FROM sales WHERE amount > 500",
                deps=test_dependencies
            )
            
            # Should execute successfully
            assert "Query Results" in result.data
            assert "1000.50" in result.data  # From mock data
    
    @pytest.mark.asyncio
    async def test_execute_database_permission_check(self, test_dependencies):
        """Test database write permission checking"""
        # Remove write permission
        test_dependencies.permissions.can_write_database = False
        
        test_model = TestModel()
        
        with business_agent.override(model=test_model):
            result = await business_agent.run(
                "INSERT INTO sales VALUES (1, 100, '2024-01-01')",
                deps=test_dependencies
            )
            
            # Should be blocked due to permissions
            assert "don't have permission to modify" in result.data


class TestEmailTools:
    """Test email-related agent tools"""
    
    @pytest.mark.asyncio
    async def test_send_email_validation(self, test_dependencies):
        """Test email address validation"""
        test_model = TestModel()
        
        with business_agent.override(model=test_model):
            result = await business_agent.run(
                "Send email to invalid-email-address",
                deps=test_dependencies
            )
            
            # Should detect invalid email
            assert "Invalid recipient email address" in result.data
    
    @pytest.mark.asyncio
    async def test_send_email_confirmation_required(self, test_dependencies):
        """Test that email sending requires confirmation"""
        test_model = TestModel()
        
        with business_agent.override(model=test_model):
            result = await business_agent.run(
                "Send email to user@test.com with subject 'Test' and body 'Hello'",
                deps=test_dependencies
            )
            
            # Should require confirmation
            assert "Email Ready to Send" in result.data
            assert "confirm=True" in result.data
    
    @pytest.mark.asyncio 
    async def test_send_email_domain_restriction(self, test_dependencies):
        """Test email domain restrictions"""
        test_model = TestModel()
        
        with business_agent.override(model=test_model):
            result = await business_agent.run(
                "Send email to user@forbidden-domain.com",
                deps=test_dependencies
            )
            
            # Should be blocked due to domain restriction
            assert "Email domain not allowed" in result.data


class TestWebResearchTools:
    """Test web research and scraping tools"""
    
    @pytest.mark.asyncio
    async def test_scrape_page_success(self, test_dependencies):
        """Test successful page scraping"""
        test_model = TestModel()
        
        with business_agent.override(model=test_model):
            result = await business_agent.run(
                "Scrape content from https://example.com",
                deps=test_dependencies
            )
            
            # Should return page content
            assert "Page Content:" in result.data
            assert "Example Page Title" in result.data
    
    @pytest.mark.asyncio
    async def test_search_web_success(self, test_dependencies):
        """Test successful web search"""
        test_model = TestModel()
        
        with business_agent.override(model=test_model):
            result = await business_agent.run(
                "Search for 'business automation tools'",
                deps=test_dependencies
            )
            
            # Should return search results
            assert "Search Results for:" in result.data
            assert "Search Result 1" in result.data
    
    @pytest.mark.asyncio
    async def test_web_tools_permission_check(self, test_dependencies):
        """Test web scraping permission checking"""
        # Remove web scraping permission
        test_dependencies.permissions.can_scrape_web = False
        
        test_model = TestModel()
        
        with business_agent.override(model=test_model):
            result = await business_agent.run(
                "Scrape https://example.com",
                deps=test_dependencies
            )
            
            # Should be blocked due to permissions
            assert "don't have permission to scrape" in result.data


class TestThinkingTools:
    """Test strategic thinking and analysis tools"""
    
    @pytest.mark.asyncio
    async def test_thinking_session_workflow(self, test_dependencies):
        """Test complete thinking session workflow"""
        test_model = TestModel()
        
        with business_agent.override(model=test_model):
            # Start thinking session
            result = await business_agent.run(
                "Help me analyze our competitor's pricing strategy",
                deps=test_dependencies
            )
            
            # Should start thinking session
            assert "Thinking Session Started" in result.data or "thinking" in result.data.lower()
    
    @pytest.mark.asyncio
    async def test_add_thought(self, test_dependencies):
        """Test adding thoughts to thinking session"""
        # Set up thinking session ID
        test_dependencies.set_temp_variable("thinking_session_id", "thinking_session_123")
        
        test_model = TestModel()
        
        with business_agent.override(model=test_model):
            result = await business_agent.run(
                "Add thought: Competitors are using value-based pricing",
                deps=test_dependencies
            )
            
            # Should add thought successfully
            assert "Thought Added" in result.data or "thought" in result.data.lower()


class TestWorkflowExecution:
    """Test workflow execution and management"""
    
    @pytest.mark.asyncio
    async def test_workflow_template_execution(self, test_dependencies):
        """Test executing predefined workflow templates"""
        test_model = TestModel()
        
        with business_agent.override(model=test_model):
            result = await business_agent.run(
                "Execute the quarterly_analysis workflow template",
                deps=test_dependencies
            )
            
            # Should execute workflow
            assert ("Workflow Execution" in result.data or 
                   "quarterly" in result.data.lower() or
                   "analysis" in result.data.lower())


class TestAgentBehaviorPatterns:
    """Test agent behavior patterns and conversation handling"""
    
    @pytest.mark.asyncio
    async def test_multi_step_task_handling(self, test_dependencies):
        """Test agent handling of complex multi-step tasks"""
        # Use TestModel with custom result
        test_model = TestModel(
            custom_result_text="I'll analyze the sales data by first querying the database, then providing insights."
        )
        
        with business_agent.override(model=test_model):
            result = await business_agent.run(
                "Analyze Q4 sales performance and email a summary to executives",
                deps=test_dependencies
            )
            
            # Should handle multi-step task
            assert result.data
            assert "sales" in result.data.lower()
    
    @pytest.mark.asyncio
    async def test_error_handling_graceful_degradation(self, test_dependencies):
        """Test graceful error handling when tools fail"""
        # Mock MCP client to return errors
        test_dependencies.mcp_client.call_tool = AsyncMock(
            side_effect=lambda tool, params: MCPResponse(
                success=False,
                data=None,
                error="Mock tool failure",
                tool_name=tool,
                status=MCPRequestStatus.FAILED
            )
        )
        
        test_model = TestModel()
        
        with business_agent.override(model=test_model):
            result = await business_agent.run(
                "List database tables",
                deps=test_dependencies
            )
            
            # Should handle error gracefully
            assert "Failed" in result.data or "error" in result.data.lower()
    
    @pytest.mark.asyncio
    async def test_context_awareness(self, test_dependencies):
        """Test agent maintains context across conversation"""
        test_model = TestModel()
        
        # Set some context in session
        test_dependencies.set_temp_variable("previous_query", "SELECT * FROM sales")
        
        with business_agent.override(model=test_model):
            result = await business_agent.run(
                "Run the same query again",
                deps=test_dependencies
            )
            
            # Should maintain context
            assert result.data
            # Context handling depends on agent implementation


class TestSecurityAndValidation:
    """Test security measures and input validation"""
    
    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self, test_dependencies):
        """Test comprehensive SQL injection prevention"""
        dangerous_queries = [
            "SELECT * FROM users; DROP TABLE users;",
            "SELECT * FROM sales WHERE id = 1; DELETE FROM customers;",
            "INSERT INTO admin (user) VALUES ('hacker')",
            "UPDATE users SET role = 'admin' WHERE id = 1"
        ]
        
        test_model = TestModel()
        
        for query in dangerous_queries:
            with business_agent.override(model=test_model):
                result = await business_agent.run(
                    f"Execute: {query}",
                    deps=test_dependencies
                )
                
                # Should block dangerous queries
                assert ("Only SELECT queries are allowed" in result.data or
                       "not allowed" in result.data.lower())
    
    @pytest.mark.asyncio
    async def test_permission_enforcement(self, test_dependencies):
        """Test that permissions are properly enforced"""
        # Create restricted permissions
        restricted_permissions = UserPermissions(
            user_id="restricted_user",
            can_read_database=False,
            can_write_database=False,
            can_send_email=False,
            can_scrape_web=False,
            can_execute_workflows=False
        )
        
        test_dependencies.permissions = restricted_permissions
        test_model = TestModel()
        
        with business_agent.override(model=test_model):
            result = await business_agent.run(
                "List database tables",
                deps=test_dependencies
            )
            
            # Should be blocked due to permissions
            assert "don't have permission" in result.data


class TestPerformanceAndReliability:
    """Test performance characteristics and reliability"""
    
    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self, test_dependencies):
        """Test handling of concurrent operations"""
        test_model = TestModel()
        
        # Create multiple concurrent requests
        tasks = []
        for i in range(3):
            with business_agent.override(model=test_model):
                task = business_agent.run(
                    f"Query database for record {i}",
                    deps=test_dependencies
                )
                tasks.append(task)
        
        # Wait for all to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should complete successfully
        assert len(results) == 3
        for result in results:
            assert not isinstance(result, Exception)
    
    @pytest.mark.asyncio
    async def test_large_result_handling(self, test_dependencies):
        """Test handling of large query results"""
        # Mock large result set
        large_data = {
            "rows": [{"id": i, "value": f"data_{i}"} for i in range(1000)],
            "row_count": 1000,
            "execution_time_ms": 500
        }
        
        test_dependencies.mcp_client.call_tool = AsyncMock(
            return_value=MCPResponse(
                success=True,
                data=large_data,
                tool_name="queryDatabase"
            )
        )
        
        test_model = TestModel()
        
        with business_agent.override(model=test_model):
            result = await business_agent.run(
                "SELECT * FROM large_table",
                deps=test_dependencies
            )
            
            # Should handle large results appropriately
            assert "1000 rows" in result.data
            assert "Large dataset" in result.data


# Integration test markers
@pytest.mark.integration
class TestIntegrationScenarios:
    """Integration tests requiring actual MCP server (optional)"""
    
    @pytest.mark.asyncio
    async def test_real_mcp_connectivity(self):
        """Test connectivity with real MCP server (if configured)"""
        # Skip if not configured for integration testing
        if not hasattr(settings, 'test_mcp_server_url'):
            pytest.skip("Integration testing not configured")
        
        # Integration test implementation would go here
        pass


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])