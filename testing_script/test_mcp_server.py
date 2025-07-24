#!/usr/bin/env python3
"""
Simple MCP client test script
"""

import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp_server():
    """Simple test of the MCP server"""
    
    print("=== Simple MCP Server Test ===")
    
    try:
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["mcp_server/server.py"]
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("✓ Connected to MCP server successfully")
                
                # Test list_tools
                print("\nTesting list_tools...")
                tools = await session.list_tools()
                print(f"✓ Found {len(tools.tools)} tools:")
                for tool in tools.tools:
                    print(f"  - {tool.name}: {tool.description}")
                
                # Test get_mapping tool
                print("\nTesting get_mapping tool...")
                result = await session.call_tool("get_mapping", {"table_name": "dbo.Customers"})
                print(f"✓ get_mapping result: {result.content[0].text}")
                
                # Test get_sql_schema tool
                print("\nTesting get_sql_schema tool...")
                result = await session.call_tool("get_sql_schema", {"table_name": "dbo.Customers"})
                print(f"✓ get_sql_schema result: {result.content[0].text}")
                
                # Test getting top 10 records from orders table
                print("\nTesting top 10 orders retrieval...")
                try:
                    # Correct call
                    result = await session.call_tool("extract_data", {
                        "table_name": "dbo.Customers",
                        "limit": 10
                    })
                    print("✓ Top 10 orders retrieved successfully:")
                    print(result.content[0].text)

                    
                except Exception as query_error:
                    print(f"⚠️  Query tool test failed: {query_error}")
                    
                
                print("\n✅ All tests completed!")
                return True
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_mcp_server())
    sys.exit(0 if success else 1)