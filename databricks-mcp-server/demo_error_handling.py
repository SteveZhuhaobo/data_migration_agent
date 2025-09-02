#!/usr/bin/env python3
"""
Demonstration script for comprehensive error handling in Databricks MCP Server.

This script shows how different types of errors are handled with structured
error messages and troubleshooting guidance.
"""

import json
import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from databricks_mcp_server.errors import ErrorHandler, log_structured_error
from databricks_mcp_server.config import ConfigManager
from databricks_mcp_server.server import ConnectionManager


def demo_configuration_errors():
    """Demonstrate configuration error handling."""
    print("=" * 60)
    print("CONFIGURATION ERROR HANDLING DEMO")
    print("=" * 60)
    
    # Test 1: Missing configuration file
    print("\n1. Missing configuration file:")
    try:
        config_manager = ConfigManager()
        config_manager.load_config('/nonexistent/config.yaml')
    except Exception as e:
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Code: {e.error_code}")
        print(f"Message: {e.message}")
        print(f"Category: {e.category.value}")
        if e.suggested_actions:
            print("Suggested Actions:")
            for i, action in enumerate(e.suggested_actions, 1):
                print(f"  {i}. {action}")
    
    # Test 2: Missing required fields
    print("\n2. Missing required configuration fields:")
    try:
        config_manager = ConfigManager()
        config_manager.validate_config({})
    except Exception as e:
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Code: {e.error_code}")
        print(f"Message: {e.message}")
        if e.suggested_actions:
            print("Suggested Actions:")
            for i, action in enumerate(e.suggested_actions[:3], 1):  # Show first 3
                print(f"  {i}. {action}")


def demo_connection_errors():
    """Demonstrate connection error handling."""
    print("\n" + "=" * 60)
    print("CONNECTION ERROR HANDLING DEMO")
    print("=" * 60)
    
    # Test 1: Invalid configuration
    print("\n1. Invalid server hostname:")
    try:
        config = {"http_path": "/test", "access_token": "test_token"}
        manager = ConnectionManager(config)
        manager.validate_connection()
    except Exception as e:
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Code: {e.error_code}")
        print(f"Message: {e.message}")
        if e.suggested_actions:
            print("Suggested Actions:")
            for i, action in enumerate(e.suggested_actions[:3], 1):
                print(f"  {i}. {action}")
    
    # Test 2: Invalid http_path
    print("\n2. Invalid http_path format:")
    try:
        config = {
            "server_hostname": "test.databricks.com",
            "http_path": "invalid_path",  # Should start with /
            "access_token": "test_token"
        }
        manager = ConnectionManager(config)
        manager.validate_connection()
    except Exception as e:
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Code: {e.error_code}")
        print(f"Message: {e.message}")


def demo_structured_error_responses():
    """Demonstrate structured error responses for JSON APIs."""
    print("\n" + "=" * 60)
    print("STRUCTURED ERROR RESPONSES DEMO")
    print("=" * 60)
    
    # Create different types of errors and show their JSON representation
    errors = [
        ErrorHandler.create_configuration_error(
            field="server_hostname",
            details="Missing required hostname"
        ),
        ErrorHandler.create_connection_error(
            details="Connection timeout after 30 seconds",
            timeout=True
        ),
        ErrorHandler.create_authentication_error(
            details="Invalid access token provided"
        ),
        ErrorHandler.create_warehouse_error(
            details="Serverless warehouse is starting up"
        ),
        ErrorHandler.create_uvx_error(
            details="Package installation failed due to network issues",
            installation_failed=True
        )
    ]
    
    for i, error in enumerate(errors, 1):
        print(f"\n{i}. {error.__class__.__name__} JSON Response:")
        error_dict = error.to_dict()
        print(json.dumps(error_dict, indent=2))


def demo_exception_handling():
    """Demonstrate automatic exception conversion to structured errors."""
    print("\n" + "=" * 60)
    print("AUTOMATIC EXCEPTION HANDLING DEMO")
    print("=" * 60)
    
    # Test different types of exceptions
    test_exceptions = [
        Exception("401 Unauthorized - Invalid token"),
        Exception("Connection timed out after 30 seconds"),
        Exception("403 Forbidden - Insufficient permissions"),
        Exception("Warehouse cluster-12345 is not available"),
        Exception("ImportError: No module named 'databricks'"),
        Exception("Some unexpected runtime error")
    ]
    
    for i, exc in enumerate(test_exceptions, 1):
        print(f"\n{i}. Original Exception: {exc}")
        structured_error = ErrorHandler.handle_exception(exc, "demo context")
        print(f"   Converted to: {structured_error.__class__.__name__}")
        print(f"   Category: {structured_error.category.value}")
        print(f"   Error Code: {structured_error.error_code}")
        print(f"   Message: {structured_error.message}")


def main():
    """Run all error handling demonstrations."""
    print("DATABRICKS MCP SERVER - ERROR HANDLING DEMONSTRATION")
    print("This demo shows comprehensive error handling with structured messages")
    print("and actionable troubleshooting guidance.")
    
    try:
        demo_configuration_errors()
        demo_connection_errors()
        demo_structured_error_responses()
        demo_exception_handling()
        
        print("\n" + "=" * 60)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("\nKey Features Demonstrated:")
        print("✓ Structured error messages with error codes")
        print("✓ Categorized errors for better handling")
        print("✓ Actionable troubleshooting guidance")
        print("✓ JSON-serializable error responses")
        print("✓ Automatic exception conversion")
        print("✓ UVX-specific error handling")
        print("✓ Configuration validation with clear messages")
        print("✓ Connection and authentication error handling")
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()