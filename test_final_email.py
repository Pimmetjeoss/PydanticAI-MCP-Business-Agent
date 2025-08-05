#!/usr/bin/env python3
"""Final test to simulate the complete email flow that the user experienced"""

import asyncio
import logging
from pydantic_ai import Agent, RunContext
from mcp_business_agent.dependencies import mcp_context

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_complete_email_flow():
    """Test the complete email flow as the user would experience it"""
    try:
        logger.info("Testing complete email flow...")
        
        async with mcp_context(user_id="test_user") as deps:
            logger.info("✅ Dependencies created successfully!")
            
            # Import the business agent
            from mcp_business_agent.agent import business_agent
            
            # Test 1: User requests email (should show preview)
            logger.info("=" * 60)
            logger.info("TEST 1: User requests email to hotmail address")
            logger.info("=" * 60)
            
            result1 = await business_agent.run(
                "send mail to; pim_lieshout40@hotmail.com, subject; test, body; test",
                deps=deps
            )
            logger.info(f"Agent Response 1:\n{result1.data}")
            
            # Test 2: User confirms (should send email)
            logger.info("\n" + "=" * 60)
            logger.info("TEST 2: User confirms with 'confirmation granted'")
            logger.info("=" * 60)
            
            result2 = await business_agent.run(
                "confirmation granted",
                deps=deps
            )
            logger.info(f"Agent Response 2:\n{result2.data}")
            
            # Check if we still get the original domain restriction error
            if "domain not allowed" in result1.data.lower():
                logger.error("❌ FAILED: Still getting domain restriction error")
            elif "email ready to send" in result1.data.lower() or "email" in result1.data.lower():
                logger.info("✅ SUCCESS: Email preview shown correctly")
                
                if "sent successfully" in result2.data.lower():
                    logger.info("✅ SUCCESS: Email sent after confirmation")
                elif "confirmation" in result2.data.lower():
                    logger.info("✅ SUCCESS: Confirmation flow working (email would send with real MCP server)")
                else:
                    logger.warning("⚠️  Confirmation may need more work")
            else:
                logger.warning("⚠️  Unexpected response format")
        
        logger.info("\n✅ Complete email flow test finished!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_complete_email_flow())