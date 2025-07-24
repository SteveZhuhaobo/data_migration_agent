# mcp_client/qa_client.py

import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent # Keep TextContent as it's used for content processing

async def main():
    """
    Main asynchronous function to connect to the MCP server and ask a question.
    This client launches the MCP server as a subprocess and communicates with it
    via standard I/O.
    """
    print("Setting up MCP QA server subprocess...")

    # Define the parameters for launching the MCP server.
    # sys.executable ensures the correct Python interpreter is used.
    # "mcp_server/qa_server.py" is the path to your server script.
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["mcp_server/qa_server.py"]
    )

    try:
        # Establish a standard I/O client connection, which also launches the server.
        async with stdio_client(server_params) as (read, write):
            print("Server subprocess started. Initializing client session...")

            # Create an MCP ClientSession instance using the read and write streams.
            async with ClientSession(read, write) as session:
                # Initialize the session to establish communication and retrieve server capabilities.
                await session.initialize()
                print("Client session initialized. Asking a question...")

                # Define the question to ask the server.
                question_to_ask = "What is the capital of France? With a list of tourist attractions."

                try:
                    # Call the 'ask_question' tool on the MCP server.
                    # The arguments are passed as a dictionary matching the inputSchema defined in the server.
                    # Removed the ToolCallResult type hint as it was causing the ImportError.
                    response = await session.call_tool(
                        "ask_question",
                        {"question": question_to_ask}
                    )

                    print(f"\nQuestion asked: '{question_to_ask}'")
                    print("Answer from server:")

                    # Process the response from the server.
                    # The server's call_tool returns an object (likely a Message or similar)
                    # which contains a list of Content objects in its 'content' attribute.
                    if response.content:
                        for content_item in response.content:
                            if isinstance(content_item, TextContent):
                                print(content_item.text)
                            else:
                                print(f"Received unexpected content type: {type(content_item)}")
                    else:
                        print("No content received in the response.")

                except Exception as e:
                    print(f"An error occurred while calling the tool: {e}")

    except Exception as e:
        print(f"An error occurred during server setup or client connection: {e}")

    print("\nClient finished.")

if __name__ == "__main__":
    # Run the main asynchronous function.
    asyncio.run(main())
