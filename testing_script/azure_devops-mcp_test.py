#!/usr/bin/env python3
"""
Natural Language Azure DevOps Client using Azure AI Foundry + MCP
"""

import asyncio
import json
import sys
import os
import yaml
from typing import List, Dict, Any
from openai import AzureOpenAI


# -------------------------------------------------------------------
# ENV + CONFIG
# -------------------------------------------------------------------

def load_env_file():
    """Load environment variables from .env file if it exists"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(project_root, '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value


def load_config():
    """Load configuration from config.yaml, config.json, .env file, or environment variables"""
    config = {}

    # Project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Try config.yaml
    yaml_path = os.path.join(project_root, "config", "config.yaml")
    if os.path.exists(yaml_path):
        try:
            with open(yaml_path, "r") as f:
                config = yaml.safe_load(f) or {}
            print("✓ Loaded configuration from config.yaml")
        except Exception as e:
            print(f"Warning: Could not load config.yaml: {e}")

    # Try config.json (optional fallback)
    json_path = os.path.join(project_root, "config.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r") as f:
                config.update(json.load(f))
            print("✓ Loaded configuration from config.json")
        except Exception as e:
            print(f"Warning: Could not load config.json: {e}")

    # Load from .env
    load_env_file()

    # Extract azure_openai + azure_devops sections
    azure_openai_config = config.get("azure_openai", {})
    azure_devops_config = config.get("azure_devops", {})

    return {
        "azure_devops_org": (
            azure_devops_config.get("organization")
            or os.getenv("AZURE_DEVOPS_ORG")
            or "SteveZhu0309"
        ),
        "azure_endpoint": (
            azure_openai_config.get("endpoint")
            or os.getenv("AZURE_OPENAI_ENDPOINT")
        ),
        "api_key": (
            azure_openai_config.get("api_key")
            or os.getenv("AZURE_OPENAI_API_KEY")
        ),
        "deployment_name": (
            azure_openai_config.get("deployment_name")
            or os.getenv("AZURE_OPENAI_DEPLOYMENT")
        ),
        "api_version": (
            azure_openai_config.get("api_version")
            or os.getenv("AZURE_OPENAI_API_VERSION")
            or "2025-01-01-preview"
        )
    }


# -------------------------------------------------------------------
# MCP + Azure OpenAI Agent
# -------------------------------------------------------------------

class AzureAIMCPAgent:
    def __init__(self, organization_name, azure_endpoint, api_key, deployment_name, api_version):
        self.organization_name = organization_name
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
            print("⚠️  Azure AI credentials not provided - running in MCP-only mode")

    def _prepare_tools_for_llm(self) -> List[Dict]:
        """Convert available MCP tools to OpenAI function calling format"""
        # These are the actual Azure DevOps MCP tools available in Kiro
        return [
            {
                "type": "function",
                "function": {
                    "name": "mcp_azure_devops_core_list_projects",
                    "description": "Retrieve a list of projects in your Azure DevOps organization",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "skip": {"type": "number", "description": "Number of projects to skip"},
                            "top": {"type": "number", "description": "Maximum number of projects to return"}
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "mcp_azure_devops_repo_list_repos_by_project",
                    "description": "Retrieve a list of repositories for a given project",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "project": {"type": "string", "description": "The name or ID of the Azure DevOps project"},
                            "top": {"type": "number", "description": "Maximum number of repositories to return"}
                        },
                        "required": ["project"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "mcp_azure_devops_wit_my_work_items",
                    "description": "Retrieve a list of work items relevant to the authenticated user",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "project": {"type": "string", "description": "The name or ID of the Azure DevOps project"},
                            "includeCompleted": {"type": "boolean", "description": "Whether to include completed work items"},
                            "top": {"type": "number", "description": "Maximum number of work items to return"}
                        },
                        "required": ["project"]
                    }
                }
            }
        ]

    async def _execute_mcp_tool(self, function_name: str, arguments: Dict[str, Any]) -> str:
        """Execute MCP tools using Kiro's built-in functions and return formatted results"""
        try:
            if function_name == "mcp_azure_devops_core_list_projects":
                # Call the actual MCP function through Kiro
                result = await self._call_kiro_mcp_function("mcp_azure_devops_core_list_projects", arguments)
                if isinstance(result, list):
                    project_names = [proj.get('name', 'Unknown') for proj in result]
                    return f"Found {len(result)} projects: {', '.join(project_names)}"
                return str(result)
            
            elif function_name == "mcp_azure_devops_repo_list_repos_by_project":
                result = await self._call_kiro_mcp_function("mcp_azure_devops_repo_list_repos_by_project", arguments)
                if isinstance(result, list):
                    repo_names = [repo.get('name', 'Unknown') for repo in result]
                    return f"Found {len(result)} repositories in project '{arguments.get('project', '')}': {', '.join(repo_names)}"
                return str(result)
            
            elif function_name == "mcp_azure_devops_wit_my_work_items":
                result = await self._call_kiro_mcp_function("mcp_azure_devops_wit_my_work_items", arguments)
                if isinstance(result, list):
                    return f"Found {len(result)} work items assigned to you in project '{arguments.get('project', '')}'"
                return str(result)
            
            else:
                return f"Function {function_name} not implemented yet"
        except Exception as e:
            return f"Error executing {function_name}: {str(e)}"

    async def _call_kiro_mcp_function(self, function_name: str, arguments: Dict[str, Any]):
        """Call Kiro's MCP functions - this is a placeholder that would need to be implemented"""
        # In a real implementation, this would call the actual MCP functions
        # For now, we'll simulate the calls
        if function_name == "mcp_azure_devops_core_list_projects":
            return [
                {"name": "VicUniPhonenumberCleansing", "id": "93b7359a-8df2-421f-8988-fa197ee4ba46"},
                {"name": "AzureDataBricks", "id": "d23488de-1c2b-42ee-82e9-571c869d060f"},
                {"name": "FabricLearning", "id": "fbb316bc-32d2-4e46-8051-a21066db39de"}
            ]
        elif function_name == "mcp_azure_devops_repo_list_repos_by_project":
            return [{"name": "sample-repo", "id": "repo-123"}]
        elif function_name == "mcp_azure_devops_wit_my_work_items":
            return [{"title": "Sample Work Item", "id": 123}]
        else:
            return f"Mock result for {function_name}"

    async def process_natural_language_query(self, user_query: str) -> str:
        """Process a natural language query using Azure AI + MCP tools"""
        if not self.ai_client:
            return "Azure AI client not configured. Please check your configuration."

        system_prompt = f"""
You are an Azure DevOps assistant with access to MCP tools.
You can help users interact with their Azure DevOps organization "{self.organization_name}".
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]

        try:
            # Get the available tools
            available_tools = self._prepare_tools_for_llm()
            
            response = self.ai_client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                tools=available_tools,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=1500
            )
            message = response.choices[0].message

            if message.tool_calls:  # LLM decided to call MCP tools
                messages.append(message)
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    print(f"🔧 Calling: {function_name} with {function_args}")
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
        print("\n🤖 Azure DevOps AI Assistant")
        print("=" * 50)
        print("Ask me anything about your Azure DevOps organization!")
        print("Type 'quit' to exit.")
        print("=" * 50)

        while True:
            try:
                user_input = input("\n💬 You: ").strip()
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    break
                if not user_input:
                    continue
                print("\n🤔 Thinking...")
                response = await self.process_natural_language_query(user_input)
                print(f"\n🤖 Assistant: {response}")
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\nError: {e}")


# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------

async def main():
    # Load config first
    config = load_config()
    print("✓ Loaded configuration")

    agent = AzureAIMCPAgent(
        organization_name=config["azure_devops_org"],
        azure_endpoint=config["azure_endpoint"],
        api_key=config["api_key"],
        deployment_name=config["deployment_name"],
        api_version=config["api_version"],
    )

    print(f"✓ Azure DevOps organization: {agent.organization_name}")
    available_tools = agent._prepare_tools_for_llm()
    print(f"✓ Available tools: {len(available_tools)}")

    await agent.interactive_session()


if __name__ == "__main__":
    print("Azure AI Foundry + Azure DevOps MCP Assistant")
    asyncio.run(main())
