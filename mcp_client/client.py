import asyncio
import json
from typing import Dict, Any, List
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client

class DataMigrationClient:
    def __init__(self):
        self.session = None
    
    async def connect(self, command: List[str]):
        """Connect to MCP server"""
        self.session = await stdio_client(command)
        await self.session.initialize()
    
    async def list_tools(self) -> List[Dict]:
        """List available tools from server"""
        if not self.session:
            raise Exception("Not connected to server")
        
        result = await self.session.list_tools()
        return result.tools
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[str]:
        """Call a tool on the server"""
        if not self.session:
            raise Exception("Not connected to server")
        
        result = await self.session.call_tool(name, arguments)
        return result.content
    
    async def get_sql_schema(self, table_name: str) -> Dict:
        """Get SQL Server table schema"""
        result = await self.call_tool("get_sql_schema", {"table_name": table_name})
        return json.loads(result[0]) if result else {}
    
    async def extract_data(self, table_name: str, limit: int = 1000) -> List[Dict]:
        """Extract data from SQL Server"""
        result = await self.call_tool("extract_data", {"table_name": table_name, "limit": limit})
        return json.loads(result[0]) if result else []
    
    async def create_databricks_table(self, table_name: str, schema: Dict) -> str:
        """Create table in Databricks"""
        result = await self.call_tool("create_databricks_table", {"table_name": table_name, "schema": schema})
        return result[0] if result else "No response"
    
    async def load_data(self, table_name: str, data: List[Dict]) -> str:
        """Load data into Databricks"""
        result = await self.call_tool("load_data", {"table_name": table_name, "data": data})
        return result[0] if result else "No response"
    
    async def get_mapping(self, table_name: str) -> Dict:
        """Get column mapping for table"""
        result = await self.call_tool("get_mapping", {"table_name": table_name})
        return json.loads(result[0]) if result else {}
    
    async def close(self):
        """Close the connection"""
        if self.session:
            await self.session.close()

# Example usage
async def main():
    client = DataMigrationClient()
    
    # Connect to server (adjust command as needed)
    await client.connect(["python", "mcp_server/server.py"])
    
    try:
        # List available tools
        tools = await client.list_tools()
        print("Available tools:")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")
        
        # Example: Get schema for a table
        schema = await client.get_sql_schema("dbo.Customers")
        print(f"\nSchema: {schema}")
        
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())