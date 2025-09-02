"""
Tests for comprehensive error handling in the Databricks MCP Server.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock

from databricks_mcp_server.errors import (
    ErrorHandler, MCPServerError, ConfigurationError, ConnectionError,
    AuthenticationError, UvxEnvironmentError, WarehouseError, DependencyError,
    ErrorCategory
)
from databricks_mcp_server.server import ConnectionManager, QueryExecutor


class TestErrorHandler:
    """Test the ErrorHandler class and error creation methods."""
    
    def test_create_configuration_error(self):
        """Test configuration error creation."""
        error = ErrorHandler.create_configuration_error(
            field="server_hostname",
            details="Missing hostname"
        )
        
        assert isinstance(error, ConfigurationError)
        assert error.category == ErrorCategory.CONFIGURATION
        assert error.error_code == "CONFIG_001"
        assert "SERVER_HOSTNAME" in error.message
        assert error.suggested_actions is not None
        assert len(error.suggested_actions) > 0
    
    def test_create_connection_error(self):
        """Test connection error creation."""
        error = ErrorHandler.create_connection_error(
            details="Connection failed",
            timeout=True
        )
        
        assert isinstance(error, ConnectionError)
        assert error.category == ErrorCategory.CONNECTION
        assert error.error_code == "CONN_002"  # timeout error
        assert "Connection failed" in error.message
    
    def test_create_authentication_error(self):
        """Test authentication error creation."""
        error = ErrorHandler.create_authentication_error(
            details="Invalid token",
            insufficient_permissions=False
        )
        
        assert isinstance(error, AuthenticationError)
        assert error.category == ErrorCategory.AUTHENTICATION
        assert error.error_code == "AUTH_001"
        assert "Invalid token" in error.message
    
    def test_create_uvx_error(self):
        """Test uvx environment error creation."""
        error = ErrorHandler.create_uvx_error(
            details="Package installation failed",
            installation_failed=True
        )
        
        assert isinstance(error, UvxEnvironmentError)
        assert error.category == ErrorCategory.UVX_ENVIRONMENT
        assert error.error_code == "UVX_002"  # installation failed
        assert "Package installation failed" in error.message
    
    def test_create_warehouse_error(self):
        """Test warehouse error creation."""
        error = ErrorHandler.create_warehouse_error(
            details="Warehouse is stopped"
        )
        
        assert isinstance(error, WarehouseError)
        assert error.category == ErrorCategory.WAREHOUSE
        assert error.error_code == "WAREHOUSE_001"
        assert "Warehouse is stopped" in error.message
    
    def test_create_dependency_error(self):
        """Test dependency error creation."""
        error = ErrorHandler.create_dependency_error(
            details="Missing package: databricks-sql-connector"
        )
        
        assert isinstance(error, DependencyError)
        assert error.category == ErrorCategory.DEPENDENCY
        assert error.error_code == "DEP_001"
        assert "Missing package" in error.message
    
    def test_handle_exception_authentication(self):
        """Test exception handling for authentication errors."""
        original_error = Exception("401 Unauthorized")
        
        structured_error = ErrorHandler.handle_exception(original_error, "test context")
        
        assert isinstance(structured_error, AuthenticationError)
        assert structured_error.original_error == original_error
    
    def test_handle_exception_timeout(self):
        """Test exception handling for timeout errors."""
        original_error = Exception("Connection timed out")
        
        structured_error = ErrorHandler.handle_exception(original_error, "test context")
        
        assert isinstance(structured_error, ConnectionError)
        assert structured_error.original_error == original_error
    
    def test_handle_exception_generic(self):
        """Test exception handling for generic errors."""
        original_error = Exception("Some unexpected error")
        
        structured_error = ErrorHandler.handle_exception(original_error, "test context")
        
        assert isinstance(structured_error, MCPServerError)
        assert structured_error.category == ErrorCategory.RUNTIME
        assert structured_error.original_error == original_error


class TestMCPServerError:
    """Test the MCPServerError base class."""
    
    def test_to_dict(self):
        """Test error serialization to dictionary."""
        error = MCPServerError(
            message="Test error",
            category=ErrorCategory.CONFIGURATION,
            error_code="TEST_001",
            troubleshooting_guide="Test guide",
            suggested_actions=["Action 1", "Action 2"],
            original_error=Exception("Original")
        )
        
        error_dict = error.to_dict()
        
        assert error_dict["error"] is True
        assert error_dict["error_code"] == "TEST_001"
        assert error_dict["category"] == "configuration"
        assert error_dict["message"] == "Test error"
        assert error_dict["troubleshooting_guide"] == "Test guide"
        assert error_dict["suggested_actions"] == ["Action 1", "Action 2"]
        assert "Original" in error_dict["original_error"]


class TestConnectionManagerErrorHandling:
    """Test error handling in ConnectionManager."""
    
    def test_validate_connection_missing_hostname(self):
        """Test validation with missing hostname."""
        config = {"http_path": "/test", "access_token": "test_token"}
        manager = ConnectionManager(config)
        
        with pytest.raises(ConfigurationError) as exc_info:
            manager.validate_connection()
        
        error = exc_info.value
        assert error.category == ErrorCategory.CONFIGURATION
        assert "SERVER_HOSTNAME" in error.message
    
    def test_validate_connection_invalid_http_path(self):
        """Test validation with invalid http_path."""
        config = {
            "server_hostname": "test.databricks.com",
            "http_path": "invalid_path",  # Should start with /
            "access_token": "test_token"
        }
        manager = ConnectionManager(config)
        
        with pytest.raises(ConfigurationError) as exc_info:
            manager.validate_connection()
        
        error = exc_info.value
        assert error.category == ErrorCategory.CONFIGURATION
        assert "http_path" in error.message
    
    def test_validate_connection_missing_token(self):
        """Test validation with missing access token."""
        config = {
            "server_hostname": "test.databricks.com",
            "http_path": "/test"
        }
        manager = ConnectionManager(config)
        
        with pytest.raises(ConfigurationError) as exc_info:
            manager.validate_connection()
        
        error = exc_info.value
        assert error.category == ErrorCategory.CONFIGURATION
        assert "ACCESS_TOKEN" in error.message
    
    @patch('builtins.__import__')
    def test_get_sql_connection_import_error(self, mock_import):
        """Test SQL connection with import error."""
        # Simulate ImportError for databricks module
        def mock_import_func(name, *args, **kwargs):
            if name == 'databricks':
                raise ImportError("No module named 'databricks'")
            return __import__(name, *args, **kwargs)
        
        mock_import.side_effect = mock_import_func
        
        config = {
            "server_hostname": "test.databricks.com",
            "http_path": "/test",
            "access_token": "test_token"
        }
        manager = ConnectionManager(config)
        
        with pytest.raises(DependencyError) as exc_info:
            manager.get_sql_connection()
        
        error = exc_info.value
        assert error.category == ErrorCategory.DEPENDENCY
        assert "databricks-sql-connector" in error.message
    
    @patch('databricks_mcp_server.server.requests.Session')
    def test_get_rest_client_timeout(self, mock_session_class):
        """Test REST client with timeout error."""
        import requests
        
        # Mock session and timeout
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_session.get.side_effect = requests.exceptions.Timeout("Request timed out")
        
        config = {
            "server_hostname": "test.databricks.com",
            "http_path": "/test",
            "access_token": "test_token"
        }
        manager = ConnectionManager(config)
        
        with pytest.raises(ConnectionError) as exc_info:
            manager.get_rest_client()
        
        error = exc_info.value
        assert error.category == ErrorCategory.CONNECTION
        assert "timeout" in error.message.lower()
    
    @patch('databricks_mcp_server.server.requests.Session')
    def test_get_rest_client_authentication_error(self, mock_session_class):
        """Test REST client with authentication error."""
        # Mock session and 401 response
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 401
        mock_session.get.return_value = mock_response
        
        config = {
            "server_hostname": "test.databricks.com",
            "http_path": "/test",
            "access_token": "invalid_token"
        }
        manager = ConnectionManager(config)
        
        with pytest.raises(AuthenticationError) as exc_info:
            manager.get_rest_client()
        
        error = exc_info.value
        assert error.category == ErrorCategory.AUTHENTICATION
        assert error.error_code == "AUTH_001"


class TestQueryExecutorErrorHandling:
    """Test error handling in QueryExecutor."""
    
    def test_execute_query_warehouse_error(self):
        """Test query execution with warehouse error."""
        # Mock connection manager
        mock_connection_manager = Mock()
        mock_connection_manager.check_warehouse_status.return_value = (False, "Warehouse stopped")
        
        executor = QueryExecutor(mock_connection_manager)
        
        # Execute query (this should be async, but for testing we'll call it directly)
        import asyncio
        result = asyncio.run(executor.execute_query("SELECT 1"))
        
        # Parse the JSON result
        result_dict = json.loads(result)
        
        assert result_dict["error"] is True
        assert result_dict["category"] == "warehouse"
        assert "Warehouse stopped" in result_dict["message"]


class TestStructuredErrorResponses:
    """Test that structured errors are properly formatted for JSON responses."""
    
    def test_error_json_serialization(self):
        """Test that errors can be serialized to JSON properly."""
        error = ErrorHandler.create_configuration_error(
            field="test_field",
            details="Test details"
        )
        
        # Convert to dict and then to JSON
        error_dict = error.to_dict()
        json_str = json.dumps(error_dict, indent=2)
        
        # Parse back to verify it's valid JSON
        parsed = json.loads(json_str)
        
        assert parsed["error"] is True
        assert parsed["error_code"] == "CONFIG_001"
        assert parsed["category"] == "configuration"
        assert "TEST_FIELD" in parsed["message"]
        assert isinstance(parsed["suggested_actions"], list)
        assert len(parsed["suggested_actions"]) > 0
    
    def test_error_with_original_exception(self):
        """Test error serialization with original exception."""
        original = ValueError("Original error message")
        
        error = ErrorHandler.create_connection_error(
            details="Connection failed",
            original_error=original
        )
        
        error_dict = error.to_dict()
        
        assert error_dict["original_error"] == "Original error message"
    
    def test_error_without_optional_fields(self):
        """Test error serialization without optional fields."""
        error = MCPServerError(
            message="Simple error",
            category=ErrorCategory.RUNTIME,
            error_code="SIMPLE_001"
        )
        
        error_dict = error.to_dict()
        
        assert error_dict["troubleshooting_guide"] is None
        assert error_dict["suggested_actions"] == []
        assert error_dict["original_error"] is None


if __name__ == "__main__":
    pytest.main([__file__])