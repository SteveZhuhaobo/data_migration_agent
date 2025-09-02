"""
Configuration management for the Databricks MCP Server.

This module handles loading configuration from multiple sources including
environment variables, config files, and command-line arguments.
"""

import os
import yaml
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .errors import ErrorHandler, ConfigurationError


logger = logging.getLogger(__name__)


@dataclass
class DatabricksConfig:
    """Configuration for Databricks connection."""
    server_hostname: str
    http_path: str
    access_token: str
    catalog: str = "hive_metastore"
    schema: str = "default"
    timeout: int = 120


@dataclass
class ServerConfig:
    """Overall server configuration."""
    databricks: DatabricksConfig
    log_level: str = "INFO"
    config_file: Optional[str] = None


class ConfigManager:
    """
    Manages configuration loading from multiple sources.
    
    Handles configuration precedence:
    1. Environment variables (highest priority)
    2. Config file specified via --config argument
    3. Default config file locations
    4. Interactive prompts for missing values (lowest priority)
    """
    
    # Environment variable mappings
    ENV_VAR_MAPPING = {
        'server_hostname': 'DATABRICKS_SERVER_HOSTNAME',
        'http_path': 'DATABRICKS_HTTP_PATH',
        'access_token': 'DATABRICKS_ACCESS_TOKEN',
        'catalog': 'DATABRICKS_CATALOG',
        'schema': 'DATABRICKS_SCHEMA',
        'timeout': 'DATABRICKS_TIMEOUT',
        'log_level': 'DATABRICKS_MCP_LOG_LEVEL'
    }
    
    # Required configuration fields
    REQUIRED_FIELDS = ['server_hostname', 'http_path', 'access_token']
    
    # Default config file locations
    DEFAULT_CONFIG_PATHS = [
        './config.yaml',
        './config/config.yaml',
        Path.home() / '.databricks-mcp' / 'config.yaml'
    ]
    
    def load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration from multiple sources.
        
        Args:
            config_path: Optional path to configuration file
            
        Returns:
            Dictionary containing merged configuration
            
        Raises:
            ConfigurationError: If configuration is invalid or missing required values
        """
        config = {}
        
        # 1. Load from config file (lowest priority)
        file_config = self._load_config_file(config_path)
        if file_config:
            config.update(file_config)
            logger.debug(f"Loaded configuration from file: {config_path or 'default location'}")
        
        # 2. Override with environment variables (highest priority)
        env_config = self._load_environment_variables()
        if env_config:
            config = self._merge_config(config, env_config)
            logger.debug("Applied environment variable overrides")
        
        # 3. Validate the final configuration
        self.validate_config(config)
        
        return config
    
    def _load_config_file(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Optional path to configuration file
            
        Returns:
            Dictionary containing file configuration or empty dict if no file found
        """
        paths_to_try = []
        
        if config_path:
            paths_to_try.append(Path(config_path))
        else:
            paths_to_try.extend(self.DEFAULT_CONFIG_PATHS)
        
        for path in paths_to_try:
            try:
                path = Path(path)
                if path.exists() and path.is_file():
                    with open(path, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f) or {}
                    logger.info(f"Loaded configuration from: {path}")
                    return config
            except (yaml.YAMLError, IOError) as e:
                if config_path:  # If specific path was provided, raise error
                    raise ErrorHandler.create_configuration_error(
                        field="config_file",
                        details=f"Failed to load config file '{path}': {e}",
                        original_error=e
                    )
                else:  # If trying default paths, just log and continue
                    logger.debug(f"Could not load config from {path}: {e}")
        
        if config_path:
            raise ErrorHandler.create_configuration_error(
                field="config_file",
                details=f"Config file not found: {config_path}"
            )
        
        logger.debug("No configuration file found in default locations")
        return {}
    
    def _load_environment_variables(self) -> Dict[str, Any]:
        """
        Load configuration from environment variables.
        
        Returns:
            Dictionary containing environment variable configuration
        """
        env_config = {}
        databricks_config = {}
        
        for config_key, env_var in self.ENV_VAR_MAPPING.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert timeout to int if it's the timeout field
                if config_key == 'timeout':
                    try:
                        value = int(value)
                    except ValueError as e:
                        raise ErrorHandler.create_configuration_error(
                            field="timeout",
                            details=f"Invalid timeout value in {env_var}: {value}. Must be an integer.",
                            original_error=e
                        )
                
                if config_key == 'log_level':
                    env_config['log_level'] = value
                else:
                    databricks_config[config_key] = value
        
        if databricks_config:
            env_config['databricks'] = databricks_config
        
        return env_config
    
    def _merge_config(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge two configuration dictionaries with override taking precedence.
        
        Args:
            base_config: Base configuration dictionary
            override_config: Override configuration dictionary
            
        Returns:
            Merged configuration dictionary
        """
        merged = base_config.copy()
        
        for key, value in override_config.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_config(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration and report any issues.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            True if configuration is valid
            
        Raises:
            ConfigurationError: If configuration is invalid or missing required values
        """
        errors = []
        
        # Check if databricks section exists
        if 'databricks' not in config:
            errors.append("Missing 'databricks' configuration section")
        else:
            databricks_config = config['databricks']
            
            # Check required fields
            for field in self.REQUIRED_FIELDS:
                if field not in databricks_config or not databricks_config[field]:
                    env_var = self.ENV_VAR_MAPPING.get(field, f'DATABRICKS_{field.upper()}')
                    errors.append(f"Missing required field '{field}'. Set it in config file or environment variable '{env_var}'")
            
            # Validate server_hostname format
            if 'server_hostname' in databricks_config:
                hostname = databricks_config['server_hostname']
                if hostname.startswith('https://') or hostname.startswith('http://'):
                    errors.append("server_hostname should not include protocol (https://). Use just the hostname.")
            
            # Validate http_path format
            if 'http_path' in databricks_config:
                http_path = databricks_config['http_path']
                if not http_path.startswith('/'):
                    errors.append("http_path must start with '/'")
            
            # Validate timeout
            if 'timeout' in databricks_config:
                timeout = databricks_config['timeout']
                if not isinstance(timeout, int) or timeout <= 0:
                    errors.append("timeout must be a positive integer")
        
        # Validate log level
        if 'log_level' in config:
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if config['log_level'].upper() not in valid_levels:
                errors.append(f"Invalid log_level '{config['log_level']}'. Must be one of: {', '.join(valid_levels)}")
        
        if errors:
            error_message = "Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
            
            # Determine the primary missing field for better error categorization
            primary_field = "configuration"
            for field in self.REQUIRED_FIELDS:
                if any(field in error for error in errors):
                    primary_field = field
                    break
            
            raise ErrorHandler.create_configuration_error(
                field=primary_field,
                details=error_message
            )
        
        return True
    
    def get_databricks_config(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get Databricks-specific configuration.
        
        Args:
            config: Optional configuration dictionary. If not provided, loads from sources.
            
        Returns:
            Dictionary containing Databricks connection configuration
        """
        if config is None:
            config = self.load_config()
        
        return config.get('databricks', {})
    
    def create_server_config(self, config_path: Optional[str] = None) -> ServerConfig:
        """
        Create a ServerConfig object from loaded configuration.
        
        Args:
            config_path: Optional path to configuration file
            
        Returns:
            ServerConfig object with loaded configuration
        """
        config = self.load_config(config_path)
        
        databricks_config = DatabricksConfig(
            server_hostname=config['databricks']['server_hostname'],
            http_path=config['databricks']['http_path'],
            access_token=config['databricks']['access_token'],
            catalog=config['databricks'].get('catalog', 'hive_metastore'),
            schema=config['databricks'].get('schema', 'default'),
            timeout=config['databricks'].get('timeout', 120)
        )
        
        return ServerConfig(
            databricks=databricks_config,
            log_level=config.get('log_level', 'INFO'),
            config_file=config_path
        )