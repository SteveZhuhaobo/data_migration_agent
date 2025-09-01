#!/usr/bin/env python3
"""
Startup wrapper for Snowflake MCP Server with timeout and debugging
"""

import asyncio
import signal
import sys
import os
from server import main

async def startup_with_timeout():
    """Start the server with a timeout for debugging"""
    print("🚀 Snowflake MCP Server Startup Wrapper")
    print("=" * 50)
    
    try:
        # Set a timeout for startup (30 seconds)
        await asyncio.wait_for(main(), timeout=30.0)
    except asyncio.TimeoutError:
        print("❌ Server startup timed out after 30 seconds")
        print("This usually indicates the server is waiting for input on stdin")
        print("Check if the MCP client is properly connected")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Server interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\n🛑 Received signal {signum}, shutting down...")
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the startup
    try:
        asyncio.run(startup_with_timeout())
    except KeyboardInterrupt:
        print("\n🛑 Startup interrupted")
        sys.exit(0)