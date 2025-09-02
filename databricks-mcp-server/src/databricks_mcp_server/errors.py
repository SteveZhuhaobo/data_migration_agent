"""
Comprehensive error handling for the Databricks MCP Server.

This module provides structured error handling with clear messages and actionable solutions
for configuration, connection, and uvx-specific issues.
"""

import logging
from typing import Dict, Optional, Any
from enum import Enum


logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Categories of errors that can occur in the MCP server."""
    CONFIGURATION = "configuration"
    CONNECTION = "connection"
    AUTHENTICATION = "authentication"
    UVX_ENVIRONMENT = "uvx_environment"
    DATABRICKS_API = "databricks_api"
    WAREHOUSE = "warehouse"
    DEPENDENCY = "dependency"
    RUNTIME = "runtime"


class MCPServerError(Exception):
    """Base exception class for MCP server errors with structured information."""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory,
        error_code: str,
        troubleshooting_guide: Optional[str] = None,
        suggested_actions: Optional[list] = None,
        original_error: Optional[Exception] = None
    ):
        """
        Initialize MCP server error.
        
        Args:
            message: Human-readable error message
            category: Error category for classification
            error_code: Unique error code for identification
            troubleshooting_guide: Detailed troubleshooting information
            suggested_actions: List of suggested actions to resolve the issue
            original_error: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.category = category
        self.error_code = error_code
        self.troubleshooting_guide = troubleshooting_guide
        self.suggested_actions = suggested_actions or []
        self.original_error = original_error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for JSON serialization."""
        return {
            "error": True,
            "error_code": self.error_code,
            "category": self.category.value,
            "message": self.message,
            "troubleshooting_guide": self.troubleshooting_guide,
            "suggested_actions": self.suggested_actions,
            "original_error": str(self.original_error) if self.original_error else None
        }


class ConfigurationError(MCPServerError):
    """Raised when configuration is invalid or missing required values."""
    
    def __init__(self, message: str, error_code: str = "CONFIG_001", **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.CONFIGURATION,
            error_code=error_code,
            **kwargs
        )


class ConnectionError(MCPServerError):
    """Raised when connection to Databricks fails."""
    
    def __init__(self, message: str, error_code: str = "CONN_001", **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.CONNECTION,
            error_code=error_code,
            **kwargs
        )


class AuthenticationError(MCPServerError):
    """Raised when authentication with Databricks fails."""
    
    def __init__(self, message: str, error_code: str = "AUTH_001", **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.AUTHENTICATION,
            error_code=error_code,
            **kwargs
        )


class UvxEnvironmentError(MCPServerError):
    """Raised when uvx environment issues are detected."""
    
    def __init__(self, message: str, error_code: str = "UVX_001", **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.UVX_ENVIRONMENT,
            error_code=error_code,
            **kwargs
        )


class WarehouseError(MCPServerError):
    """Raised when warehouse-related issues occur."""
    
    def __init__(self, message: str, error_code: str = "WAREHOUSE_001", **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.WAREHOUSE,
            error_code=error_code,
            **kwargs
        )


class DependencyError(MCPServerError):
    """Raised when required dependencies are missing or incompatible."""
    
    def __init__(self, message: str, error_code: str = "DEP_001", **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.DEPENDENCY,
            error_code=error_code,
            **kwargs
        )


class ErrorHandler:
    """Centralized error handling with structured error messages and troubleshooting guidance."""
    
    # Error message templates with troubleshooting guidance
    ERROR_TEMPLATES = {
        # Configuration Errors
        "CONFIG_001": {
            "message": "Missing required configuration: {field}",
            "troubleshooting": """
This error occurs when a required configuration field is missing.

The Databricks MCP server requires the following configuration:
- server_hostname: Your Databricks workspace hostname
- http_path: The HTTP path to your SQL warehouse
- access_token: Your Databricks personal access token

You can provide these values through:
1. Environment variables (recommended for security)
2. Configuration file (config.yaml)
3. Command-line arguments
            """,
            "actions": [
                "Set the missing environment variable: export DATABRICKS_{field}=your_value",
                "Add the field to your config.yaml file",
                "Check the documentation for configuration examples",
                "Verify your Databricks workspace settings"
            ]
        },
        
        "CONFIG_002": {
            "message": "Invalid configuration format: {details}",
            "troubleshooting": """
The configuration format is invalid. Common issues include:
- Invalid YAML syntax in config file
- Incorrect hostname format (should not include https://)
- Invalid http_path format (must start with /)
- Invalid timeout value (must be positive integer)
            """,
            "actions": [
                "Check YAML syntax in your config file",
                "Ensure server_hostname doesn't include protocol (https://)",
                "Verify http_path starts with '/'",
                "Confirm timeout is a positive integer",
                "Use the provided config.yaml.example as a template"
            ]
        },
        
        # Connection Errors
        "CONN_001": {
            "message": "Failed to connect to Databricks: {details}",
            "troubleshooting": """
Connection to Databricks failed. This can happen due to:
- Network connectivity issues
- Incorrect server hostname
- Firewall or proxy blocking the connection
- Databricks workspace being unavailable
            """,
            "actions": [
                "Verify your internet connection",
                "Check the server_hostname is correct",
                "Test connectivity: ping your-workspace.cloud.databricks.com",
                "Check if your organization uses a proxy or firewall",
                "Verify the Databricks workspace is accessible via browser"
            ]
        },
        
        "CONN_002": {
            "message": "Connection timeout: {details}",
            "troubleshooting": """
The connection to Databricks timed out. This often happens with:
- Serverless warehouses that need to cold start
- Network latency issues
- Overloaded warehouses
            """,
            "actions": [
                "Wait a few minutes and try again (serverless warehouse cold start)",
                "Increase the timeout value in configuration",
                "Check warehouse status in Databricks UI",
                "Consider using a different warehouse",
                "Verify network stability"
            ]
        },
        
        # Authentication Errors
        "AUTH_001": {
            "message": "Authentication failed: {details}",
            "troubleshooting": """
Authentication with Databricks failed. Common causes:
- Invalid or expired access token
- Insufficient permissions
- Token not associated with the workspace
            """,
            "actions": [
                "Generate a new personal access token in Databricks",
                "Verify the token has the required permissions",
                "Check the token is for the correct workspace",
                "Ensure the token hasn't expired",
                "Test the token using Databricks CLI or API"
            ]
        },
        
        "AUTH_002": {
            "message": "Insufficient permissions: {details}",
            "troubleshooting": """
Your access token doesn't have sufficient permissions for the requested operation.
Required permissions may include:
- SQL warehouse access
- Catalog and schema permissions
- Cluster access (if using clusters)
            """,
            "actions": [
                "Contact your Databricks administrator",
                "Request additional permissions for your user account",
                "Verify workspace-level permissions",
                "Check catalog and schema access rights",
                "Use a token with admin privileges for testing"
            ]
        },
        
        # UVX Environment Errors
        "UVX_001": {
            "message": "UVX environment issue: {details}",
            "troubleshooting": """
There's an issue with the uvx environment. This can happen when:
- uvx is not properly installed
- Python version incompatibility
- Package installation conflicts
- Isolated environment corruption
            """,
            "actions": [
                "Verify uvx is installed: uvx --version",
                "Update uvx to the latest version",
                "Check Python version compatibility (>=3.8 required)",
                "Clear uvx cache: uvx cache clear",
                "Reinstall the package: uvx --force databricks-mcp-server"
            ]
        },
        
        "UVX_002": {
            "message": "Package installation failed: {details}",
            "troubleshooting": """
The package failed to install via uvx. Common causes:
- Network connectivity issues
- Package repository unavailable
- Dependency conflicts
- Insufficient disk space
            """,
            "actions": [
                "Check internet connectivity",
                "Try installing with --force flag",
                "Clear uvx cache and retry",
                "Check available disk space",
                "Try installing from a different network"
            ]
        },
        
        # Warehouse Errors
        "WAREHOUSE_001": {
            "message": "Warehouse unavailable: {details}",
            "troubleshooting": """
The SQL warehouse is not available. This can happen when:
- Warehouse is stopped or stopping
- Warehouse is starting up (cold start)
- Warehouse configuration issues
- Insufficient compute resources
            """,
            "actions": [
                "Check warehouse status in Databricks UI",
                "Wait for warehouse to start (can take 2-3 minutes)",
                "Try starting the warehouse manually",
                "Use a different warehouse if available",
                "Contact your Databricks administrator"
            ]
        },
        
        # Dependency Errors
        "DEP_001": {
            "message": "Missing dependency: {details}",
            "troubleshooting": """
A required Python package is missing or incompatible.
This shouldn't happen with uvx installations but can occur in development.
            """,
            "actions": [
                "Reinstall using uvx (recommended)",
                "If developing locally, install dependencies: pip install -r requirements.txt",
                "Check Python version compatibility",
                "Verify package versions match requirements"
            ]
        }
    }
    
    @classmethod
    def create_configuration_error(
        cls,
        field: str,
        details: Optional[str] = None,
        original_error: Optional[Exception] = None
    ) -> ConfigurationError:
        """Create a configuration error with structured information."""
        template = cls.ERROR_TEMPLATES["CONFIG_001"]
        message = template["message"].format(field=field.upper())
        
        if details:
            message += f": {details}"
        
        actions = [action.format(field=field.upper()) for action in template["actions"]]
        
        return ConfigurationError(
            message=message,
            error_code="CONFIG_001",
            troubleshooting_guide=template["troubleshooting"],
            suggested_actions=actions,
            original_error=original_error
        )
    
    @classmethod
    def create_connection_error(
        cls,
        details: str,
        timeout: bool = False,
        original_error: Optional[Exception] = None
    ) -> ConnectionError:
        """Create a connection error with appropriate troubleshooting."""
        error_code = "CONN_002" if timeout else "CONN_001"
        template = cls.ERROR_TEMPLATES[error_code]
        message = template["message"].format(details=details)
        
        return ConnectionError(
            message=message,
            error_code=error_code,
            troubleshooting_guide=template["troubleshooting"],
            suggested_actions=template["actions"],
            original_error=original_error
        )
    
    @classmethod
    def create_authentication_error(
        cls,
        details: str,
        insufficient_permissions: bool = False,
        original_error: Optional[Exception] = None
    ) -> AuthenticationError:
        """Create an authentication error with troubleshooting guidance."""
        error_code = "AUTH_002" if insufficient_permissions else "AUTH_001"
        template = cls.ERROR_TEMPLATES[error_code]
        message = template["message"].format(details=details)
        
        return AuthenticationError(
            message=message,
            error_code=error_code,
            troubleshooting_guide=template["troubleshooting"],
            suggested_actions=template["actions"],
            original_error=original_error
        )
    
    @classmethod
    def create_uvx_error(
        cls,
        details: str,
        installation_failed: bool = False,
        original_error: Optional[Exception] = None
    ) -> UvxEnvironmentError:
        """Create a uvx environment error with troubleshooting guidance."""
        error_code = "UVX_002" if installation_failed else "UVX_001"
        template = cls.ERROR_TEMPLATES[error_code]
        message = template["message"].format(details=details)
        
        return UvxEnvironmentError(
            message=message,
            error_code=error_code,
            troubleshooting_guide=template["troubleshooting"],
            suggested_actions=template["actions"],
            original_error=original_error
        )
    
    @classmethod
    def create_warehouse_error(
        cls,
        details: str,
        original_error: Optional[Exception] = None
    ) -> WarehouseError:
        """Create a warehouse error with troubleshooting guidance."""
        template = cls.ERROR_TEMPLATES["WAREHOUSE_001"]
        message = template["message"].format(details=details)
        
        return WarehouseError(
            message=message,
            error_code="WAREHOUSE_001",
            troubleshooting_guide=template["troubleshooting"],
            suggested_actions=template["actions"],
            original_error=original_error
        )
    
    @classmethod
    def create_dependency_error(
        cls,
        details: str,
        original_error: Optional[Exception] = None
    ) -> DependencyError:
        """Create a dependency error with troubleshooting guidance."""
        template = cls.ERROR_TEMPLATES["DEP_001"]
        message = template["message"].format(details=details)
        
        return DependencyError(
            message=message,
            error_code="DEP_001",
            troubleshooting_guide=template["troubleshooting"],
            suggested_actions=template["actions"],
            original_error=original_error
        )
    
    @classmethod
    def handle_exception(cls, exception: Exception, context: str = "") -> MCPServerError:
        """
        Convert a generic exception to a structured MCP server error.
        
        Args:
            exception: The original exception
            context: Additional context about where the error occurred
            
        Returns:
            Structured MCP server error
        """
        error_str = str(exception).lower()
        
        # Analyze the exception to determine the appropriate error type
        if "authentication" in error_str or "unauthorized" in error_str or "401" in error_str:
            return cls.create_authentication_error(
                details=str(exception),
                original_error=exception
            )
        
        elif "permission" in error_str or "forbidden" in error_str or "403" in error_str:
            return cls.create_authentication_error(
                details=str(exception),
                insufficient_permissions=True,
                original_error=exception
            )
        
        elif "timeout" in error_str or "timed out" in error_str:
            return cls.create_connection_error(
                details=str(exception),
                timeout=True,
                original_error=exception
            )
        
        elif "connection" in error_str or "network" in error_str or "dns" in error_str:
            return cls.create_connection_error(
                details=str(exception),
                original_error=exception
            )
        
        elif "warehouse" in error_str or "cluster" in error_str:
            return cls.create_warehouse_error(
                details=str(exception),
                original_error=exception
            )
        
        elif "import" in error_str or "module" in error_str or "package" in error_str:
            return cls.create_dependency_error(
                details=str(exception),
                original_error=exception
            )
        
        elif "uvx" in error_str or "uv" in error_str:
            return cls.create_uvx_error(
                details=str(exception),
                original_error=exception
            )
        
        else:
            # Generic runtime error
            return MCPServerError(
                message=f"Runtime error{': ' + context if context else ''}: {str(exception)}",
                category=ErrorCategory.RUNTIME,
                error_code="RUNTIME_001",
                troubleshooting_guide="An unexpected error occurred. Check the logs for more details.",
                suggested_actions=[
                    "Check the server logs for more information",
                    "Verify your configuration is correct",
                    "Try restarting the server",
                    "Report this issue if it persists"
                ],
                original_error=exception
            )


def log_structured_error(error: MCPServerError, logger_instance: Optional[logging.Logger] = None) -> None:
    """
    Log a structured error with full troubleshooting information.
    
    Args:
        error: The structured error to log
        logger_instance: Optional logger instance to use
    """
    log = logger_instance or logger
    
    log.error(f"[{error.error_code}] {error.message}")
    
    if error.troubleshooting_guide:
        log.info(f"Troubleshooting guide: {error.troubleshooting_guide}")
    
    if error.suggested_actions:
        log.info("Suggested actions:")
        for i, action in enumerate(error.suggested_actions, 1):
            log.info(f"  {i}. {action}")
    
    if error.original_error:
        log.debug(f"Original error: {error.original_error}")