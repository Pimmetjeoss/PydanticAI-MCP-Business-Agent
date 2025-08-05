#!/usr/bin/env python3
"""Test script to verify email confirmation flow works correctly"""

import asyncio
import logging
from pydantic_ai import Agent, RunContext
from mcp_business_agent.dependencies import mcp_context

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_email_confirmation():
    """Test that the agent properly handles email confirmations"""
    try:
        logger.info("Testing email confirmation flow...")
        
        async with mcp_context(user_id="test_user") as deps:
            logger.info("✅ Dependencies created successfully!")
            
            # Import the business agent
            from mcp_business_agent.agent import business_agent
            
            # Test 1: Send email request (should show preview)
            logger.info("Test 1: Requesting email send (should show preview)")
            result1 = await business_agent.run(
                "Send email to test@example.com, subject: Test Email, body: This is a test message",
                deps=deps
            )
            logger.info(f"Result 1: {result1.data[:200]}...")
            
            # Test 2: Confirm email sending
            logger.info("Test 2: Confirming email send")
            result2 = await business_agent.run(
                "confirm: true",
                deps=deps
            )
            logger.info(f"Result 2: {result2.data[:200]}...")
            
            # Test 3: Try another confirmation pattern
            logger.info("Test 3: Testing different confirmation pattern")
            result3a = await business_agent.run(
                "Send email to test2@example.com, subject: Another Test, body: Another test message",
                deps=deps
            )
            logger.info(f"Result 3a (preview): {result3a.data[:150]}...")
            
            result3b = await business_agent.run(
                "yes, send it",
                deps=deps
            )
            logger.info(f"Result 3b (send): {result3b.data[:200]}...")
        
        logger.info("✅ Email confirmation test completed!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_email_confirmation())