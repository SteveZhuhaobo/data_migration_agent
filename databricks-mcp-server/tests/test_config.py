"""
Unit tests for configuration management functionality.

Tests configuration loading, validation, and environment variable processing.
"""

import os
import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from databricks_mcp_server.config import ConfigManager, DatabricksConfig, ServerConfig, ConfigurationError


class TestConfigManager:
    """Test cases for ConfigManager class."""
    
    def test_config_manager_initialization(self):
        """Test ConfigManager initialization."""
        config_manager = ConfigManager()
        assert config_manager is not None
        assert hasattr(config_manager, 'ENV_VAR_MAPPING')
        assert hasattr(config_manager, 'REQUIRED_FIELDS')
        assert hasattr(config_manager, 'DEFAULT_CONFIG_PATHS')
    
    @patch.dict(os.environ, {
        'DATABRICKS_SERVER_HOSTNAME': 'test.databricks.com',
        'DATABRICKS_HTTP_PATH': '/sql/1.0/warehouses/test',
        'DATABRICKS_ACCESS_TOKEN': 'test-token',
        'DATABRICKS_CATALOG': 'test_catalog',
        'DATABRICKS_SCHEMA': 'test_schema',
        'DATABRICKS_MCP_LOG_LEVEL': 'DEBUG'
    })
    def test_load_config_from_environment_variables(self):
        """Test loading configuration from environment variables."""
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        assert 'databricks' in config
        assert config['databricks']['server_hostname'] == 'test.databricks.com'
        assert config['databricks']['http_path'] == '/sql/1.0/warehouses/test'
        assert config['databricks']['access_token'] == 'test-token'
        assert config['databricks']['catalog'] == 'test_catalog'
        assert config['databricks']['schema'] == 'test_schema'
        assert config['log_level'] == 'DEBUG'
    
    def test_load_config_from_file(self):
        """Test loading configuration from YAML file."""
        config_data = {
            'databricks': {
                'server_hostname': 'file.databricks.com',
                'http_path': '/sql/1.0/warehouses/file',
                'access_token': 'file-token',
                'catalog': 'file_catalog',
                'schema': 'file_schema',
                'timeout': 300
            },
            'log_level': 'WARNING'
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_file_path = f.name
        
        try:
            config_manager = ConfigManager()
            config = config_manager.load_config(config_file_path)
            
            assert config['databricks']['server_hostname'] == 'file.databricks.com'
            assert config['databricks']['http_path'] == '/sql/1.0/warehouses/file'
            assert config['databricks']['access_token'] == 'file-token'
            assert config['databricks']['catalog'] == 'file_catalog'
            assert config['databricks']['schema'] == 'file_schema'
            assert config['databricks']['timeout'] == 300
            assert config['log_level'] == 'WARNING'
        finally:
            os.unlink(config_file_path)
    
    @patch.dict(os.environ, {
        'DATABRICKS_SERVER_HOSTNAME': 'env.databricks.com',
        'DATABRICKS_ACCESS_TOKEN': 'env-token'
    })
    def test_environment_variables_override_file(self):
        """Test that environment variables take precedence over config file."""
        config_data = {
            'databricks': {
                'server_hostname': 'file.databricks.com',
                'http_path': '/sql/1.0/warehouses/file',
                'access_token': 'file-token'
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_file_path = f.name
        
        try:
            config_manager = ConfigManager()
            config = config_manager.load_config(config_file_path)
            
            # Environment variables should override file values
            assert config['databricks']['server_hostname'] == 'env.databricks.com'
            assert config['databricks']['access_token'] == 'env-token'
            # File values should remain for non-overridden fields
            assert config['databricks']['http_path'] == '/sql/1.0/warehouses/file'
        finally:
            os.unlink(config_file_path)
    
    def test_load_config_file_not_found(self):
        """Test loading configuration when specified file doesn't exist."""
        config_manager = ConfigManager()
        
        with pytest.raises(ConfigurationError, match="Config file not found"):
            config_manager.load_config('/nonexistent/config.yaml')
    
    def test_load_config_invalid_yaml(self):
        """Test loading configuration with invalid YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_file_path = f.name
        
        try:
            config_manager = ConfigManager()
            with pytest.raises(ConfigurationError, match="Failed to load config file"):
                config_manager.load_config(config_file_path)
        finally:
            os.unlink(config_file_path)
    
    @patch.dict(os.environ, {'DATABRICKS_TIMEOUT': 'invalid'})
    def test_invalid_timeout_environment_variable(self):
        """Test handling of invalid timeout value in environment variable."""
        config_manager = ConfigManager()
        
        with pytest.raises(ConfigurationError, match="Invalid timeout value"):
            config_manager.load_config()
    
    def test_validate_config_missing_databricks_section(self):
        """Test validation with missing databricks section."""
        config_manager = ConfigManager()
        
        with pytest.raises(ConfigurationError, match="Missing 'databricks' configuration section"):
            config_manager.validate_config({})
    
    def test_validate_config_missing_required_fields(self):
        """Test validation with missing required fields."""
        config_manager = ConfigManager()
        config = {'databricks': {}}
        
        with pytest.raises(ConfigurationError) as exc_info:
            config_manager.validate_config(config)
        
        error_message = str(exc_info.value)
        assert "Missing required field 'server_hostname'" in error_message
        assert "Missing required field 'http_path'" in error_message
        assert "Missing required field 'access_token'" in error_message
    
    def test_validate_config_invalid_server_hostname(self):
        """Test validation with invalid server hostname format."""
        config_manager = ConfigManager()
        config = {
            'databricks': {
                'server_hostname': 'https://test.databricks.com',
                'http_path': '/sql/1.0/warehouses/test',
                'access_token': 'test-token'
            }
        }
        
        with pytest.raises(ConfigurationError, match="server_hostname should not include protocol"):
            config_manager.validate_config(config)
    
    def test_validate_config_invalid_http_path(self):
        """Test validation with invalid http_path format."""
        config_manager = ConfigManager()
        config = {
            'databricks': {
                'server_hostname': 'test.databricks.com',
                'http_path': 'sql/1.0/warehouses/test',  # Missing leading slash
                'access_token': 'test-token'
            }
        }
        
        with pytest.raises(ConfigurationError, match="http_path must start with '/'"):
            config_manager.validate_config(config)
    
    def test_validate_config_invalid_timeout(self):
        """Test validation with invalid timeout value."""
        config_manager = ConfigManager()
        config = {
            'databricks': {
                'server_hostname': 'test.databricks.com',
                'http_path': '/sql/1.0/warehouses/test',
                'access_token': 'test-token',
                'timeout': -1
            }
        }
        
        with pytest.raises(ConfigurationError, match="timeout must be a positive integer"):
            config_manager.validate_config(config)
    
    def test_validate_config_invalid_log_level(self):
        """Test validation with invalid log level."""
        config_manager = ConfigManager()
        config = {
            'databricks': {
                'server_hostname': 'test.databricks.com',
                'http_path': '/sql/1.0/warehouses/test',
                'access_token': 'test-token'
            },
            'log_level': 'INVALID'
        }
        
        with pytest.raises(ConfigurationError, match="Invalid log_level 'INVALID'"):
            config_manager.validate_config(config)
    
    def test_validate_config_valid(self):
        """Test validation with valid configuration."""
        config_manager = ConfigManager()
        config = {
            'databricks': {
                'server_hostname': 'test.databricks.com',
                'http_path': '/sql/1.0/warehouses/test',
                'access_token': 'test-token',
                'catalog': 'test_catalog',
                'schema': 'test_schema',
                'timeout': 120
            },
            'log_level': 'INFO'
        }
        
        assert config_manager.validate_config(config) is True
    
    def test_get_databricks_config_with_provided_config(self):
        """Test getting Databricks config with provided configuration."""
        config_manager = ConfigManager()
        config = {
            'databricks': {
                'server_hostname': 'test.databricks.com',
                'http_path': '/sql/1.0/warehouses/test',
                'access_token': 'test-token'
            }
        }
        
        databricks_config = config_manager.get_databricks_config(config)
        assert databricks_config == config['databricks']
    
    def test_get_databricks_config_empty(self):
        """Test getting Databricks config with empty configuration."""
        config_manager = ConfigManager()
        config = {}
        
        databricks_config = config_manager.get_databricks_config(config)
        assert databricks_config == {}
    
    @patch.dict(os.environ, {
        'DATABRICKS_SERVER_HOSTNAME': 'test.databricks.com',
        'DATABRICKS_HTTP_PATH': '/sql/1.0/warehouses/test',
        'DATABRICKS_ACCESS_TOKEN': 'test-token',
        'DATABRICKS_CATALOG': 'test_catalog',
        'DATABRICKS_SCHEMA': 'test_schema',
        'DATABRICKS_MCP_LOG_LEVEL': 'DEBUG'
    })
    def test_create_server_config(self):
        """Test creating ServerConfig object from loaded configuration."""
        config_manager = ConfigManager()
        server_config = config_manager.create_server_config()
        
        assert isinstance(server_config, ServerConfig)
        assert isinstance(server_config.databricks, DatabricksConfig)
        assert server_config.databricks.server_hostname == 'test.databricks.com'
        assert server_config.databricks.http_path == '/sql/1.0/warehouses/test'
        assert server_config.databricks.access_token == 'test-token'
        assert server_config.databricks.catalog == 'test_catalog'
        assert server_config.databricks.schema == 'test_schema'
        assert server_config.log_level == 'DEBUG'
    
    def test_merge_config_simple(self):
        """Test merging simple configuration dictionaries."""
        config_manager = ConfigManager()
        base = {'a': 1, 'b': 2}
        override = {'b': 3, 'c': 4}
        
        merged = config_manager._merge_config(base, override)
        assert merged == {'a': 1, 'b': 3, 'c': 4}
    
    def test_merge_config_nested(self):
        """Test merging nested configuration dictionaries."""
        config_manager = ConfigManager()
        base = {
            'databricks': {
                'server_hostname': 'base.com',
                'http_path': '/base/path',
                'catalog': 'base_catalog'
            },
            'log_level': 'INFO'
        }
        override = {
            'databricks': {
                'server_hostname': 'override.com',
                'access_token': 'override-token'
            }
        }
        
        merged = config_manager._merge_config(base, override)
        expected = {
            'databricks': {
                'server_hostname': 'override.com',
                'http_path': '/base/path',
                'catalog': 'base_catalog',
                'access_token': 'override-token'
            },
            'log_level': 'INFO'
        }
        assert merged == expected


class TestDatabricksConfig:
    """Test cases for DatabricksConfig dataclass."""
    
    def test_databricks_config_creation(self):
        """Test creating DatabricksConfig with required fields."""
        config = DatabricksConfig(
            server_hostname="test.databricks.com",
            http_path="/sql/1.0/warehouses/test",
            access_token="test-token"
        )
        assert config.server_hostname == "test.databricks.com"
        assert config.http_path == "/sql/1.0/warehouses/test"
        assert config.access_token == "test-token"
        assert config.catalog == "hive_metastore"  # default value
        assert config.schema == "default"  # default value
        assert config.timeout == 120  # default value


class TestServerConfig:
    """Test cases for ServerConfig dataclass."""
    
    def test_server_config_creation(self):
        """Test creating ServerConfig with DatabricksConfig."""
        databricks_config = DatabricksConfig(
            server_hostname="test.databricks.com",
            http_path="/sql/1.0/warehouses/test",
            access_token="test-token"
        )
        server_config = ServerConfig(databricks=databricks_config)
        assert server_config.databricks == databricks_config
        assert server_config.log_level == "INFO"  # default value
        assert server_config.config_file is None  # default value