# Azure DevOps LangChain MCP Client Application
# This application connects to the official Microsoft Azure DevOps MCP Server
# Requirements: pip install langchain langchain-openai mcp python-dotenv

import os
import json
import asyncio
import subprocess
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Core imports
from dotenv import load_dotenv

# LangChain imports
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import BaseTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import AzureChatOpenAI

# MCP Client imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Load environment variables
load_dotenv()

@dataclass
class Config:
    # Azure OpenAI Configuration
    azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_openai_key: str = os.getenv("AZURE_OPENAI_KEY")
    azure_openai_deployment: str = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    azure_openai_version: str = os.getenv("AZURE_OPENAI_VERSION", "2024-02-01")
    
    # Azure DevOps Configuration (for MCP server)
    devops_organization: str = os.getenv("DEVOPS_ORGANIZATION")  # Just the org name, not full URL

class AzureDevOpsMCPClient:
    """Client for the official Azure DevOps MCP Server"""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = None
        self.server_process = None
    
    async def connect(self):
        """Connect to the Azure DevOps MCP Server"""
        try:
            # Configure server parameters for the official Azure DevOps MCP server
            server_params = StdioServerParameters(
                command="npx",
                args=["-y", "@azure-devops/mcp", self.config.devops_organization]
            )
            
            # Connect to the MCP server
            self.session = await stdio_client(server_params).__aenter__()
            
            # Initialize the session
            init_result = await self.session.initialize()
            print(f"Connected to Azure DevOps MCP Server. Available tools: {len(init_result.capabilities.tools or [])}")
            
            return True
        except Exception as e:
            print(f"Error connecting to MCP server: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server"""
        if self.session:
            try:
                await self.session.__aexit__(None, None, None)
            except Exception as e:
                print(f"Error disconnecting: {e}")
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """Get available tools from the MCP server"""
        if not self.session:
            raise Exception("Not connected to MCP server")
        
        tools_result = await self.session.list_tools()
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema
            }
            for tool in tools_result.tools
        ]
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the MCP server"""
        if not self.session:
            raise Exception("Not connected to MCP server")
        
        try:
            result = await self.session.call_tool(tool_name, arguments)
            return result.content[0].text if result.content else "No result"
        except Exception as e:
            return f"Error calling tool {tool_name}: {str(e)}"

class MCPLangChainTool(BaseTool):
    """LangChain tool wrapper for MCP server tools"""
    
    def __init__(self, mcp_client: AzureDevOpsMCPClient, tool_info: Dict[str, Any]):
        super().__init__()
        self.mcp_client = mcp_client
        self.name = tool_info["name"]
        self.description = tool_info["description"]
        self.tool_info = tool_info
    
    def _run(self, **kwargs) -> str:
        """Synchronous run (calls async version)"""
        return asyncio.run(self._arun(**kwargs))
    
    async def _arun(self, **kwargs) -> str:
        """Asynchronous run"""
        try:
            result = await self.mcp_client.call_tool(self.name, kwargs)
            return str(result)
        except Exception as e:
            return f"Error executing {self.name}: {str(e)}"

class DevOpsAgent:
    """Main agent class that orchestrates LangChain with Azure DevOps MCP"""
    
    def __init__(self, config: Config):
        self.config = config
        self.mcp_client = AzureDevOpsMCPClient(config)
        self.tools = []
        self.agent = None
        
        # Initialize Azure OpenAI
        self.llm = AzureChatOpenAI(
            azure_endpoint=config.azure_openai_endpoint,
            azure_deployment=config.azure_openai_deployment,
            api_version=config.azure_openai_version,
            api_key=config.azure_openai_key,
            temperature=0
        )
    
    async def initialize(self):
        """Initialize the agent with MCP server connection"""
        # Connect to MCP server
        connected = await self.mcp_client.connect()
        if not connected:
            raise Exception("Failed to connect to Azure DevOps MCP server")
        
        # Get available tools
        mcp_tools = await self.mcp_client.list_tools()
        print(f"Available MCP tools: {[tool['name'] for tool in mcp_tools]}")
        
        # Create LangChain tools from MCP tools
        self.tools = [MCPLangChainTool(self.mcp_client, tool) for tool in mcp_tools]
        
        # Create the agent
        self.agent = self._create_agent()
        
        return True
    
    def _create_agent(self):
        """Create LangChain agent with MCP tools"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an Azure DevOps assistant powered by the official Microsoft Azure DevOps MCP Server. 
You can help users interact with their Azure DevOps organization using natural language.

Available capabilities include:
- Project and team management
- Work item operations (create, update, list, search)
- Repository and pull request management  
- Build and release information
- Test plan management
- Search across code, wiki, and work items

Organization: {organization}

Guidelines:
- Always provide clear, formatted responses
- When listing items, format them in a readable way
- Ask for clarification if the request is ambiguous
- Use appropriate tools based on the user's request
- Handle errors gracefully and suggest alternatives

Example queries you can handle:
- "List my ADO projects"
- "Show me open work items for project X"
- "Create a new task in project Y"
- "List recent builds for project Z"
- "Find pull requests in repository A"
""".format(organization=self.config.devops_organization)),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_openai_functions_agent(self.llm, self.tools, prompt)
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True, max_iterations=3)
    
    async def process_query(self, query: str) -> str:
        """Process natural language query"""
        if not self.agent:
            return "Agent not initialized. Please call initialize() first."
        
        try:
            result = await self.agent.ainvoke({"input": query})
            return result["output"]
        except Exception as e:
            return f"Error processing query: {str(e)}"
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.mcp_client.disconnect()

# CLI Interface
class DevOpsCLI:
    """Command line interface for the application"""
    
    def __init__(self):
        self.agent = DevOpsAgent(Config())
    
    async def run(self):
        """Run interactive CLI"""
        print("Azure DevOps LangChain MCP Assistant")
        print("Connecting to Azure DevOps MCP Server...")
        print("-" * 50)
        
        try:
            await self.agent.initialize()
            print("✅ Connected successfully!")
            print("\nAvailable tools:")
            tools = await self.agent.mcp_client.list_tools()
            for tool in tools[:5]:  # Show first 5 tools
                print(f"  • {tool['name']}: {tool['description'][:60]}...")
            if len(tools) > 5:
                print(f"  ... and {len(tools) - 5} more tools")
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return
        
        print(f"\nType 'quit' to exit")
        print(f"Organization: {self.agent.config.devops_organization}")
        print("-" * 50)
        
        try:
            while True:
                query = input("\nYou: ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break
                
                if not query:
                    continue
                
                if query.lower() == 'tools':
                    tools = await self.agent.mcp_client.list_tools()
                    print("\nAvailable tools:")
                    for tool in tools:
                        print(f"  • {tool['name']}: {tool['description']}")
                    continue
                
                print("Assistant: Processing...")
                response = await self.agent.process_query(query)
                print(f"Assistant: {response}")
                
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await self.agent.cleanup()

# Utility functions for setup verification
class SetupChecker:
    """Utility class to verify setup requirements"""
    
    @staticmethod
    def check_azure_cli():
        """Check if Azure CLI is installed and logged in"""
        try:
            result = subprocess.run(['az', 'account', 'show'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Azure CLI is installed and you are logged in")
                return True
            else:
                print("❌ Azure CLI login required. Run: az login")
                return False
        except FileNotFoundError:
            print("❌ Azure CLI not found. Please install from https://docs.microsoft.com/en-us/cli/azure/install-azure-cli")
            return False
    
    @staticmethod
    def check_node_js():
        """Check if Node.js is available"""
        try:
            result = subprocess.run(['node', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Node.js is installed: {result.stdout.strip()}")
                return True
            else:
                print("❌ Node.js is required but not found")
                return False
        except FileNotFoundError:
            print("❌ Node.js not found. Please install from https://nodejs.org/")
            return False
    
    @staticmethod
    def check_mcp_server():
        """Check if the Azure DevOps MCP server can be accessed"""
        try:
            result = subprocess.run(['npx', '-y', '@azure-devops/mcp', '--help'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Azure DevOps MCP server is accessible")
                return True
            else:
                print("❌ Unable to access Azure DevOps MCP server")
                return False
        except Exception as e:
            print(f"❌ Error checking MCP server: {e}")
            return False
    
    @classmethod
    def run_full_check(cls):
        """Run all setup checks"""
        print("Running setup verification...")
        print("-" * 40)
        
        checks = [
            cls.check_azure_cli(),
            cls.check_node_js(),
            cls.check_mcp_server()
        ]
        
        if all(checks):
            print("\n✅ All checks passed! You're ready to go.")
        else:
            print("\n❌ Some checks failed. Please resolve the issues above.")
        
        return all(checks)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        # Run setup verification
        SetupChecker.run_full_check()
    else:
        # Run CLI interface
        cli = DevOpsCLI()
        asyncio.run(cli.run())