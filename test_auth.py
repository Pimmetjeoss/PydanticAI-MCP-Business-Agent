#!/usr/bin/env python3
"""
Simple test to verify MCP authentication is working.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_business_agent.mcp_client import MCPClient, create_mcp_client
from mcp_business_agent.settings import settings

async def test_mcp_authentication():
    """Test MCP server authentication and basic connectivity."""
    try:
        print("🧪 Testing MCP authentication...")
        
        # Create MCP client
        async with MCPClient(settings.mcp_server_url) as client:
            print("✅ MCP client initialized successfully")
            
            # Test health check
            health_response = await client.health_check()
            
            if health_response.success:
                print("✅ MCP server health check passed!")
                print(f"   Response: {health_response.data}")
            else:
                print(f"❌ Health check failed: {health_response.error}")
                return False
            
            # Test list tools
            tools_response = await client.list_available_tools()
            
            if tools_response.success:
                print("✅ Successfully retrieved MCP tools!")
                tools = tools_response.data
                if isinstance(tools, list):
                    print(f"   Available tools: {len(tools)}")
                    for tool in tools[:3]:  # Show first 3 tools
                        tool_name = tool.get('name', 'Unknown')
                        tool_desc = tool.get('description', 'No description')
                        print(f"   - {tool_name}: {tool_desc}")
                else:
                    print(f"   Tools data: {tools}")
            else:
                print(f"❌ Failed to list tools: {tools_response.error}")
                
            return True
            
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_mcp_authentication())
    if success:
        print("\n🎉 MCP authentication test completed successfully!")
        print("   The agent should now be able to connect to the MCP server.")
        sys.exit(0)
    else:
        print("\n💥 MCP authentication test failed!")
        sys.exit(1)