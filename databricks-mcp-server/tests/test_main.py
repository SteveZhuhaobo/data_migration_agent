"""
Unit tests for the main entry point functionality.

Tests command-line argument parsing, configuration loading, server lifecycle,
and error handling in the main entry point.
"""

import argparse
import os
import pytest
import sys
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from io import StringIO

from databricks_mcp_server.main import (
    main, parse_arguments, setup_logging, run_server, detect_uvx_environment
)
from databricks_mcp_server.config import ServerConfig, DatabricksConfig
from databricks_mcp_server.errors import (
    ConfigurationError, UvxEnvironmentError, DependencyError, MCPServerError
)


class TestParseArguments:
    """Test cases for command-line argument parsing."""
    
    def test_parse_arguments_defaults(self):
        """Test argument parsing with default values."""
        with patch('sys.argv', ['databricks-mcp-server']):
            args = parse_arguments()
            assert args.config is None
            assert args.log_level == 'INFO'
    
    def test_parse_arguments_with_config(self):
        """Test argument parsing with config file specified."""
        with patch('sys.argv', ['databricks-mcp-server', '--config', '/path/to/config.yaml']):
            args = parse_arguments()
            assert args.config == '/path/to/config.yaml'
            assert args.log_level == 'INFO'
    
    def test_parse_arguments_with_log_level(self):
        """Test argument parsing with log level specified."""
        with patch('sys.argv', ['databricks-mcp-server', '--log-level', 'DEBUG']):
            args = parse_arguments()
            assert args.config is None
            assert args.log_level == 'DEBUG'
    
    def test_parse_arguments_all_options(self):
        """Test argument parsing with all options specified."""
        with patch('sys.argv', [
            'databricks-mcp-server', 
            '--config', '/custom/config.yaml',
            '--log-level', 'WARNING'
        ]):
            args = parse_arguments()
            assert args.config == '/custom/config.yaml'
            assert args.log_level == 'WARNING'
    
    def test_parse_arguments_invalid_log_level(self):
        """Test argument parsing with invalid log level."""
        with patch('sys.argv', ['databricks-mcp-server', '--log-level', 'INVALID']):
            with pytest.raises(SystemExit):
                parse_arguments()
    
    def test_parse_arguments_version(self):
        """Test version argument."""
        with patch('sys.argv', ['databricks-mcp-server', '--version']):
            with pytest.raises(SystemExit) as exc_info:
                parse_arguments()
            assert exc_info.value.code == 0
    
    def test_parse_arguments_help(self):
        """Test help argument."""
        with patch('sys.argv', ['databricks-mcp-server', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                parse_arguments()
            assert exc_info.value.code == 0


class TestSetupLogging:
    """Test cases for logging setup."""
    
    @patch('databricks_mcp_server.main.logging.basicConfig')
    def test_setup_logging_default(self, mock_basic_config):
        """Test logging setup with default level."""
        setup_logging()
        mock_basic_config.assert_called_once()
        call_args = mock_basic_config.call_args
        assert call_args[1]['level'] == 20  # INFO level
        assert call_args[1]['stream'] == sys.stderr
    
    @patch('databricks_mcp_server.main.logging.basicConfig')
    def test_setup_logging_debug(self, mock_basic_config):
        """Test logging setup with DEBUG level."""
        setup_logging('DEBUG')
        mock_basic_config.assert_called_once()
        call_args = mock_basic_config.call_args
        assert call_args[1]['level'] == 10  # DEBUG level
    
    @patch('databricks_mcp_server.main.logging.basicConfig')
    def test_setup_logging_error(self, mock_basic_config):
        """Test logging setup with ERROR level."""
        setup_logging('ERROR')
        mock_basic_config.assert_called_once()
        call_args = mock_basic_config.call_args
        assert call_args[1]['level'] == 40  # ERROR level


class TestDetectUvxEnvironment:
    """Test cases for uvx environment detection."""
    
    @patch.dict(os.environ, {'VIRTUAL_ENV': '/path/to/uvx/env'})
    def test_detect_uvx_environment_success(self):
        """Test successful uvx environment detection."""
        with patch('sys.version_info', (3, 9, 0)):
            # Should not raise an exception
            detect_uvx_environment()
    
    @patch.dict(os.environ, {'VIRTUAL_ENV': '/path/to/uvx/env'})
    def test_detect_uvx_environment_old_python(self):
        """Test uvx environment detection with old Python version."""
        with patch('sys.version_info', (3, 7, 0)):
            with pytest.raises(UvxEnvironmentError) as exc_info:
                detect_uvx_environment()
            assert "Python" in str(exc_info.value)
            assert "Requires Python 3.8" in str(exc_info.value)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_detect_uvx_environment_no_uvx(self):
        """Test environment detection without uvx."""
        with patch('sys.version_info', (3, 9, 0)):
            # Should not raise an exception when not in uvx
            detect_uvx_environment()
    
    def test_detect_uvx_environment_missing_dependencies(self):
        """Test environment detection with missing dependencies."""
        with patch('builtins.__import__') as mock_import:
            def mock_import_func(name, *args, **kwargs):
                if name == 'mcp':
                    raise ImportError("No module named 'mcp'")
                return __import__(name, *args, **kwargs)
            
            mock_import.side_effect = mock_import_func
            
            with pytest.raises(DependencyError) as exc_info:
                detect_uvx_environment()
            assert "mcp" in str(exc_info.value)


class TestRunServer:
    """Test cases for server execution."""
    
    @pytest.mark.asyncio
    async def test_run_server_success(self):
        """Test successful server execution."""
        databricks_config = DatabricksConfig(
            server_hostname='test.databricks.com',
            http_path='/sql/1.0/warehouses/test',
            access_token='test-token'
        )
        config = ServerConfig(databricks=databricks_config)
        
        with patch('databricks_mcp_server.main.DatabricksMCPServer') as mock_server_class:
            mock_server = AsyncMock()
            mock_server_class.return_value = mock_server
            
            with patch('databricks_mcp_server.main.signal.signal'):
                await run_server(config)
            
            mock_server_class.assert_called_once()
            mock_server.start.assert_called_once()
            mock_server.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_server_keyboard_interrupt(self):
        """Test server execution with keyboard interrupt."""
        databricks_config = DatabricksConfig(
            server_hostname='test.databricks.com',
            http_path='/sql/1.0/warehouses/test',
            access_token='test-token'
        )
        config = ServerConfig(databricks=databricks_config)
        
        with patch('databricks_mcp_server.main.DatabricksMCPServer') as mock_server_class:
            mock_server = AsyncMock()
            mock_server.start.side_effect = KeyboardInterrupt()
            mock_server_class.return_value = mock_server
            
            with patch('databricks_mcp_server.main.signal.signal'):
                # Should not raise an exception
                await run_server(config)
            
            mock_server.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_server_exception(self):
        """Test server execution with exception."""
        databricks_config = DatabricksConfig(
            server_hostname='test.databricks.com',
            http_path='/sql/1.0/warehouses/test',
            access_token='test-token'
        )
        config = ServerConfig(databricks=databricks_config)
        
        with patch('databricks_mcp_server.main.DatabricksMCPServer') as mock_server_class:
            mock_server = AsyncMock()
            mock_server.start.side_effect = Exception("Server error")
            mock_server_class.return_value = mock_server
            
            with patch('databricks_mcp_server.main.signal.signal'):
                with pytest.raises(Exception, match="Server error"):
                    await run_server(config)
            
            mock_server.stop.assert_called_once()


class TestMainFunction:
    """Test cases for the main function."""
    
    @patch('databricks_mcp_server.main.detect_uvx_environment')
    @patch('databricks_mcp_server.main.parse_arguments')
    @patch('databricks_mcp_server.main.setup_logging')
    @patch('databricks_mcp_server.main.ConfigManager')
    @patch('databricks_mcp_server.main.asyncio.run')
    def test_main_success(self, mock_asyncio_run, mock_config_manager_class, 
                         mock_setup_logging, mock_parse_args, mock_detect_uvx):
        """Test successful main function execution."""
        # Mock arguments
        mock_args = Mock()
        mock_args.config = None
        mock_args.log_level = 'INFO'
        mock_parse_args.return_value = mock_args
        
        # Mock config manager
        mock_config_manager = Mock()
        databricks_config = DatabricksConfig(
            server_hostname='test.databricks.com',
            http_path='/sql/1.0/warehouses/test',
            access_token='test-token'
        )
        server_config = ServerConfig(databricks=databricks_config)
        mock_config_manager.create_server_config.return_value = server_config
        mock_config_manager_class.return_value = mock_config_manager
        
        main()
        
        mock_detect_uvx.assert_called_once()
        mock_parse_args.assert_called_once()
        mock_setup_logging.assert_called()
        mock_config_manager.create_server_config.assert_called_once()
        mock_asyncio_run.assert_called_once()
    
    @patch('databricks_mcp_server.main.detect_uvx_environment')
    @patch('databricks_mcp_server.main.parse_arguments')
    @patch('databricks_mcp_server.main.setup_logging')
    @patch('databricks_mcp_server.main.ConfigManager')
    @patch('sys.exit')
    def test_main_configuration_error(self, mock_exit, mock_config_manager_class,
                                    mock_setup_logging, mock_parse_args, mock_detect_uvx):
        """Test main function with configuration error."""
        # Mock arguments
        mock_args = Mock()
        mock_args.config = None
        mock_args.log_level = 'INFO'
        mock_parse_args.return_value = mock_args
        
        # Mock config manager to raise ConfigurationError
        mock_config_manager = Mock()
        config_error = ConfigurationError(
            message="Missing required configuration",
            error_code="CONFIG_001",
            troubleshooting_guide="Check your configuration",
            suggested_actions=["Set environment variables", "Create config file"]
        )
        mock_config_manager.create_server_config.side_effect = config_error
        mock_config_manager_class.return_value = mock_config_manager
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            main()
        
        mock_exit.assert_called_with(1)
        stderr_output = mock_stderr.getvalue()
        assert "Configuration Error" in stderr_output
        assert "Missing required configuration" in stderr_output
        assert "Troubleshooting Guide" in stderr_output
        assert "Suggested Actions" in stderr_output
    
    @patch('databricks_mcp_server.main.detect_uvx_environment')
    @patch('databricks_mcp_server.main.parse_arguments')
    @patch('databricks_mcp_server.main.setup_logging')
    @patch('databricks_mcp_server.main.ConfigManager')
    @patch('databricks_mcp_server.main.asyncio.run')
    @patch('sys.exit')
    def test_main_keyboard_interrupt(self, mock_exit, mock_asyncio_run, mock_config_manager_class,
                                   mock_setup_logging, mock_parse_args, mock_detect_uvx):
        """Test main function with keyboard interrupt."""
        # Mock arguments
        mock_args = Mock()
        mock_args.config = None
        mock_args.log_level = 'INFO'
        mock_parse_args.return_value = mock_args
        
        # Mock config manager
        mock_config_manager = Mock()
        databricks_config = DatabricksConfig(
            server_hostname='test.databricks.com',
            http_path='/sql/1.0/warehouses/test',
            access_token='test-token'
        )
        server_config = ServerConfig(databricks=databricks_config)
        mock_config_manager.create_server_config.return_value = server_config
        mock_config_manager_class.return_value = mock_config_manager
        
        # Mock asyncio.run to raise KeyboardInterrupt
        mock_asyncio_run.side_effect = KeyboardInterrupt()
        
        main()
        
        mock_exit.assert_called_once_with(0)
    
    @patch('databricks_mcp_server.main.detect_uvx_environment')
    @patch('databricks_mcp_server.main.parse_arguments')
    @patch('databricks_mcp_server.main.setup_logging')
    @patch('databricks_mcp_server.main.ConfigManager')
    @patch('databricks_mcp_server.main.asyncio.run')
    @patch('sys.exit')
    def test_main_mcp_server_error(self, mock_exit, mock_asyncio_run, mock_config_manager_class,
                                  mock_setup_logging, mock_parse_args, mock_detect_uvx):
        """Test main function with MCP server error."""
        # Mock arguments
        mock_args = Mock()
        mock_args.config = None
        mock_args.log_level = 'INFO'
        mock_parse_args.return_value = mock_args
        
        # Mock config manager
        mock_config_manager = Mock()
        databricks_config = DatabricksConfig(
            server_hostname='test.databricks.com',
            http_path='/sql/1.0/warehouses/test',
            access_token='test-token'
        )
        server_config = ServerConfig(databricks=databricks_config)
        mock_config_manager.create_server_config.return_value = server_config
        mock_config_manager_class.return_value = mock_config_manager
        
        # Mock asyncio.run to raise MCPServerError
        server_error = MCPServerError(
            message="Server startup failed",
            category="runtime",
            error_code="SERVER_001",
            troubleshooting_guide="Check server configuration",
            suggested_actions=["Verify credentials", "Check network connectivity"]
        )
        mock_asyncio_run.side_effect = server_error
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            main()
        
        mock_exit.assert_called_once_with(1)
        stderr_output = mock_stderr.getvalue()
        assert "Server Error" in stderr_output
        assert "Server startup failed" in stderr_output
    
    @patch('databricks_mcp_server.main.detect_uvx_environment')
    def test_main_uvx_environment_error(self, mock_detect_uvx):
        """Test main function with uvx environment error."""
        uvx_error = UvxEnvironmentError(
            message="uvx environment validation failed",
            error_code="UVX_001",
            troubleshooting_guide="Check uvx installation",
            suggested_actions=["Install uv/uvx", "Check Python version"]
        )
        mock_detect_uvx.side_effect = uvx_error
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with patch('sys.exit') as mock_exit:
                main()
        
        mock_exit.assert_called_with(1)
        stderr_output = mock_stderr.getvalue()
        assert "Critical Error" in stderr_output
        assert "uvx environment validation failed" in stderr_output
    
    @patch('databricks_mcp_server.main.detect_uvx_environment')
    @patch('databricks_mcp_server.main.parse_arguments')
    @patch('databricks_mcp_server.main.setup_logging')
    @patch('databricks_mcp_server.main.ConfigManager')
    @patch('databricks_mcp_server.main.asyncio.run')
    @patch('sys.exit')
    def test_main_unexpected_error(self, mock_exit, mock_asyncio_run, mock_config_manager_class,
                                  mock_setup_logging, mock_parse_args, mock_detect_uvx):
        """Test main function with unexpected error."""
        # Mock arguments
        mock_args = Mock()
        mock_args.config = None
        mock_args.log_level = 'INFO'
        mock_parse_args.return_value = mock_args
        
        # Mock config manager
        mock_config_manager = Mock()
        databricks_config = DatabricksConfig(
            server_hostname='test.databricks.com',
            http_path='/sql/1.0/warehouses/test',
            access_token='test-token'
        )
        server_config = ServerConfig(databricks=databricks_config)
        mock_config_manager.create_server_config.return_value = server_config
        mock_config_manager_class.return_value = mock_config_manager
        
        # Mock asyncio.run to raise unexpected error
        mock_asyncio_run.side_effect = RuntimeError("Unexpected runtime error")
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            main()
        
        mock_exit.assert_called_once_with(1)
        stderr_output = mock_stderr.getvalue()
        assert "Unexpected Error" in stderr_output


if __name__ == "__main__":
    pytest.main([__file__])