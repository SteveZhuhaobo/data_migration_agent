#!/usr/bin/env python3
"""
Environment variable validation for SQL Server MCP Server
"""

import os
import sys
from typing import Dict, List, Optional, Tuple


class EnvironmentValidator:
    """Validates environment variables and configuration for SQL Server MCP Server"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        
    def validate_required_env_vars(self) -> bool:
        """Validate required environment variables"""
        # Server is always required
        if not os.getenv('SQLSERVER_SERVER'):
            self.errors.append("Missing required environment variable: SQLSERVER_SERVER (SQL Server hostname)")
            return False
        
        # Check authentication method
        use_windows_auth = os.getenv('SQLSERVER_USE_WINDOWS_AUTH', 'false').lower() == 'true'
        
        if not use_windows_auth:
            missing_auth = []
            if not os.getenv('SQLSERVER_USERNAME'):
                missing_auth.append('SQLSERVER_USERNAME')
            if not os.getenv('SQLSERVER_PASSWORD'):
                missing_auth.append('SQLSERVER_PASSWORD')
            
            if missing_auth:
                self.errors.append(
                    f"Missing required authentication variables: {', '.join(missing_auth)}. "
                    "Required when SQLSERVER_USE_WINDOWS_AUTH is not 'true'"
                )
                return False
        
        return True
    
    def validate_server_format(self) -> bool:
        """Validate SQL Server hostname/connection string format"""
        server = os.getenv('SQLSERVER_SERVER')
        if not server:
            return True  # Will be caught by required validation
        
        # Basic server validation
        if server.strip() != server:
            self.warnings.append("SQLSERVER_SERVER has leading/trailing whitespace")
        
        # Check for common formats
        if ',' in server:
            # Server with port (server,port)
            parts = server.split(',')
            if len(parts) == 2:
                try:
                    port = int(parts[1])
                    if port < 1 or port > 65535:
                        self.warnings.append(f"Port {port} is outside valid range (1-65535)")
                except ValueError:
                    self.warnings.append(f"Invalid port format in server string: '{parts[1]}'")
        
        return True
    
    def validate_database_name(self) -> bool:
        """Validate database name format"""
        database = os.getenv('SQLSERVER_DATABASE')
        if not database:
            self.warnings.append("SQLSERVER_DATABASE not set, will use 'master' database")
            return True
        
        # Basic database name validation
        if not self._is_valid_sql_identifier(database):
            self.warnings.append(
                f"SQLSERVER_DATABASE='{database}' contains potentially invalid characters. "
                "Use alphanumeric characters and underscores."
            )
        
        return True
    
    def validate_authentication_config(self) -> bool:
        """Validate authentication configuration"""
        use_windows_auth = os.getenv('SQLSERVER_USE_WINDOWS_AUTH', 'false').lower() == 'true'
        
        if use_windows_auth:
            # Windows authentication
            if os.getenv('SQLSERVER_USERNAME') or os.getenv('SQLSERVER_PASSWORD'):
                self.warnings.append(
                    "SQLSERVER_USERNAME and SQLSERVER_PASSWORD are ignored when using Windows authentication"
                )
        else:
            # SQL Server authentication
            username = os.getenv('SQLSERVER_USERNAME')
            password = os.getenv('SQLSERVER_PASSWORD')
            
            if username and len(username.strip()) != len(username):
                self.warnings.append("SQLSERVER_USERNAME has leading/trailing whitespace")
            
            if password and len(password) < 4:
                self.warnings.append("SQLSERVER_PASSWORD appears to be very short")
        
        return True
    
    def validate_connection_options(self) -> bool:
        """Validate connection options"""
        valid = True
        
        # Validate encrypt option
        encrypt = os.getenv('SQLSERVER_ENCRYPT', 'yes').lower()
        if encrypt not in ['yes', 'no', 'true', 'false']:
            self.warnings.append(
                f"SQLSERVER_ENCRYPT='{encrypt}' is not a standard value. "
                "Use 'yes', 'no', 'true', or 'false'"
            )
        
        # Validate trust certificate option
        trust_cert = os.getenv('SQLSERVER_TRUST_CERTIFICATE', 'yes').lower()
        if trust_cert not in ['yes', 'no', 'true', 'false']:
            self.warnings.append(
                f"SQLSERVER_TRUST_CERTIFICATE='{trust_cert}' is not a standard value. "
                "Use 'yes', 'no', 'true', or 'false'"
            )
        
        # Validate driver
        driver = os.getenv('SQLSERVER_DRIVER', 'ODBC Driver 17 for SQL Server')
        if driver and 'ODBC Driver' not in driver:
            self.warnings.append(
                f"SQLSERVER_DRIVER='{driver}' doesn't appear to be a standard ODBC driver name"
            )
        
        return valid
    
    def _is_valid_sql_identifier(self, identifier: str) -> bool:
        """Check if identifier is valid for SQL Server"""
        if not identifier:
            return False
        
        # Allow alphanumeric and underscores, must start with letter or underscore
        if not (identifier[0].isalpha() or identifier[0] == '_'):
            return False
        
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_')
        return all(c in allowed_chars for c in identifier)
    
    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """Run all validations and return results"""
        self.errors.clear()
        self.warnings.clear()
        
        valid = True
        valid &= self.validate_required_env_vars()
        valid &= self.validate_server_format()
        valid &= self.validate_database_name()
        valid &= self.validate_authentication_config()
        valid &= self.validate_connection_options()
        
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
        summary['Server'] = os.getenv('SQLSERVER_SERVER', 'NOT SET')
        summary['Database'] = os.getenv('SQLSERVER_DATABASE', 'master')
        
        # Authentication method
        use_windows_auth = os.getenv('SQLSERVER_USE_WINDOWS_AUTH', 'false').lower() == 'true'
        if use_windows_auth:
            summary['Auth Method'] = 'Windows Authentication'
        else:
            username = os.getenv('SQLSERVER_USERNAME', 'NOT SET')
            summary['Auth Method'] = f'SQL Server Authentication (User: {username})'
        
        # Connection options
        summary['Driver'] = os.getenv('SQLSERVER_DRIVER', 'ODBC Driver 17 for SQL Server')
        summary['Encrypt'] = os.getenv('SQLSERVER_ENCRYPT', 'yes')
        summary['Trust Certificate'] = os.getenv('SQLSERVER_TRUST_CERTIFICATE', 'yes')
        
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