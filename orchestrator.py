#!/usr/bin/env python3
"""
Personal AI Employee Orchestrator

Manages multiple watcher services, handles priority-based processing,
and coordinates between different services with health checks and failover.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class WatcherStatus(Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    RECOVERING = "recovering"


@dataclass
class WatcherInfo:
    name: str
    host: str
    port: int
    status: WatcherStatus
    last_heartbeat: float
    priority: int
    error_count: int


class Orchestrator:
    def __init__(self):
        self.watchers: Dict[str, WatcherInfo] = {}
        self.running = False
        self.health_check_interval = 30  # seconds
        self.max_errors_before_recovery = 3

        # Configure logging
        self.logger = logging.getLogger("Orchestrator")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def register_watcher(self, name: str, host: str, port: int, priority: int = 0):
        """Register a new watcher service"""
        self.watchers[name] = WatcherInfo(
            name=name,
            host=host,
            port=port,
            status=WatcherStatus.STOPPED,
            last_heartbeat=time.time(),
            priority=priority,
            error_count=0
        )
        self.logger.info(f"Registered watcher: {name} at {host}:{port} with priority {priority}")

    def start_watchers(self):
        """Start all registered watchers"""
        if self.running:
            self.logger.warning("Orchestrator is already running")
            return

        self.running = True
        asyncio.run(self._start_watchers_async())

    async def _start_watchers_async(self):
        """Async wrapper to start watchers"""
        self.logger.info("Starting all watchers...")

        # Start watchers in priority order
        sorted_watchers = sorted(self.watchers.values(), key=lambda x: x.priority, reverse=True)

        for watcher in sorted_watchers:
            await self._start_watcher(watcher)

        # Start health check loop
        asyncio.create_task(self._health_check_loop())

    async def _start_watcher(self, watcher: WatcherInfo):
        """Start a single watcher"""
        # In a real implementation, this would start the watcher process
        # For now, we'll simulate starting the watcher
        watcher.status = WatcherStatus.RUNNING
        watcher.last_heartbeat = time.time()
        self.logger.info(f"Started watcher: {watcher.name}")

    async def _health_check_loop(self):
        """Continuous health check loop for all watchers"""
        while self.running:
            await asyncio.sleep(self.health_check_interval)

            self.logger.debug("Running health checks...")

            for watcher in self.watchers.values():
                await self._check_watcher_health(watcher)

    async def _check_watcher_health(self, watcher: WatcherInfo):
        """Check the health of a single watcher"""
        # Simulate health check
        # In a real implementation, this would make an actual health check request
        current_time = time.time()

        # Check if watcher has been silent for too long
        if current_time - watcher.last_heartbeat > 60:  # 60 seconds
            watcher.error_count += 1
            self.logger.warning(f"Watcher {watcher.name} has been silent for {(current_time - watcher.last_heartbeat):.0f} seconds")

            if watcher.error_count >= self.max_errors_before_recovery:
                await self._recover_watcher(watcher)
        else:
            watcher.error_count = max(0, watcher.error_count - 1)  # Decay error count

    async def _recover_watcher(self, watcher: WatcherInfo):
        """Attempt to recover a failed watcher"""
        watcher.status = WatcherStatus.RECOVERING
        self.logger.warning(f"Attempting to recover watcher: {watcher.name}")

        # Simulate recovery process
        await asyncio.sleep(5)  # Simulate recovery time

        # Reset watcher status
        watcher.status = WatcherStatus.RUNNING
        watcher.last_heartbeat = time.time()
        watcher.error_count = 0

        self.logger.info(f"Successfully recovered watcher: {watcher.name}")

    def stop_watchers(self):
        """Stop all watchers"""
        if not self.running:
            self.logger.warning("Orchestrator is not running")
            return

        self.running = False
        self.logger.info("Stopping all watchers...")

        for watcher in self.watchers.values():
            watcher.status = WatcherStatus.STOPPED

        self.logger.info("All watchers stopped")

    def get_watcher_status(self) -> Dict[str, Dict]:
        """Get status of all watchers"""
        return {
            name: {
                "status": watcher.status.value,
                "last_heartbeat": watcher.last_heartbeat,
                "priority": watcher.priority,
                "error_count": watcher.error_count
            }
            for name, watcher in self.watchers.items()
        }

    def get_overall_status(self) -> Dict:
        """Get overall system status"""
        statuses = [watcher.status for watcher in self.watchers.values()]

        # Calculate system health
        healthy_count = sum(1 for status in statuses if status == WatcherStatus.RUNNING)
        total_count = len(statuses)
        health_percentage = (healthy_count / total_count) * 100 if total_count > 0 else 0

        return {
            "system_health": health_percentage,
            "watchers": self.get_watcher_status(),
            "healthy_watchers": healthy_count,
            "total_watchers": total_count,
            "status": "healthy" if health_percentage >= 80 else "degraded" if health_percentage >= 50 else "critical"
        }

    def handle_event(self, event_type: str, data: Dict):
        """Handle events from watchers and route them appropriately"""
        self.logger.info(f"Received event: {event_type} from {data.get('source')}")

        # Route events based on type and priority
        if event_type == "file_modified":
            # Handle file modification events
            self._handle_file_event(data)
        elif event_type == "email_received":
            # Handle email events
            self._handle_email_event(data)
        elif event_type == "message_received":
            # Handle message events
            self._handle_message_event(data)
        else:
            self.logger.warning(f"Unknown event type: {event_type}")

    def _handle_file_event(self, data: Dict):
        """Handle file modification events"""
        # Process file events with priority
        priority = data.get("priority", 0)
        self.logger.info(f"Processing file event with priority {priority}: {data.get('file_path')}")

        # In a real implementation, this would trigger appropriate actions
        # For now, we'll just log the event
        pass

    def _handle_email_event(self, data: Dict):
        """Handle email received events"""
        # Process email events
        self.logger.info(f"Processing email from {data.get('sender')}: {data.get('subject')}")

        # In a real implementation, this would trigger appropriate actions
        # For now, we'll just log the event
        pass

    def _handle_message_event(self, data: Dict):
        """Handle message received events"""
        # Process message events
        self.logger.info(f"Processing message from {data.get('sender')}: {data.get('content')[:50]}...")

        # In a real implementation, this would trigger appropriate actions
        # For now, we'll just log the event
        pass

    def get_priority_queue(self) -> List[Dict]:
        """Get priority queue of pending events"""
        # In a real implementation, this would return actual pending events
        # For now, we'll return a simulated priority queue
        return [
            {"event": "file_modified", "priority": 2, "data": {"file_path": "/path/to/important/file.txt"}},
            {"event": "email_received", "priority": 1, "data": {"subject": "Important Update"}},
            {"event": "message_received", "priority": 3, "data": {"content": "Urgent message"}}
        ]


# CLI interface for orchestrator
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Personal AI Employee Orchestrator")
    parser.add_argument("--config", default="mcp.json", help="Path to MCP configuration file")
    parser.add_argument("--host", default="localhost", help="Orchestrator host")
    parser.add_argument("--port", type=int, default=50054, help="Orchestrator port")
    parser.add_argument("--log-level", default="INFO", help="Logging level")

    args = parser.parse_args()

    # Configure logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))

    orchestrator = Orchestrator()

    # Load configuration from MCP file
    try:
        with open(args.config) as f:
            config = json.load(f)

            # Register watchers from config
            for service_name, service_config in config.get("services", {}).items():
                if "args" in service_config:
                    host = next((arg for arg in service_config["args"] if arg == "--host"), "localhost")
                    port = next((int(arg) for arg in service_config["args"] if arg == "--port"), 50051)
                    orchestrator.register_watcher(service_name, host, port)

    except Exception as e:
        print(f"Error loading configuration: {e}")
        exit(1)

    print("Personal AI Employee Orchestrator")
    print("Available commands:")
    print("  start      - Start all watchers")
    print("  stop       - Stop all watchers")
    print("  status     - Show current status")
    print("  priority   - Show priority queue")
    print("  exit       - Exit orchestrator")

    while True:
        command = input("\n> ").strip().lower()

        if command == "start":
            orchestrator.start_watchers()
        elif command == "stop":
            orchestrator.stop_watchers()
        elif command == "status":
            status = orchestrator.get_overall_status()
            print(json.dumps(status, indent=2))
        elif command == "priority":
            queue = orchestrator.get_priority_queue()
            print(json.dumps(queue, indent=2))
        elif command == "exit":
            break
        else:
            print(f"Unknown command: {command}")