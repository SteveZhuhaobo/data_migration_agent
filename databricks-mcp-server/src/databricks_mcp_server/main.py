"""
Main entry point for the Databricks MCP Server.

This module provides the main() function that serves as the console script entry point
when the package is installed via uvx or pip.
"""

import argparse
import asyncio
import logging
import os
import signal
import sys
from typing import Optional

from .config import ConfigManager, ServerConfig
from .server import DatabricksMCPServer
from .errors import (
    MCPServerError, ConfigurationError, ConnectionError, AuthenticationError,
    UvxEnvironmentError, DependencyError, ErrorHandler, log_structured_error
)


def setup_logging(log_level: str = "INFO") -> None:
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Configure logging to stderr to avoid interfering with JSON-RPC on stdout
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stderr
    )


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Databricks MCP Server - Model Context Protocol server for Databricks operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Configuration:
  The server can be configured using:
  1. Environment variables (highest priority):
     - DATABRICKS_SERVER_HOSTNAME
     - DATABRICKS_HTTP_PATH  
     - DATABRICKS_ACCESS_TOKEN
     - DATABRICKS_CATALOG (optional, default: hive_metastore)
     - DATABRICKS_SCHEMA (optional, default: default)
     - DATABRICKS_TIMEOUT (optional, default: 120)
     - DATABRICKS_MCP_LOG_LEVEL (optional, default: INFO)
  
  2. Configuration file (lower priority):
     - Use --config to specify a custom config file
     - Default locations: ./config.yaml, ./config/config.yaml, ~/.databricks-mcp/config.yaml

Examples:
  # Run with environment variables
  export DATABRICKS_SERVER_HOSTNAME=your-workspace.cloud.databricks.com
  export DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id
  export DATABRICKS_ACCESS_TOKEN=your-token
  databricks-mcp-server
  
  # Run with custom config file
  databricks-mcp-server --config /path/to/config.yaml
  
  # Run with debug logging
  databricks-mcp-server --log-level DEBUG
        """
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file (YAML format)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="databricks-mcp-server 1.0.0"
    )
    
    return parser.parse_args()


async def run_server(config: ServerConfig) -> None:
    """
    Run the MCP server with the given configuration.
    
    Args:
        config: Server configuration object
    """
    server = None
    try:
        # Create and initialize the server
        server = DatabricksMCPServer(config.databricks.__dict__)
        
        # Set up signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logging.info(f"Received signal {signum}, initiating graceful shutdown...")
            if server:
                # Create a new event loop task to handle shutdown
                asyncio.create_task(server.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logging.info("Starting Databricks MCP Server...")
        logging.info(f"Connected to: {config.databricks.server_hostname}")
        logging.info(f"Catalog: {config.databricks.catalog}, Schema: {config.databricks.schema}")
        
        # Start the server
        await server.start()
        
    except KeyboardInterrupt:
        logging.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logging.error(f"Server error: {e}")
        raise
    finally:
        if server:
            try:
                await server.stop()
            except Exception as e:
                logging.error(f"Error during server shutdown: {e}")


def detect_uvx_environment() -> None:
    """
    Detect and validate uvx environment setup.
    
    Raises:
        UvxEnvironmentError: If uvx environment issues are detected
    """
    try:
        # Check if we're running in a uvx environment
        virtual_env = os.getenv('VIRTUAL_ENV')
        if virtual_env and 'uvx' in virtual_env:
            logging.debug(f"Running in uvx environment: {virtual_env}")
            
            # Check Python version compatibility
            import sys
            if sys.version_info < (3, 8):
                raise ErrorHandler.create_uvx_error(
                    details=f"Python {sys.version} is not supported. Requires Python 3.8 or higher."
                )
        
        # Check if required packages are available
        try:
            import mcp
            import yaml
        except ImportError as e:
            raise ErrorHandler.create_dependency_error(
                details=f"Required package not found: {e}",
                original_error=e
            )
            
    except Exception as e:
        if isinstance(e, (UvxEnvironmentError, DependencyError)):
            raise
        else:
            raise ErrorHandler.create_uvx_error(
                details=f"Environment validation failed: {e}",
                original_error=e
            )


def main() -> None:
    """
    Main entry point for uvx execution.
    
    This function handles command-line arguments, configuration loading,
    server lifecycle management, and error handling.
    """
    try:
        # Detect and validate uvx environment
        detect_uvx_environment()
        
        # Parse command-line arguments
        args = parse_arguments()
        
        # Set up logging early (may be overridden by config)
        setup_logging(args.log_level)
        
        # Load configuration
        config_manager = ConfigManager()
        try:
            config = config_manager.create_server_config(args.config)
            
            # Override log level from command line if specified
            if args.log_level != "INFO":
                config.log_level = args.log_level
                
            # Reconfigure logging with final log level
            setup_logging(config.log_level)
            
        except ConfigurationError as e:
            print(f"Configuration Error: {e.message}", file=sys.stderr)
            print("\nTroubleshooting Guide:", file=sys.stderr)
            if e.troubleshooting_guide:
                print(e.troubleshooting_guide, file=sys.stderr)
            
            if e.suggested_actions:
                print("\nSuggested Actions:", file=sys.stderr)
                for i, action in enumerate(e.suggested_actions, 1):
                    print(f"  {i}. {action}", file=sys.stderr)
            
            print("\nUse --help for more configuration examples.", file=sys.stderr)
            sys.exit(1)
        
        # Run the server
        try:
            asyncio.run(run_server(config))
        except KeyboardInterrupt:
            logging.info("Server stopped by user")
            sys.exit(0)
        except MCPServerError as e:
            log_structured_error(e)
            print(f"\nServer Error: {e.message}", file=sys.stderr)
            if e.troubleshooting_guide:
                print(f"\nTroubleshooting: {e.troubleshooting_guide}", file=sys.stderr)
            if e.suggested_actions:
                print("\nSuggested Actions:", file=sys.stderr)
                for i, action in enumerate(e.suggested_actions, 1):
                    print(f"  {i}. {action}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            # Convert unexpected errors to structured errors
            structured_error = ErrorHandler.handle_exception(e, "server startup")
            log_structured_error(structured_error)
            print(f"\nUnexpected Error: {structured_error.message}", file=sys.stderr)
            if structured_error.suggested_actions:
                print("\nSuggested Actions:", file=sys.stderr)
                for i, action in enumerate(structured_error.suggested_actions, 1):
                    print(f"  {i}. {action}", file=sys.stderr)
            sys.exit(1)
            
    except Exception as e:
        # Handle any unexpected errors at the top level
        structured_error = ErrorHandler.handle_exception(e, "application startup")
        log_structured_error(structured_error)
        
        print(f"Critical Error: {structured_error.message}", file=sys.stderr)
        if structured_error.troubleshooting_guide:
            print(f"\nTroubleshooting: {structured_error.troubleshooting_guide}", file=sys.stderr)
        if structured_error.suggested_actions:
            print("\nSuggested Actions:", file=sys.stderr)
            for i, action in enumerate(structured_error.suggested_actions, 1):
                print(f"  {i}. {action}", file=sys.stderr)
        
        # Also print traceback for debugging
        import traceback
        logging.debug("Full traceback:", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()