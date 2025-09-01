#!/usr/bin/env python3
"""
Health check and monitoring for Snowflake MCP Server
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta


class HealthChecker:
    """Health check and monitoring for Snowflake MCP Server"""
    
    def __init__(self):
        self.last_health_check = None
        self.health_check_interval = 300  # 5 minutes
        self.connection_retry_count = 0
        self.max_retry_attempts = 3
        self.last_successful_connection = None
        
    async def perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        start_time = time.time()
        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "checks": {},
            "response_time_ms": 0,
            "uptime_seconds": 0
        }
        
        try:
            # Check 1: Environment configuration
            config_check = await self._check_configuration()
            health_status["checks"]["configuration"] = config_check
            
            # Check 2: Database connectivity
            db_check = await self._check_database_connection()
            health_status["checks"]["database_connection"] = db_check
            
            # Check 3: Authentication
            auth_check = await self._check_authentication()
            health_status["checks"]["authentication"] = auth_check
            
            # Check 4: Basic query execution
            query_check = await self._check_query_execution()
            health_status["checks"]["query_execution"] = query_check
            
            # Determine overall health status
            failed_checks = [name for name, check in health_status["checks"].items() 
                           if not check.get("healthy", False)]
            
            if failed_checks:
                health_status["status"] = "unhealthy"
                health_status["failed_checks"] = failed_checks
            
            # Update connection tracking
            if db_check.get("healthy", False):
                self.last_successful_connection = datetime.utcnow()
                self.connection_retry_count = 0
            else:
                self.connection_retry_count += 1
            
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
            health_status["error_type"] = type(e).__name__
        
        # Calculate response time
        health_status["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
        self.last_health_check = datetime.utcnow()
        
        return health_status
    
    async def _check_configuration(self) -> Dict[str, Any]:
        """Check configuration validity"""
        try:
            from env_validator import EnvironmentValidator
            
            validator = EnvironmentValidator()
            valid, errors, warnings = validator.validate_all()
            
            return {
                "healthy": valid,
                "details": {
                    "valid": valid,
                    "errors": errors,
                    "warnings": warnings
                }
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def _check_database_connection(self) -> Dict[str, Any]:
        """Check database connection"""
        try:
            # Import here to avoid circular imports
            import server
            
            if not hasattr(server, 'config') or server.config is None:
                return {
                    "healthy": False,
                    "error": "Configuration not loaded"
                }
            
            # Try to create a connection
            connection = await server.create_snowflake_connection()
            
            # Test basic connectivity
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            connection.close()
            
            return {
                "healthy": True,
                "details": {
                    "connection_test": "passed",
                    "result": result[0] if result else None
                }
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def _check_authentication(self) -> Dict[str, Any]:
        """Check authentication status"""
        try:
            # Import here to avoid circular imports
            import server
            
            success, message, details = await server.test_authentication()
            
            return {
                "healthy": success,
                "details": {
                    "message": message,
                    "user_info": details
                }
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def _check_query_execution(self) -> Dict[str, Any]:
        """Check basic query execution"""
        try:
            # Import here to avoid circular imports
            import server
            
            if not hasattr(server, 'sql_executor') or server.sql_executor is None:
                return {
                    "healthy": False,
                    "error": "SQL executor not initialized"
                }
            
            # Execute a simple query
            result = await server.sql_executor.execute_query("SELECT CURRENT_VERSION()")
            
            return {
                "healthy": result.get("success", False),
                "details": {
                    "query_result": result
                }
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def should_perform_health_check(self) -> bool:
        """Check if it's time for a health check"""
        if self.last_health_check is None:
            return True
        
        time_since_last = datetime.utcnow() - self.last_health_check
        return time_since_last.total_seconds() >= self.health_check_interval
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get connection status information"""
        return {
            "last_successful_connection": self.last_successful_connection.isoformat() if self.last_successful_connection else None,
            "connection_retry_count": self.connection_retry_count,
            "max_retry_attempts": self.max_retry_attempts,
            "connection_healthy": self.connection_retry_count < self.max_retry_attempts
        }
    
    async def validate_connection_with_retry(self) -> Tuple[bool, str]:
        """Validate connection with retry logic"""
        max_retries = 3
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                # Import here to avoid circular imports
                import server
                
                connection = await server.create_snowflake_connection()
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                connection.close()
                
                self.connection_retry_count = 0
                self.last_successful_connection = datetime.utcnow()
                return True, "Connection successful"
                
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    self.connection_retry_count += 1
                    return False, f"Connection failed after {max_retries} attempts: {str(e)}"
        
        return False, "Max retries exceeded"


# Global health checker instance
health_checker = HealthChecker()


async def get_health_status() -> str:
    """Get current health status as JSON string"""
    try:
        health_status = await health_checker.perform_health_check()
        return json.dumps(health_status, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "unhealthy",
            "error": str(e),
            "error_type": type(e).__name__,
            "timestamp": datetime.utcnow().isoformat()
        }, indent=2)


async def quick_health_check() -> bool:
    """Quick health check that returns True if healthy"""
    try:
        health_status = await health_checker.perform_health_check()
        return health_status.get("status") == "healthy"
    except Exception:
        return False


if __name__ == "__main__":
    """Allow running as standalone script for health check"""
    async def main():
        print("Performing health check...")
        status = await get_health_status()
        print(status)
        
        # Exit with appropriate code
        health_data = json.loads(status)
        exit_code = 0 if health_data.get("status") == "healthy" else 1
        exit(exit_code)
    
    asyncio.run(main())