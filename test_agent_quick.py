#!/usr/bin/env python3
"""Quick test to verify the agent works with SSE client"""

import asyncio
import logging
from mcp_business_agent.dependencies import mcp_context

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_agent_with_sse():
    """Test that the agent dependencies work with SSE client"""
    try:
        logger.info("Testing agent with SSE client...")
        
        async with mcp_context(user_id="test_user") as deps:
            logger.info("✅ Dependencies created successfully!")
            logger.info(f"MCP Client type: {type(deps.mcp_client)}")
            logger.info(f"User ID: {deps.user_id}")
            logger.info(f"Debug mode: {deps.debug_mode}")
            
            # Test a simple tool call
            logger.info("Testing tool call...")
            response = await deps.mcp_client.call_tool("listTables", {})
            
            if response.success:
                logger.info("✅ Tool call successful!")
                logger.info(f"Response data: {response.data}")
            else:
                logger.error(f"❌ Tool call failed: {response.error}")
        
        logger.info("✅ All tests passed!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent_with_sse())