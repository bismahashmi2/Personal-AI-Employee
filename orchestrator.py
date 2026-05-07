#!/usr/bin/env python3
"""
Personal AI Employee Orchestrator

Manages multiple watcher services from mcp.json configuration.
"""

import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Orchestrator")


@dataclass
class ServiceInfo:
    name: str
    host: str
    port: int
    process: Optional[subprocess.Popen] = None
    status: str = "stopped"  # running, stopped, error
    pid: Optional[int] = None
    command: str = ""
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)


class Orchestrator:
    def __init__(self, config_path: str = 'mcp.json', vault_path: str = '.'):
        self.config_path = Path(config_path)
        self.vault_path = Path(vault_path)
        self.services: Dict[str, ServiceInfo] = {}
        self.running = False
        self._shutdown = False

        # Set up signal handlers
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame):
        """Handle termination signals"""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self._shutdown = True
        self.running = False

    def load_config(self):
        """Load service configuration from mcp.json"""
        if not self.config_path.exists():
            logger.error(f"Config file not found: {self.config_path}")
            return False

        try:
            with open(self.config_path) as f:
                config = json.load(f)

            # Load services
            for name, svc_config in config.get('services', {}).items():
                if 'args' not in svc_config:
                    logger.warning(f"Service {name} missing 'args', skipping")
                    continue

                # Extract host and port from args
                host = 'localhost'
                port = None
                args = svc_config['args'].copy()

                if '--host' in args:
                    idx = args.index('--host')
                    if idx + 1 < len(args):
                        host = args[idx + 1]

                if '--port' in args:
                    idx = args.index('--port')
                    if idx + 1 < len(args):
                        try:
                            port = int(args[idx + 1])
                        except ValueError:
                            port = None

                # Determine command
                command = svc_config.get('command', 'python')
                if isinstance(command, list):
                    command = command[0]

                self.services[name] = ServiceInfo(
                    name=name,
                    host=host,
                    port=port or self._infer_port(name),
                    command=command,
                    args=args,
                    env=svc_config.get('env', {})
                )
                logger.info(f"Loaded service: {name} -> {host}:{self.services[name].port}")

            return True

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return False

    def _infer_port(self, service_name: str) -> int:
        """Infer default port for service based on name"""
        # Map of service names to default ports
        port_map = {
            'filesystem-watcher': 50051,
            'gmail-watcher': 50052,
            'whatsapp-watcher': 50053,
            'linkedin-watcher': 50056,
            'orchestrator': 50054,
            'analytics': 50055,
        }
        return port_map.get(service_name, 50050 + hash(service_name) % 100)

    async def start_all(self):
        """Start all configured services"""
        logger.info("Starting all services...")

        # Start in priority order
        for name in sorted(self.services.keys()):
            if not self._shutdown:
                await self.start_service(name)

        logger.info(f"Started {len([s for s in self.services.values() if s.status == 'running'])} services")

    async def start_service(self, name: str) -> bool:
        """Start a single service"""
        service = self.services.get(name)
        if not service:
            logger.error(f"Service not found: {name}")
            return False

        if service.status == "running":
            logger.warning(f"Service {name} already running (PID: {service.pid})")
            return True

        logger.info(f"Starting service: {name}...")

        try:
            # Prepare environment
            env = os.environ.copy()
            env.update(service.env)
            # Add vault path if not set
            if 'VAULT_PATH' not in env and 'vault_path' in env:
                env['VAULT_PATH'] = str(self.vault_path)

            # Build command
            cmd = [service.command] + service.args

            # Start the process
            proc = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            service.process = proc
            service.pid = proc.pid
            service.status = "running"

            # Start log streaming in background
            asyncio.create_task(self._stream_logs(name, proc))

            logger.info(f"Started service {name} (PID: {proc.pid})")
            return True

        except Exception as e:
            logger.error(f"Failed to start service {name}: {e}")
            service.status = "error"
            return False

    async def _stream_logs(self, name: str, proc: subprocess.Popen):
        """Stream service logs to orchestrator logger"""
        if proc.stderr is None:
            return

        for line in iter(proc.stderr.readline, ''):
            if line:
                logger.info(f"[{name}] {line.rstrip()}")
            if self._shutdown:
                break

        proc.stderr.close()

    async def stop_all(self):
        """Stop all services"""
        logger.info("Stopping all services...")

        # Stop in reverse order
        for name in reversed(list(self.services.keys())):
            await self.stop_service(name)

        logger.info("All services stopped")

    async def stop_service(self, name: str) -> bool:
        """Stop a single service"""
        service = self.services.get(name)
        if not service or service.status != "running":
            return True

        if service.process:
            logger.info(f"Stopping service {name} (PID: {service.pid})...")
            try:
                service.process.terminate()
                try:
                    service.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    logger.warning(f"Service {name} did not exit, killing...")
                    service.process.kill()
            except Exception as e:
                logger.error(f"Error stopping {name}: {e}")

        service.status = "stopped"
        service.process = None
        service.pid = None
        return True

    async def monitor_loop(self):
        """Monitor service health and restart if needed"""
        logger.info("Starting monitoring loop...")

        while self.running and not self._shutdown:
            for name, service in self.services.items():
                if service.status == "running" and service.process:
                    # Check if process is still alive
                    if service.process.poll() is not None:
                        logger.warning(f"Service {name} exited with code {service.process.returncode}")
                        service.status = "error"
                        service.error_count += 1

                        # Attempt restart if not too many errors
                        if service.error_count < self.max_errors_before_recovery:
                            logger.info(f"Attempting to restart {name}...")
                            await self.start_service(name)
                        else:
                            logger.error(f"Service {name} failed too many times, manual intervention needed")

            await asyncio.sleep(self.health_check_interval)

    async def run(self):
        """Main run loop"""
        if not self.load_config():
            logger.error("Failed to load configuration")
            return 1

        self.running = True

        # Start all services
        await self.start_all()

        if self._shutdown:
            await self.stop_all()
            return 0

        # Run monitoring in background
        monitor_task = asyncio.create_task(self.monitor_loop())

        try:
            # Wait for shutdown signal
            while self.running and not self._shutdown:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            self.running = False

        # Cleanup
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass

        await self.stop_all()
        return 0

    def get_status(self) -> dict:
        """Get status of all services"""
        status = {}
        for name, svc in self.services.items():
            status[name] = {
                'status': svc.status,
                'pid': svc.pid,
                'port': svc.port,
                'host': svc.host,
                'error_count': svc.error_count
            }
        return status


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Personal AI Employee Orchestrator")
    parser.add_argument("--config", default="mcp.json", help="Path to MCP configuration file")
    parser.add_argument("--vault", default=".", help="Path to vault directory")
    parser.add_argument("--log-level", default="INFO", help="Logging level")

    args = parser.parse_args()

    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))

    orchestrator = Orchestrator(args.config, args.vault)
    return await orchestrator.run()


if __name__ == '__main__':
    asyncio.run(main())
