# mcp_server/qa_server.py

import asyncio
import yaml
import openai
from mcp.server import Server
from mcp.types import Tool, TextContent
from typing import List, Dict, Any, Optional
import mcp.server.stdio

# MCP server instance
server = Server("qa-mcp-server")

# Global config
config = {}

def load_config():
    global config
    with open("config/config.yaml", "r") as f:
        config = yaml.safe_load(f)

    # Configure OpenAI client
    openai.api_key = config["azure_openai"]["api_key"]
    openai.api_base = config["azure_openai"]["endpoint"]
    openai.api_version = config["azure_openai"]["api_version"]

@server.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="ask_question",
            description="Ask a question using Azure OpenAI",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {"type": "string"}
                },
                "required": ["question"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Optional[Dict[str, Any]] = None) -> List[TextContent]:
    if name == "ask_question":
        question = arguments["question"]
        answer = await ask_openai(question)
        return [TextContent(type="text", text=answer)]
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

async def ask_openai(question: str) -> str:
    try:
        deployment = config["azure_openai"]["deployment_name"]

        client = openai.AzureOpenAI(
            api_key=config["azure_openai"]["api_key"],
            api_version=config["azure_openai"]["api_version"],
            azure_endpoint=config["azure_openai"]["endpoint"]
        )

        response = client.chat.completions.create(
            model=deployment,  # deployment name used as "model"
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": question}
            ],
            temperature=0.7,
            max_tokens=500
        )

        return response.choices[0].message.content
    except Exception as e:
        return f"Error calling Azure OpenAI: {e}"

async def main():
    load_config()
    async with mcp.server.stdio.stdio_server() as (read, write):
        await server.run(
            read,
            write,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
