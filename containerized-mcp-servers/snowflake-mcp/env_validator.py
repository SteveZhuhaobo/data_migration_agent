#!/usr/bin/env python3
"""
Environment variable validation for Snowflake MCP Server
"""

import os
import sys
from typing import Dict, List, Optional, Tuple


class EnvironmentValidator:
    """Validates environment variables and configuration for Snowflake MCP Server"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        
    def validate_required_env_vars(self) -> bool:
        """Validate required environment variables"""
        required_vars = {
            'SNOWFLAKE_ACCOUNT': 'Snowflake account identifier',
            'SNOWFLAKE_USER': 'Snowflake username'
        }
        
        missing_vars = []
        for var, description in required_vars.items():
            if not os.getenv(var):
                missing_vars.append(f"{var} ({description})")
        
        if missing_vars:
            self.errors.append(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        return True
    
    def validate_authentication_config(self) -> bool:
        """Validate authentication configuration"""
        password = os.getenv('SNOWFLAKE_PASSWORD')
        private_key_path = os.getenv('SNOWFLAKE_PRIVATE_KEY_PATH')
        
        if not password and not private_key_path:
            self.errors.append(
                "Authentication method required: set either SNOWFLAKE_PASSWORD or SNOWFLAKE_PRIVATE_KEY_PATH"
            )
            return False
        
        # Validate private key file exists if specified
        if private_key_path and not os.path.exists(private_key_path):
            self.errors.append(f"Private key file not found: {private_key_path}")
            return False
        
        return True
    
    def validate_optional_config(self) -> bool:
        """Validate optional configuration parameters"""
        valid = True
        
        # Validate numeric parameters
        numeric_params = {
            'SNOWFLAKE_TIMEOUT': (1, 3600, 120),  # min, max, default
            'SNOWFLAKE_MAX_RETRIES': (0, 10, 3),
            'SNOWFLAKE_RETRY_DELAY': (1, 60, 5),
            'SNOWFLAKE_POOL_SIZE': (1, 20, 5),
            'SNOWFLAKE_POOL_TIMEOUT': (1, 300, 30)
        }
        
        for param, (min_val, max_val, default_val) in numeric_params.items():
            value = os.getenv(param)
            if value:
                try:
                    int_value = int(value)
                    if int_value < min_val or int_value > max_val:
                        self.warnings.append(
                            f"{param}={int_value} is outside recommended range [{min_val}-{max_val}], "
                            f"using default {default_val}"
                        )
                except ValueError:
                    self.warnings.append(
                        f"{param}='{value}' is not a valid integer, using default {default_val}"
                    )
                    valid = False
        
        # Validate account format (basic check)
        account = os.getenv('SNOWFLAKE_ACCOUNT')
        if account and not self._is_valid_account_format(account):
            self.warnings.append(
                f"SNOWFLAKE_ACCOUNT='{account}' may not be in correct format. "
                "Expected format: <account_identifier> or <account_identifier>.<region>.<cloud>"
            )
        
        return valid
    
    def _is_valid_account_format(self, account: str) -> bool:
        """Basic validation of Snowflake account format"""
        if not account or len(account) < 2:
            return False
        
        # Allow alphanumeric, hyphens, underscores, and dots
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.')
        return all(c in allowed_chars for c in account)
    
    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """Run all validations and return results"""
        self.errors.clear()
        self.warnings.clear()
        
        valid = True
        valid &= self.validate_required_env_vars()
        valid &= self.validate_authentication_config()
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
        summary['Account'] = os.getenv('SNOWFLAKE_ACCOUNT', 'NOT SET')
        summary['User'] = os.getenv('SNOWFLAKE_USER', 'NOT SET')
        
        # Authentication method
        if os.getenv('SNOWFLAKE_PASSWORD'):
            summary['Auth Method'] = 'Password'
        elif os.getenv('SNOWFLAKE_PRIVATE_KEY_PATH'):
            summary['Auth Method'] = f"Private Key ({os.getenv('SNOWFLAKE_PRIVATE_KEY_PATH')})"
        else:
            summary['Auth Method'] = 'NOT CONFIGURED'
        
        # Optional connection settings
        summary['Database'] = os.getenv('SNOWFLAKE_DATABASE', 'default')
        summary['Schema'] = os.getenv('SNOWFLAKE_SCHEMA', 'default')
        summary['Warehouse'] = os.getenv('SNOWFLAKE_WAREHOUSE', 'default')
        summary['Role'] = os.getenv('SNOWFLAKE_ROLE', 'default')
        
        # Connection parameters
        summary['Timeout'] = os.getenv('SNOWFLAKE_TIMEOUT', '120')
        summary['Max Retries'] = os.getenv('SNOWFLAKE_MAX_RETRIES', '3')
        summary['Pool Size'] = os.getenv('SNOWFLAKE_POOL_SIZE', '5')
        
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