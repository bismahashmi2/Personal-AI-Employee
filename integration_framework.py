#!/usr/bin/env python3
"""
Integration Framework

Provides templates and utilities for connecting external APIs, databases,
and services with priority-based processing and robust error handling.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Callable, TypeVar
from dataclasses import dataclass, field
from enum import Enum
import requests
import sqlite3
from contextlib import contextmanager


# Type variable for generic integration handlers
T = TypeVar('T')


class IntegrationType(Enum):
    API = "api"
    DATABASE = "database"
    FILE_SYSTEM = "filesystem"
    MESSAGING = "messaging"
    CUSTOM = "custom"


class PriorityLevel(Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3


@dataclass
class IntegrationConfig:
    name: str
    type: IntegrationType
    endpoint: str
    auth: Optional[Dict[str, str]] = None
    headers: Optional[Dict[str, str]] = None
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    priority: PriorityLevel = PriorityLevel.MEDIUM
    enabled: bool = True


@dataclass
class IntegrationStatus:
    name: str
    status: str
    last_success: Optional[float] = None
    last_error: Optional[float] = None
    error_count: int = 0
    success_count: int = 0
    response_time: Optional[float] = None


class IntegrationError(Exception):
    """Base exception for integration errors"""
    pass


class RateLimitError(IntegrationError):
    """Exception for rate limiting"""
    pass


class AuthenticationError(IntegrationError):
    """Exception for authentication failures"""
    pass


class IntegrationHandler:
    def __init__(self):
        self.integrations: Dict[str, IntegrationConfig] = {}
        self.status: Dict[str, IntegrationStatus] = {}
        self.logger = logging.getLogger("IntegrationHandler")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def register_integration(self, config: IntegrationConfig):
        """Register a new integration"""
        if config.name in self.integrations:
            raise ValueError(f"Integration {config.name} already exists")

        self.integrations[config.name] = config
        self.status[config.name] = IntegrationStatus(
            name=config.name,
            status="registered"
        )
        self.logger.info(f"Registered integration: {config.name}")

    def get_integration(self, name: str) -> Optional[IntegrationConfig]:
        """Get integration configuration"""
        return self.integrations.get(name)

    def get_all_integrations(self) -> Dict[str, IntegrationConfig]:
        """Get all registered integrations"""
        return self.integrations.copy()

    async def execute_integration(
        self,
        name: str,
        data: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute an integration with priority-based processing"""
        config = self.get_integration(name)
        if not config:
            raise IntegrationError(f"Integration {name} not found")

        if not config.enabled:
            raise IntegrationError(f"Integration {name} is disabled")

        # Process based on integration type
        if config.type == IntegrationType.API:
            return await self._execute_api_integration(config, data, context)
        elif config.type == IntegrationType.DATABASE:
            return await self._execute_database_integration(config, data, context)
        elif config.type == IntegrationType.FILE_SYSTEM:
            return await self._execute_filesystem_integration(config, data, context)
        elif config.type == IntegrationType.MESSAGING:
            return await self._execute_messaging_integration(config, data, context)
        elif config.type == IntegrationType.CUSTOM:
            return await self._execute_custom_integration(config, data, context)
        else:
            raise IntegrationError(f"Unknown integration type: {config.type}")

    async def _execute_api_integration(
        self,
        config: IntegrationConfig,
        data: Optional[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> Any:
        """Execute API integration"""
        method = data.get("method", "GET") if data else "GET"
        endpoint = data.get("endpoint", config.endpoint) if data else config.endpoint
        payload = data.get("payload", {}) if data else {}
        headers = {**(config.headers or {}), **(data.get("headers", {}) if data else {})}

        # Add authentication headers
        if config.auth:
            if "token" in config.auth:
                headers["Authorization"] = f"Bearer {config.auth['token']}"
            elif "username" in config.auth and "password" in config.auth:
                headers["Authorization"] = f"Basic {config.auth['username']}:{config.auth['password']}"

        # Execute with retry logic
        for attempt in range(config.max_retries):
            try:
                start_time = time.time()
                response = await self._make_api_request(
                    method, endpoint, payload, headers, config.timeout
                )
                response_time = time.time() - start_time

                # Update status
                self._update_status(
                    config.name,
                    status="success",
                    last_success=time.time(),
                    success_count=self.status[config.name].success_count + 1,
                    response_time=response_time
                )

                return response

            except requests.exceptions.RequestException as e:
                self._update_status(
                    config.name,
                    status="error",
                    last_error=time.time(),
                    error_count=self.status[config.name].error_count + 1
                )

                if attempt < config.max_retries - 1:
                    await asyncio.sleep(config.retry_delay * (attempt + 1))
                else:
                    raise IntegrationError(f"API integration failed: {str(e)}")

    async def _make_api_request(
        self,
        method: str,
        url: str,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        timeout: int
    ) -> Dict[str, Any]:
        """Make HTTP request"""
        response = requests.request(
            method=method,
            url=url,
            json=payload if method.upper() in ["POST", "PUT", "PATCH"] else None,
            data=payload if method.upper() in ["GET", "DELETE"] else None,
            headers=headers,
            timeout=timeout
        )

        if response.status_code >= 400:
            if response.status_code == 429:
                raise RateLimitError(f"Rate limit exceeded: {response.text}")
            elif response.status_code == 401 or response.status_code == 403:
                raise AuthenticationError(f"Authentication failed: {response.text}")
            else:
                raise IntegrationError(f"API request failed: {response.status_code} - {response.text}")

        return response.json()

    async def _execute_database_integration(
        self,
        config: IntegrationConfig,
        data: Optional[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> Any:
        """Execute database integration"""
        query = data.get("query", "") if data else ""
        params = data.get("params", []) if data else []

        try:
            start_time = time.time()
            result = await self._execute_database_query(config.endpoint, query, params)
            response_time = time.time() - start_time

            # Update status
            self._update_status(
                config.name,
                status="success",
                last_success=time.time(),
                success_count=self.status[config.name].success_count + 1,
                response_time=response_time
            )

            return result

        except sqlite3.DatabaseError as e:
            self._update_status(
                config.name,
                status="error",
                last_error=time.time(),
                error_count=self.status[config.name].error_count + 1
            )
            raise IntegrationError(f"Database integration failed: {str(e)}")

    @contextmanager
    def _get_database_connection(self, db_path: str):
        """Context manager for database connections"""
        conn = sqlite3.connect(db_path)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    async def _execute_database_query(
        self,
        db_path: str,
        query: str,
        params: List[Any]
    ) -> List[Dict]:
        """Execute database query"""
        with self._get_database_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    async def _execute_filesystem_integration(
        self,
        config: IntegrationConfig,
        data: Optional[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> Any:
        """Execute filesystem integration"""
        operation = data.get("operation", "read") if data else "read"
        path = data.get("path", config.endpoint) if data else config.endpoint

        try:
            start_time = time.time()
            result = await self._execute_filesystem_operation(operation, path)
            response_time = time.time() - start_time

            # Update status
            self._update_status(
                config.name,
                status="success",
                last_success=time.time(),
                success_count=self.status[config.name].success_count + 1,
                response_time=response_time
            )

            return result

        except Exception as e:
            self._update_status(
                config.name,
                status="error",
                last_error=time.time(),
                error_count=self.status[config.name].error_count + 1
            )
            raise IntegrationError(f"Filesystem integration failed: {str(e)}")

    async def _execute_filesystem_operation(self, operation: str, path: str) -> Any:
        """Execute filesystem operation"""
        if operation == "read":
            with open(path, 'r') as f:
                return f.read()
        elif operation == "write":
            with open(path, 'w') as f:
                return f.write("")  # Write empty content, can be extended
        elif operation == "exists":
            return os.path.exists(path)
        else:
            raise IntegrationError(f"Unknown filesystem operation: {operation}")

    async def _execute_messaging_integration(
        self,
        config: IntegrationConfig,
        data: Optional[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> Any:
        """Execute messaging integration"""
        message = data.get("message", "") if data else ""
        recipient = data.get("recipient", "") if data else ""

        try:
            start_time = time.time()
            result = await self._send_message(config.endpoint, message, recipient)
            response_time = time.time() - start_time

            # Update status
            self._update_status(
                config.name,
                status="success",
                last_success=time.time(),
                success_count=self.status[config.name].success_count + 1,
                response_time=response_time
            )

            return result

        except Exception as e:
            self._update_status(
                config.name,
                status="error",
                last_error=time.time(),
                error_count=self.status[config.name].error_count + 1
            )
            raise IntegrationError(f"Messaging integration failed: {str(e)}")

    async def _send_message(self, endpoint: str, message: str, recipient: str) -> Dict:
        """Send message"""
        # This would be implemented based on specific messaging service
        # For now, we'll simulate it
        await asyncio.sleep(0.1)  # Simulate network delay
        return {"status": "sent", "message": message, "recipient": recipient}

    async def _execute_custom_integration(
        self,
        config: IntegrationConfig,
        data: Optional[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> Any:
        """Execute custom integration"""
        handler = data.get("handler", None) if data else None
        if not handler:
            raise IntegrationError("Custom integration requires a handler function")

        try:
            start_time = time.time()
            result = await handler(data, context)
            response_time = time.time() - start_time

            # Update status
            self._update_status(
                config.name,
                status="success",
                last_success=time.time(),
                success_count=self.status[config.name].success_count + 1,
                response_time=response_time
            )

            return result

        except Exception as e:
            self._update_status(
                config.name,
                status="error",
                last_error=time.time(),
                error_count=self.status[config.name].error_count + 1
            )
            raise IntegrationError(f"Custom integration failed: {str(e)}")

    def _update_status(
        self,
        name: str,
        status: str,
        last_success: Optional[float] = None,
        last_error: Optional[float] = None,
        error_count: Optional[int] = None,
        success_count: Optional[int] = None,
        response_time: Optional[float] = None
    ):
        """Update integration status"""
        if name not in self.status:
            return

        if status:
            self.status[name].status = status
        if last_success is not None:
            self.status[name].last_success = last_success
        if last_error is not None:
            self.status[name].last_error = last_error
        if error_count is not None:
            self.status[name].error_count = error_count
        if success_count is not None:
            self.status[name].success_count = success_count
        if response_time is not None:
            if self.status[name].response_time is None:
                self.status[name].response_time = response_time
            else:
                # Calculate moving average
                current = self.status[name].response_time
                self.status[name].response_time = (current + response_time) / 2

    def get_status(self, name: str) -> Optional[IntegrationStatus]:
        """Get integration status"""
        return self.status.get(name)

    def get_all_statuses(self) -> Dict[str, IntegrationStatus]:
        """Get all integration statuses"""
        return self.status.copy()

    def get_health_metrics(self) -> Dict:
        """Get overall health metrics"""
        total = len(self.integrations)
        if total == 0:
            return {"integrations": 0, "healthy": 0, "error_rate": 0.0}

        healthy = sum(1 for status in self.status.values() if status.status == "success")
        error_count = sum(status.error_count for status in self.status.values())
        success_count = sum(status.success_count for status in self.status.values())
        total_requests = error_count + success_count

        return {
            "integrations": total,
            "healthy": healthy,
            "error_rate": error_count / total_requests if total_requests > 0 else 0.0,
            "average_response_time": sum(
                (status.response_time or 0) for status in self.status.values()
            ) / total if total > 0 else 0.0
        }


# CLI interface for integration framework
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Integration Framework")
    parser.add_argument("--register", action="store_true", help="Register sample integrations")
    parser.add_argument("--status", action="store_true", help="Show integration status")
    parser.add_argument("--test", action="store_true", help="Run test integrations")

    args = parser.parse_args()

    handler = IntegrationHandler()

    if args.register:
        print("Registering sample integrations...")

        # Sample API integration
        api_config = IntegrationConfig(
            name="sample_api",
            type=IntegrationType.API,
            endpoint="https://jsonplaceholder.typicode.com/posts",
            auth={"token": "sample-token"},
            priority=PriorityLevel.HIGH
        )
        handler.register_integration(api_config)

        # Sample database integration
        db_config = IntegrationConfig(
            name="sample_database",
            type=IntegrationType.DATABASE,
            endpoint="sample.db",
            priority=PriorityLevel.MEDIUM
        )
        handler.register_integration(db_config)

        # Sample filesystem integration
        fs_config = IntegrationConfig(
            name="sample_filesystem",
            type=IntegrationType.FILE_SYSTEM,
            endpoint="/mnt/d/Code/hackathon0/AI_Employee_Vault/test.txt",
            priority=PriorityLevel.LOW
        )
        handler.register_integration(fs_config)

        print("Sample integrations registered!")

    if args.status:
        statuses = handler.get_all_statuses()
        print(json.dumps({name: asdict(status) for name, status in statuses.items()}, indent=2))

    if args.test:
        print("Testing integrations...")

        # Test API integration
        try:
            result = asyncio.run(handler.execute_integration(
                "sample_api",
                data={"method": "GET"}
            ))
            print(f"API test result: {result[:100]}...")
        except Exception as e:
            print(f"API test failed: {e}")

        # Test database integration
        try:
            result = asyncio.run(handler.execute_integration(
                "sample_database",
                data={"query": "SELECT name FROM sqlite_master WHERE type='table';"}
            ))
            print(f"Database test result: {result}")
        except Exception as e:
            print(f"Database test failed: {e}")

        # Test filesystem integration
        try:
            result = asyncio.run(handler.execute_integration(
                "sample_filesystem",
                data={"operation": "exists"}
            ))
            print(f"Filesystem test result: {result}")
        except Exception as e:
            print(f"Filesystem test failed: {e}")

        # Show final status
        statuses = handler.get_all_statuses()
        print(json.dumps({name: asdict(status) for name, status in statuses.items()}, indent=2))