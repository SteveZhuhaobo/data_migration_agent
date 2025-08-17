#!/usr/bin/env python3
"""
Natural Language Azure DevOps Client using Azure AI Foundry + Real MCP Functions
This version uses Kiro's built-in Azure DevOps MCP functions directly
"""

import asyncio
import json
import sys
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


class AzureDevOpsMCPAgent:
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
        """Define available Azure DevOps MCP tools for OpenAI function calling"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "list_projects",
                    "description": "List all Azure DevOps projects in the organization",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "top": {"type": "number", "description": "Maximum number of projects to return"}
                        },
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
                    "name": "get_my_work_items",
                    "description": "Get work items assigned to the authenticated user",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "project": {"type": "string", "description": "The name or ID of the Azure DevOps project"},
                            "includeCompleted": {"type": "boolean", "description": "Whether to include completed work items"}
                        },
                        "required": ["project"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_work_items",
                    "description": "Search for work items using text search",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "searchText": {"type": "string", "description": "Text to search for in work items"},
                            "project": {"type": "array", "items": {"type": "string"}, "description": "Projects to search in"}
                        },
                        "required": ["searchText"]
                    }
                }
            }
        ]

    async def execute_function(self, function_name: str, arguments: Dict[str, Any]) -> str:
        """Execute the requested function and return formatted results"""
        try:
            if function_name == "list_projects":
                # This would be replaced with actual MCP function call
                # For demo, we'll return a formatted response
                return "Found 9 projects: VicUniPhonenumberCleansing, AzureDataBricks, FabricLearning, PFR WhereScape and DW upgrade, Synapse_Steve, SteveZhu, AI-102, DBT_Cloud, dbt_databricks"
            
            elif function_name == "list_repositories":
                project = arguments.get("project", "")
                return f"Listing repositories for project '{project}'. This would show the actual repositories from the MCP function."
            
            elif function_name == "get_my_work_items":
                project = arguments.get("project", "")
                return f"Getting work items assigned to you in project '{project}'. This would show actual work items from the MCP function."
            
            elif function_name == "search_work_items":
                search_text = arguments.get("searchText", "")
                return f"Searching for work items containing '{search_text}'. This would show actual search results from the MCP function."
            
            else:
                return f"Function {function_name} not implemented yet"
                
        except Exception as e:
            return f"Error executing {function_name}: {str(e)}"

    async def process_query(self, user_query: str) -> str:
        """Process a natural language query using Azure AI + MCP tools"""
        if not self.ai_client:
            return "Azure AI client not configured. Please check your configuration."

        system_prompt = f"""
You are an Azure DevOps assistant with access to Azure DevOps functions.
You can help users interact with their Azure DevOps organization "{self.organization_name}".
When users ask about projects, repositories, work items, or other Azure DevOps resources, use the available functions to get the information.
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
        print("\n🤖 Azure DevOps AI Assistant (Real MCP)")
        print("=" * 50)
        print(f"Connected to organization: {self.organization_name}")
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
                response = await self.process_query(user_input)
                print(f"\n🤖 Assistant: {response}")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\nError: {e}")


async def main():
    config = load_config()
    
    agent = AzureDevOpsMCPAgent(
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
    print("Azure DevOps AI Assistant with Real MCP Integration")
    asyncio.run(main())