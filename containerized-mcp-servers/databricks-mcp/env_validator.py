#!/usr/bin/env python3
"""
Environment variable validation for Databricks MCP Server
"""

import os
import sys
from typing import Dict, List, Optional, Tuple


class EnvironmentValidator:
    """Validates environment variables and configuration for Databricks MCP Server"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        
    def validate_required_env_vars(self) -> bool:
        """Validate required environment variables"""
        required_vars = {
            'DATABRICKS_SERVER_HOSTNAME': 'Databricks workspace hostname',
            'DATABRICKS_HTTP_PATH': 'SQL warehouse HTTP path',
            'DATABRICKS_ACCESS_TOKEN': 'Personal access token'
        }
        
        missing_vars = []
        for var, description in required_vars.items():
            if not os.getenv(var):
                missing_vars.append(f"{var} ({description})")
        
        if missing_vars:
            self.errors.append(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        return True
    
    def validate_hostname_format(self) -> bool:
        """Validate Databricks hostname format"""
        hostname = os.getenv('DATABRICKS_SERVER_HOSTNAME')
        if not hostname:
            return True  # Will be caught by required validation
        
        # Remove protocol if present
        if hostname.startswith('https://'):
            hostname = hostname[8:]
        elif hostname.startswith('http://'):
            self.warnings.append("HTTP protocol detected in hostname. HTTPS is recommended for security.")
            hostname = hostname[7:]
        
        # Basic hostname validation
        if not hostname or '/' in hostname:
            self.errors.append(
                f"Invalid DATABRICKS_SERVER_HOSTNAME format: '{os.getenv('DATABRICKS_SERVER_HOSTNAME')}'. "
                "Expected format: 'your-workspace.cloud.databricks.com'"
            )
            return False
        
        # Check if it looks like a Databricks hostname
        if not any(domain in hostname.lower() for domain in ['.databricks.com', '.azuredatabricks.net', '.gcp.databricks.com']):
            self.warnings.append(
                f"Hostname '{hostname}' doesn't appear to be a standard Databricks hostname. "
                "Ensure it's correct for your workspace."
            )
        
        return True
    
    def validate_http_path_format(self) -> bool:
        """Validate HTTP path format"""
        http_path = os.getenv('DATABRICKS_HTTP_PATH')
        if not http_path:
            return True  # Will be caught by required validation
        
        if not http_path.startswith('/'):
            self.errors.append(
                f"Invalid DATABRICKS_HTTP_PATH format: '{http_path}'. "
                "Path must start with '/'. Expected format: '/sql/1.0/warehouses/warehouse_id'"
            )
            return False
        
        # Check if it looks like a SQL warehouse path
        if '/sql/' not in http_path or '/warehouses/' not in http_path:
            self.warnings.append(
                f"HTTP path '{http_path}' doesn't appear to be a SQL warehouse path. "
                "Expected format: '/sql/1.0/warehouses/warehouse_id'"
            )
        
        return True
    
    def validate_access_token_format(self) -> bool:
        """Validate access token format"""
        token = os.getenv('DATABRICKS_ACCESS_TOKEN')
        if not token:
            return True  # Will be caught by required validation
        
        # Basic token validation
        if len(token) < 10:
            self.errors.append("DATABRICKS_ACCESS_TOKEN appears to be too short to be valid")
            return False
        
        # Check for common token prefixes
        if token.startswith('dapi') and len(token) < 40:
            self.warnings.append("Access token appears to be shorter than typical Databricks tokens")
        elif not token.startswith('dapi') and not token.startswith('dkea'):
            self.warnings.append("Access token doesn't start with expected prefix (dapi/dkea)")
        
        return True
    
    def validate_optional_config(self) -> bool:
        """Validate optional configuration parameters"""
        valid = True
        
        # Validate catalog name
        catalog = os.getenv('DATABRICKS_CATALOG')
        if catalog and not self._is_valid_identifier(catalog):
            self.warnings.append(
                f"DATABRICKS_CATALOG='{catalog}' contains invalid characters. "
                "Use alphanumeric characters, underscores, and hyphens only."
            )
        
        # Validate schema name
        schema = os.getenv('DATABRICKS_SCHEMA')
        if schema and not self._is_valid_identifier(schema):
            self.warnings.append(
                f"DATABRICKS_SCHEMA='{schema}' contains invalid characters. "
                "Use alphanumeric characters, underscores, and hyphens only."
            )
        
        return valid
    
    def _is_valid_identifier(self, identifier: str) -> bool:
        """Check if identifier is valid for Databricks (catalog/schema names)"""
        if not identifier:
            return False
        
        # Allow alphanumeric, underscores, and hyphens
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-')
        return all(c in allowed_chars for c in identifier) and not identifier.startswith('-')
    
    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """Run all validations and return results"""
        self.errors.clear()
        self.warnings.clear()
        
        valid = True
        valid &= self.validate_required_env_vars()
        valid &= self.validate_hostname_format()
        valid &= self.validate_http_path_format()
        valid &= self.validate_access_token_format()
        valid &= self.validate_optional_config()
        
        return valid, self.errors.copy(), self.warnings.copy()
    
    def print_validation_results(self, valid: bool, errors: List[str], warnings: List[str]) -> None:
        """Print validation results to console"""
        if errors:
            print("❌ Configuration Errors:")
            for error in errors:
                print(f"  • {error}")
            print()
        
        if warnings:
            print("⚠️  Configuration Warnings:")
            for warning in warnings:
                print(f"  • {warning}")
            print()
        
        if valid and not warnings:
            print("✅ Environment configuration is valid")
        elif valid:
            print("✅ Environment configuration is valid (with warnings)")
        else:
            print("❌ Environment configuration is invalid")
    
    def get_config_summary(self) -> Dict[str, str]:
        """Get a summary of current configuration"""
        summary = {}
        
        # Required fields
        hostname = os.getenv('DATABRICKS_SERVER_HOSTNAME', 'NOT SET')
        # Mask the hostname for security (show first and last parts)
        if hostname != 'NOT SET' and len(hostname) > 10:
            masked_hostname = hostname[:8] + '***' + hostname[-8:]
            summary['Server Hostname'] = masked_hostname
        else:
            summary['Server Hostname'] = hostname
        
        summary['HTTP Path'] = os.getenv('DATABRICKS_HTTP_PATH', 'NOT SET')
        
        # Mask access token
        token = os.getenv('DATABRICKS_ACCESS_TOKEN', 'NOT SET')
        if token != 'NOT SET' and len(token) > 8:
            summary['Access Token'] = token[:4] + '***' + token[-4:]
        else:
            summary['Access Token'] = token
        
        # Optional settings
        summary['Catalog'] = os.getenv('DATABRICKS_CATALOG', 'hive_metastore')
        summary['Schema'] = os.getenv('DATABRICKS_SCHEMA', 'default')
        
        return summary


def validate_environment() -> bool:
    """Standalone function to validate environment and exit if invalid"""
    validator = EnvironmentValidator()
    valid, errors, warnings = validator.validate_all()
    
    validator.print_validation_results(valid, errors, warnings)
    
    if not valid:
        print("\nPlease fix the configuration errors above before starting the server.")
        print("See the README.md file for configuration examples.")
        return False
    
    if warnings:
        print("\nServer will start with warnings. Consider reviewing the configuration.")
    
    # Print configuration summary
    print("\n📋 Configuration Summary:")
    summary = validator.get_config_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    print()
    
    return True


if __name__ == "__main__":
    """Allow running as standalone script for validation"""
    if not validate_environment():
        sys.exit(1)
    print("Environment validation passed!")