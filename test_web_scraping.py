#!/usr/bin/env python3
"""Simple test script to verify web scraping authentication"""

import asyncio
import logging
from mcp_business_agent.dependencies import DependencyManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_web_scraping():
    """Test the web scraping tool directly"""
    dep_manager = DependencyManager()
    dependencies = await dep_manager.create_dependencies(user_id="test_user")
    
    # Get the MCP client
    mcp_client = dependencies.mcp_client
    
    # Test the crawlWebsite tool directly
    async with mcp_client:
        logger.info("Testing crawlWebsite tool...")
        
        try:
            response = await mcp_client.call_tool(
                "crawlWebsite", 
                {"url": "https://www.contiweb.com", "limit": 1}
            )
            
            if response.success:
                logger.info("✅ Web scraping successful!")
                logger.info(f"Response data: {response.data}")
            else:
                logger.error(f"❌ Web scraping failed: {response.error}")
                
        except Exception as e:
            logger.error(f"❌ Error calling tool: {e}")
    
    # await dep_manager.cleanup()  # DependencyManager has no cleanup method

if __name__ == "__main__":
    asyncio.run(test_web_scraping())