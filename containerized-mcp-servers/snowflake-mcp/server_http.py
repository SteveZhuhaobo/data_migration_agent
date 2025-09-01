#!/usr/bin/env python3
"""
Snowflake MCP Server with HTTP Support
Enhanced version that supports both stdio and HTTP protocols
"""

import asyncio
import json
import os
from typing import Dict, Any, List, Optional
from mcp.server import Server
from mcp.types import Resource, Tool, TextContent
import mcp.server.stdio
import mcp.server.sse

# Import the existing server components
from server import (
    load_config, initialize_global_instances, 
    connection_manager, sql_executor, server,
    validate_environment
)

async def main():
    """Main entry point with HTTP and stdio support"""
    try:
        # Validate environment variables first
        print("🔍 Validating environment configuration...")
        if not validate_environment():
            print("❌ Environment validation failed. Server cannot start.")
            return
        
        # Load configuration on startup
        load_config()
        print("✅ Configuration loaded successfully")
        
        # Initialize global instances after config is loaded
        initialize_global_instances()
        print("✅ Global instances initialized successfully")
        
        # Check if we should run in HTTP mode
        http_mode = os.getenv('MCP_HTTP_MODE', 'false').lower() == 'true'
        http_port = int(os.getenv('MCP_HTTP_PORT', '8080'))
        
        if http_mode:
            print(f"🌐 Starting Snowflake MCP Server in HTTP mode on port {http_port}...")
            
            # Run HTTP server using SSE (Server-Sent Events)
            from mcp.server.sse import SseServerTransport
            from starlette.applications import Starlette
            from starlette.routing import Route
            from starlette.responses import Response
            import uvicorn
            
            # Create SSE transport
            sse_transport = SseServerTransport("/messages")
            
            async def handle_sse(request):
                async with sse_transport.connect_sse(
                    request.scope, request.receive, request._send
                ) as streams:
                    await server.run(
                        streams[0], streams[1], server.create_initialization_options()
                    )
            
            async def handle_messages(request):
                async with sse_transport.connect_post(
                    request.scope, request.receive, request._send
                ) as streams:
                    await server.run(
                        streams[0], streams[1], server.create_initialization_options()
                    )
            
            # Health check endpoint
            async def health_check(request):
                return Response("OK", status_code=200)
            
            app = Starlette(
                routes=[
                    Route("/sse", handle_sse),
                    Route("/messages", handle_messages, methods=["POST"]),
                    Route("/health", health_check),
                ]
            )
            
            # Run the HTTP server
            config = uvicorn.Config(app, host="0.0.0.0", port=http_port)
            server_instance = uvicorn.Server(config)
            await server_instance.serve()
            
        else:
            print("📡 Starting Snowflake MCP Server in stdio mode...")
            
            # Run the traditional stdio MCP server
            async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
                await server.run(
                    read_stream,
                    write_stream,
                    server.create_initialization_options()
                )
                
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())