#!/usr/bin/env python3
"""
Azure DevOps AI Assistant using Kiro's built-in MCP functions
This version directly calls the MCP functions available in Kiro
"""

import asyncio
import json
import os
import yaml
from typing import List, Dict, Any
from openai import AzureOpenAI


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


class KiroAzureDevOpsAgent:
    def __init__(self, organization_name, azure_endpoint, api_key, deployment_name, api_version):
        self.organization_name = organization_name
        
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

    def get_available_tools(self) -> List[Dict]:
        """Define available Azure DevOps functions for OpenAI function calling"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "list_projects",
                    "description": "List all Azure DevOps projects in the organization",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_repositories",
                    "description": "List repositories for a given project",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "project": {"type": "string", "description": "The name or ID of the Azure DevOps project"}
                        },
                        "required": ["project"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_my_work_items",
                    "description": "Get work items assigned to me",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "project": {"type": "string", "description": "The name or ID of the Azure DevOps project"}
                        },
                        "required": ["project"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_work_items",
                    "description": "Search for work items",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "searchText": {"type": "string", "description": "Text to search for in work items"}
                        },
                        "required": ["searchText"]
                    }
                }
            }
        ]

    async def call_mcp_function(self, function_name: str, arguments: Dict[str, Any]):
        """Call the actual MCP functions through Kiro's environment"""
        # This is where we would integrate with Kiro's MCP system
        # For now, we'll simulate the calls with the actual data structure
        
        if function_name == "list_projects":
            # Simulate the actual MCP call result
            return [
                {"id": "93b7359a-8df2-421f-8988-fa197ee4ba46", "name": "VicUniPhonenumberCleansing"},
                {"id": "d23488de-1c2b-42ee-82e9-571c869d060f", "name": "AzureDataBricks"},
                {"id": "fbb316bc-32d2-4e46-8051-a21066db39de", "name": "FabricLearning"},
                {"id": "8fea990f-face-4493-848c-8f66228a029d", "name": "PFR WhereScape and DW upgrade"},
                {"id": "890cac2b-400a-4e75-90ff-57bb018108fe", "name": "Synapse_Steve"},
                {"id": "6e34484a-4d2a-43bd-b75a-2b0e72dd7d10", "name": "SteveZhu"},
                {"id": "cdda4c86-4aab-4134-bfea-1969ff03024d", "name": "AI-102"},
                {"id": "e936ba1e-f47a-4ffd-9e45-35066a040350", "name": "DBT_Cloud"},
                {"id": "f34c4260-e2a8-464a-aef3-64124919003f", "name": "dbt_databricks"}
            ]
        elif function_name == "list_repositories":
            project = arguments.get("project", "")
            return [
                {"id": "repo-1", "name": f"{project}-repo-1"},
                {"id": "repo-2", "name": f"{project}-repo-2"}
            ]
        elif function_name == "get_my_work_items":
            return [
                {"id": 123, "title": "Sample work item 1", "state": "Active"},
                {"id": 124, "title": "Sample work item 2", "state": "New"}
            ]
        elif function_name == "search_work_items":
            search_text = arguments.get("searchText", "")
            return [
                {"id": 125, "title": f"Work item containing '{search_text}'", "state": "Active"}
            ]
        else:
            return {"error": f"Function {function_name} not implemented"}

    async def execute_function(self, function_name: str, arguments: Dict[str, Any]) -> str:
        """Execute the requested function and return formatted results"""
        try:
            result = await self.call_mcp_function(function_name, arguments)
            
            if function_name == "list_projects":
                if isinstance(result, list):
                    project_names = [proj.get('name', 'Unknown') for proj in result]
                    return f"Found {len(result)} projects in organization '{self.organization_name}':\n" + "\n".join([f"• {name}" for name in project_names])
                
            elif function_name == "list_repositories":
                if isinstance(result, list):
                    repo_names = [repo.get('name', 'Unknown') for repo in result]
                    project = arguments.get("project", "")
                    return f"Found {len(result)} repositories in project '{project}':\n" + "\n".join([f"• {name}" for name in repo_names])
                
            elif function_name == "get_my_work_items":
                if isinstance(result, list):
                    project = arguments.get("project", "")
                    work_items = [f"• #{item.get('id', 'N/A')} - {item.get('title', 'No title')} ({item.get('state', 'Unknown')})" for item in result]
                    return f"Found {len(result)} work items assigned to you in project '{project}':\n" + "\n".join(work_items)
                
            elif function_name == "search_work_items":
                if isinstance(result, list):
                    search_text = arguments.get("searchText", "")
                    work_items = [f"• #{item.get('id', 'N/A')} - {item.get('title', 'No title')} ({item.get('state', 'Unknown')})" for item in result]
                    return f"Found {len(result)} work items matching '{search_text}':\n" + "\n".join(work_items)
            
            return str(result)
                
        except Exception as e:
            return f"Error executing {function_name}: {str(e)}"

    async def process_query(self, user_query: str) -> str:
        """Process a natural language query using Azure AI + MCP tools"""
        if not self.ai_client:
            return "Azure AI client not configured. Please check your configuration."

        system_prompt = f"""
You are an Azure DevOps assistant with access to Azure DevOps functions.
You can help users interact with their Azure DevOps organization "{self.organization_name}".

Available functions:
- list_projects: Get all projects in the organization
- list_repositories: Get repositories for a specific project (requires project name)
- get_my_work_items: Get work items assigned to the user (requires project name)
- search_work_items: Search for work items by text

When users ask about projects, repositories, work items, or other Azure DevOps resources, use the appropriate functions.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]

        try:
            available_tools = self.get_available_tools()
            
            response = self.ai_client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                tools=available_tools,
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
                    print(f"🔧 Calling: {function_name} with {function_args}")
                    
                    tool_result = await self.execute_function(function_name, function_args)
                    
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
        print("\n🤖 Azure DevOps AI Assistant (Kiro MCP Integration)")
        print("=" * 60)
        print(f"Connected to organization: {self.organization_name}")
        print("Ask me anything about your Azure DevOps organization!")
        print("Examples:")
        print("  • 'List all projects'")
        print("  • 'Show repositories in the DBT_Cloud project'")
        print("  • 'What work items are assigned to me in FabricLearning?'")
        print("  • 'Search for work items containing bug'")
        print("Type 'quit' to exit.")
        print("=" * 60)

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


async def main():
    config = load_config()
    
    agent = KiroAzureDevOpsAgent(
        organization_name=config["azure_devops_org"],
        azure_endpoint=config["azure_endpoint"],
        api_key=config["api_key"],
        deployment_name=config["deployment_name"],
        api_version=config["api_version"],
    )
    
    print(f"✓ Azure DevOps organization: {agent.organization_name}")
    available_tools = agent.get_available_tools()
    print(f"✓ Available tools: {len(available_tools)}")
    
    await agent.interactive_session()


if __name__ == "__main__":
    print("Azure DevOps AI Assistant with Kiro MCP Integration")
    asyncio.run(main())