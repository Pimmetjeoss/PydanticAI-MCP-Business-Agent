#!/usr/bin/env python3
"""Simple test to verify email tool behavior directly"""

import asyncio
import logging
from mcp_business_agent.dependencies import mcp_context
from mcp_business_agent.agent import send_email

# Set up logging  
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_email_tool_directly():
    """Test the email tool directly to see confirmation behavior"""
    try:
        logger.info("Testing email tool directly...")
        
        async with mcp_context(user_id="test_user") as deps:
            logger.info("✅ Dependencies created successfully!")
            
            # Create a mock RunContext for the tool
            from pydantic_ai import RunContext
            ctx = RunContext(deps=deps)
            
            # Test 1: Call email tool without confirmation (should show preview)
            logger.info("Test 1: Calling send_email without confirmation")
            result1 = await send_email(
                ctx=ctx,
                to="test@example.com",
                subject="Test Email",
                body="This is a test message",
                confirm=False
            )
            logger.info(f"Result 1: {result1}")
            
            # Test 2: Call email tool with confirmation (should attempt to send)
            logger.info("Test 2: Calling send_email with confirmation")
            result2 = await send_email(
                ctx=ctx,
                to="test@example.com", 
                subject="Test Email",
                body="This is a test message",
                confirm=True
            )
            logger.info(f"Result 2: {result2}")
        
        logger.info("✅ Direct email tool test completed!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_email_tool_directly())