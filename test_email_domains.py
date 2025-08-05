#!/usr/bin/env python3
"""Test script to verify email domain restrictions work correctly"""

import asyncio
import logging
from mcp_business_agent.dependencies import mcp_context
from mcp_business_agent.agent import send_email
from pydantic_ai import RunContext

# Set up logging  
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_email_domains():
    """Test that email domains work correctly"""
    try:
        logger.info("Testing email domain restrictions...")
        
        async with mcp_context(user_id="test_user") as deps:
            logger.info("✅ Dependencies created successfully!")
            
            # Create a mock RunContext for the tool
            from unittest.mock import Mock
            ctx = Mock()
            ctx.deps = deps
            
            # Test emails to different domains
            test_emails = [
                ("pim_lieshout40@hotmail.com", "Should be allowed - hotmail"),
                ("test@gmail.com", "Should be allowed - gmail"), 
                ("user@outlook.com", "Should be allowed - outlook"),
                ("person@yahoo.com", "Should be allowed - yahoo"),
                ("blocked@example.com", "Should be blocked - not in allowed list")
            ]
            
            for email, description in test_emails:
                logger.info(f"\nTesting: {email} - {description}")
                
                try:
                    result = await send_email(
                        ctx=ctx,
                        to=email,
                        subject="Test Email",
                        body="This is a test message",
                        confirm=False  # Just test domain validation, don't send
                    )
                    
                    if "domain not allowed" in result.lower():
                        logger.info(f"❌ BLOCKED: {email}")
                    elif "email ready to send" in result.lower():
                        logger.info(f"✅ ALLOWED: {email}")
                    else:
                        logger.info(f"📧 RESULT: {result[:100]}...")
                        
                except Exception as e:
                    logger.error(f"❌ ERROR for {email}: {e}")
        
        logger.info("\n✅ Email domain test completed!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_email_domains())