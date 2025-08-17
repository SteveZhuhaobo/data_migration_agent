#!/usr/bin/env python3
"""
Azure DevOps AI Assistant with Real MCP Server Connection
This version connects to an actual MCP server for Azure DevOps
"""

import asyncio
import json
import os
import yaml
import subprocess
import sys
from typing import List, Dict, Any
from openai import AzureOpenAI

# Try to import MCP client libraries
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    print("⚠️  MCP client libraries not available. Install with: pip install mcp")
    MCP_AVAILABLE = False


def load_config():
    """Load configuration from config.yaml"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    yaml_path = os.path.join(project_root, "config", "config.yaml")
    
    if os.path.exists(yaml_path):
        with open(yaml_path, "r") as f:
            config = yaml.safe_load(f) or {}
        print("✓ Loaded configuration from config.yaml")
    else:
        config = {}
        print("⚠️  No config.yaml found")

    azure_openai_config = config.get("azure_openai", {})
    azure_devops_config = config.get("azure_devops", {})

    return {
        "azure_devops_org": azure_devops_config.get("organization", "SteveZhu0309"),
        "azure_endpoint": azure_openai_config.get("endpoint"),
        "api_key": azure_openai_config.get("api_key"),
        "deployment_name": azure_openai_config.get("deployment_name"),
        "api_version": azure_openai_config.get("api_version", "2025-01-01-preview")
    }


class MCPAzureDevOpsAgent:
    def __init__(self, organization_name, azure_endpoint, api_key, deployment_name, api_version):
        self.organization_name = organization_name
        self.mcp_session = None
        self.available_tools = []
        
        if azure_endpoint and api_key and deployment_name:
            self.ai_client = AzureOpenAI(
                azure_endpoint=azure_endpoint,
                api_key=api_key,
                api_version=api_version
            )
            self.deployment_name = deployment_name
            print("✓ Azure AI client initialized")
        else:
            self.ai_client = None
            self.deployment_name = None
            print("⚠️  Azure AI credentials not provided")

    async def connect_to_mcp_server(self):
        """Connect to the Azure DevOps MCP server"""
        if not MCP_AVAILABLE:
            print("❌ MCP client libraries not available")
            return False

        try:
            # Try different MCP server configurations
            server_configs = [
                # Configuration 1: Using uvx with mcp-server-azure-devops
                {
                    "command": "uvx",
                    "args": ["mcp-server-azure-devops"],
                    "env": {"AZURE_DEVOPS_ORG": self.organization_name}
                },
                # Configuration 2: Using npx with a different package
                {
                    "command": "npx",
                    "args": ["-y", "azure-devops-mcp-server", self.organization_name]
                },
                # Configuration 3: Direct python execution if available
                {
                    "command": "python",
                    "args": ["-m", "azure_devops_mcp", "--org", self.organization_name]
                }
            ]

            for i, config in enumerate(server_configs, 1):
                print(f"🔄 Trying MCP server configuration {i}...")
                try:
                    # Set up environment variables
                    env = os.environ.copy()
                    if "env" in config:
                        env.update(config["env"])
                    
                    # Create server parameters
                    server_params = StdioServerParameters(
                        command=config["command"],
                        args=config["args"],
                        env=env
                    )

                    # Try to connect
                    async with stdio_client(server_params) as (read, write):
                        self.mcp_session = ClientSession(read, write)
                        
                        # Test the connection by listing tools
                        tools_response = await self.mcp_session.list_tools()
                        self.available_tools = self._prepare_tools_for_llm(tools_response.tools)
                        
                        print(f"✓ Connected to Azure DevOps MCP server (config {i})")
                        print(f"✓ Available MCP tools: {len(self.available_tools)}")
                        return True
                        
                except Exception as e:
                    print(f"❌ Configuration {i} failed: {str(e)}")
                    continue

            print("❌ Could not connect to any MCP server configuration")
            return False
            
        except Exception as e:
            print(f"❌ Error connecting to MCP server: {str(e)}")
            return False

    def _prepare_tools_for_llm(self, mcp_tools) -> List[Dict]:
        """Convert MCP tools to OpenAI function calling format"""
        openai_tools = []
        for tool in mcp_tools:
            function_def = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
            if hasattr(tool, 'inputSchema') and tool.inputSchema:
                if 'properties' in tool.inputSchema:
                    function_def["function"]["parameters"]["properties"] = tool.inputSchema["properties"]
                if 'required' in tool.inputSchema:
                    function_def["function"]["parameters"]["required"] = tool.inputSchema["required"]
            openai_tools.append(function_def)
        return openai_tools

    async def _execute_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute an MCP tool and return formatted results"""
        if not self.mcp_session:
            return "MCP server not connected"
            
        try:
            result = await self.mcp_session.call_tool(tool_name, arguments)
            if result and result.content:
                formatted_result = []
                for content in result.content:
                    if hasattr(content, 'text'):
                        formatted_result.append(content.text)
                    elif hasattr(content, 'data'):
                        formatted_result.append(str(content.data))
                return "\n".join(formatted_result)
            else:
                return f"No results returned from {tool_name}"
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    async def process_query(self, user_query: str) -> str:
        """Process a natural language query using Azure AI + MCP tools"""
        if not self.ai_client:
            return "Azure AI client not configured. Please check your configuration."

        if not self.mcp_session:
            return "MCP server not connected. Please connect to the MCP server first."

        system_prompt = f"""
You are an Azure DevOps assistant with access to MCP tools.
You can help users interact with their Azure DevOps organization "{self.organization_name}".
Use the available MCP tools to get real-time information from Azure DevOps.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]

        try:
            response = self.ai_client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                tools=self.available_tools,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=1500
            )
            
            message = response.choices[0].message

            if message.tool_calls:
                messages.append(message)
                
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    print(f"🔧 Calling MCP tool: {function_name} with {function_args}")
                    
                    tool_result = await self._execute_mcp_tool(function_name, function_args)
                    
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": tool_result
                    })
                
                final_response = self.ai_client.chat.completions.create(
                    model=self.deployment_name,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2000
                )
                return final_response.choices[0].message.content
            else:
                return message.content
                
        except Exception as e:
            return f"Error processing query: {str(e)}"

    async def interactive_session(self):
        """Run an interactive chat session"""
        print("\n🤖 Azure DevOps AI Assistant (MCP Server Connection)")
        print("=" * 65)
        print(f"Connected to organization: {self.organization_name}")
        
        if self.mcp_session:
            print("✓ MCP server connected")
            print(f"✓ Available MCP tools: {len(self.available_tools)}")
        else:
            print("❌ MCP server not connected - limited functionality")
            
        print("\nAsk me anything about your Azure DevOps organization!")
        print("Type 'quit' to exit.")
        print("=" * 65)

        while True:
            try:
                user_input = input("\n💬 You: ").strip()
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    break
                if not user_input:
                    continue
                    
                print("\n🤔 Thinking...")
                response = await self.process_query(user_input)
                print(f"\n🤖 Assistant: {response}")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\nError: {e}")

    def get_fallback_tools(self) -> List[Dict]:
        """Fallback tools when MCP server is not available"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "list_projects_fallback",
                    "description": "List Azure DevOps projects (fallback mode)",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "help_connect_mcp",
                    "description": "Get help on connecting to MCP server",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                }
            }
        ]

    async def execute_fallback_function(self, function_name: str, arguments: Dict[str, Any]) -> str:
        """Execute fallback functions when MCP is not available"""
        if function_name == "list_projects_fallback":
            return f"MCP server not connected. To see real projects, please connect to the MCP server first."
        elif function_name == "help_connect_mcp":
            return """
To connect to the Azure DevOps MCP server, you need to:

1. **Install MCP client libraries**:
   ```
   pip install mcp
   ```

2. **Install Azure DevOps MCP server**:
   ```
   uvx install mcp-server-azure-devops
   ```
   or
   ```
   npm install -g azure-devops-mcp-server
   ```

3. **Set up authentication**:
   - Set AZURE_DEVOPS_ORG environment variable
   - Set AZURE_DEVOPS_PAT environment variable with your Personal Access Token

4. **Restart the application**

The application will automatically try to connect to the MCP server on startup.
"""
        else:
            return f"Function {function_name} not implemented"


async def main():
    config = load_config()
    
    agent = MCPAzureDevOpsAgent(
        organization_name=config["azure_devops_org"],
        azure_endpoint=config["azure_endpoint"],
        api_key=config["api_key"],
        deployment_name=config["deployment_name"],
        api_version=config["api_version"],
    )
    
    print(f"✓ Azure DevOps organization: {agent.organization_name}")
    
    # Try to connect to MCP server
    mcp_connected = await agent.connect_to_mcp_server()
    
    if not mcp_connected:
        print("⚠️  Running in fallback mode without MCP server")
        agent.available_tools = agent.get_fallback_tools()
    
    await agent.interactive_session()


if __name__ == "__main__":
    print("Azure DevOps AI Assistant with MCP Server Connection")
    print("=" * 60)
    
    # Check if required dependencies are available
    missing_deps = []
    
    try:
        import mcp
    except ImportError:
        missing_deps.append("mcp")
    
    if missing_deps:
        print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
        print("Install with: pip install " + " ".join(missing_deps))
        print("Running in limited mode...")
        print("=" * 60)
    
    asyncio.run(main())