#!/usr/bin/env python3
"""Test script to verify MCP authentication fix"""

import asyncio
import logging
from mcp_business_agent.dependencies import DependencyManager
from mcp_business_agent.agent import business_agent
from pydantic_ai.models.test import TestModel

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_authentication():
    """Test the authentication and web scraping functionality"""
    try:
        # Create dependency manager
        dep_manager = DependencyManager()
        
        logger.info("Creating dependencies...")
        dependencies = await dep_manager.create_dependencies(user_id="test_user")
        
        logger.info("Dependencies created successfully!")
        logger.info(f"MCP Client created: {dependencies.mcp_client is not None}")
        logger.info(f"Has access token: {hasattr(dependencies.mcp_client, 'access_token') and dependencies.mcp_client.access_token is not None}")
        
        # Test the agent with a simple web scraping task
        logger.info("\nTesting web scraping functionality...")
        
        # Use test model for quick testing
        test_model = TestModel()
        agent_with_deps = business_agent.with_deps(dependencies).override(model=test_model)
        
        # Run a test query
        result = await agent_with_deps.run("Can you scrape the website www.example.com?")
        logger.info(f"Agent response: {result.data}")
        
        # Clean up
        await dep_manager.cleanup()
        logger.info("Test completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_authentication())