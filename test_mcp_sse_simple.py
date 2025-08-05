#!/usr/bin/env python3
"""Simple test for the new MCP SSE client"""

import asyncio
import logging
from mcp_business_agent.mcp_sse_client import MCPSSEClient
from mcp_business_agent.oauth_manager import oauth_manager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_mcp_sse_client():
    """Test the new MCP SSE client"""
    try:
        # Get OAuth authentication
        logger.info("Getting OAuth authentication...")
        cookies = await oauth_manager.get_valid_session_cookies()
        
        if not cookies:
            logger.error("Failed to get OAuth session cookies")
            return
        
        access_token = cookies.get('mcp_access_token')
        if not access_token:
            logger.error("No access token found in cookies")
            return
        
        logger.info("✅ Got OAuth credentials")
        
        # Create SSE client
        server_url = "http://localhost:8792/sse"
        client = MCPSSEClient(server_url, access_token)
        
        # Test health check
        logger.info("Testing health check...")
        health_response = await client.health_check()
        
        if health_response.success:
            logger.info(f"✅ Health check successful: {health_response.data}")
        else:
            logger.error(f"❌ Health check failed: {health_response.error}")
            return
        
        # Test list tools
        logger.info("Testing list tools...")
        tools_response = await client.list_available_tools()
        
        if tools_response.success:
            tools_data = tools_response.data
            logger.info(f"✅ Found {tools_data['count']} tools:")
            for tool in tools_data['tools']:
                logger.info(f"  - {tool['name']}: {tool['description']}")
        else:
            logger.error(f"❌ List tools failed: {tools_response.error}")
            return
        
        # Test web scraping tool
        logger.info("Testing web scraping...")
        scrape_response = await client.call_tool(
            "crawlWebsite",
            {"url": "https://www.contiweb.com", "limit": 1}
        )
        
        if scrape_response.success:
            logger.info("✅ Web scraping successful!")
            # Just show first 200 chars of response
            response_text = str(scrape_response.data)[:200]
            logger.info(f"Response preview: {response_text}...")
        else:
            logger.error(f"❌ Web scraping failed: {scrape_response.error}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_sse_client())