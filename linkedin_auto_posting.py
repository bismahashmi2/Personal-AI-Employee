#!/usr/bin/env python3
"""
LinkedIn Auto-Posting Workflow Runner
Complete Silver Tier implementation for automatic LinkedIn posting.

This script runs the full workflow:
1. LinkedIn Watcher monitors for trending topics
2. Creates action files in Needs_Action/
3. Claude reasoning loop processes them (manual step)
4. Workflow Coordinator moves plans to Pending_Approval/
5. Human approves by moving to Approved/
6. Post Executor automatically posts to LinkedIn
7. Completed items moved to Done/

Usage:
    python linkedin_auto_posting.py --vault . --mode full
    python linkedin_auto_posting.py --vault . --mode executor-only
    python linkedin_auto_posting.py --vault . --mode coordinator-only
"""

import sys
import time
import logging
import argparse
import subprocess
import signal
from pathlib import Path
from typing import List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class LinkedInAutoPostingWorkflow:
    """
    Manages the complete LinkedIn auto-posting workflow.
    Coordinates multiple components to achieve Silver Tier requirements.
    """

    def __init__(self, vault_path: str, mode: str = 'full'):
        self.vault_path = Path(vault_path)
        self.mode = mode
        self.logger = logging.getLogger('LinkedInAutoPosting')
        self.processes: List[subprocess.Popen] = []
        self.running = False

        # Validate vault structure
        self._validate_vault()

    def _validate_vault(self):
        """Ensure required directories exist"""
        required_dirs = [
            'Needs_Action',
            'Plans',
            'Pending_Approval',
            'Approved',
            'Done'
        ]

        for dir_name in required_dirs:
            dir_path = self.vault_path / dir_name
            dir_path.mkdir(exist_ok=True)
            self.logger.debug(f"✅ Directory ready: {dir_name}/")

    def start_linkedin_watcher(self) -> Optional[subprocess.Popen]:
        """Start the LinkedIn watcher to monitor for trending topics"""
        self.logger.info("🔍 Starting LinkedIn Watcher...")

        try:
            proc = subprocess.Popen(
                [sys.executable, 'linkedin_watcher.py', '--vault', str(self.vault_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            self.logger.info(f"✅ LinkedIn Watcher started (PID: {proc.pid})")
            return proc
        except Exception as e:
            self.logger.error(f"❌ Failed to start LinkedIn Watcher: {e}")
            return None

    def start_workflow_coordinator(self) -> Optional[subprocess.Popen]:
        """Start the workflow coordinator to process plans"""
        self.logger.info("📋 Starting Workflow Coordinator...")

        try:
            proc = subprocess.Popen(
                [sys.executable, 'linkedin_workflow_coordinator.py', '--vault', str(self.vault_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            self.logger.info(f"✅ Workflow Coordinator started (PID: {proc.pid})")
            return proc
        except Exception as e:
            self.logger.error(f"❌ Failed to start Workflow Coordinator: {e}")
            return None

    def start_post_executor(self) -> Optional[subprocess.Popen]:
        """Start the post executor to automatically post approved content"""
        self.logger.info("📤 Starting Post Executor...")

        try:
            proc = subprocess.Popen(
                [sys.executable, 'linkedin_post_executor.py', '--vault', str(self.vault_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            self.logger.info(f"✅ Post Executor started (PID: {proc.pid})")
            return proc
        except Exception as e:
            self.logger.error(f"❌ Failed to start Post Executor: {e}")
            return None

    def stream_process_output(self, proc: subprocess.Popen, name: str):
        """Stream process output to logger"""
        if proc.stdout:
            for line in iter(proc.stdout.readline, ''):
                if line:
                    self.logger.info(f"[{name}] {line.rstrip()}")
                if not self.running:
                    break

    def run(self):
        """Run the complete workflow"""
        self.logger.info("=" * 70)
        self.logger.info("🚀 LinkedIn Auto-Posting Workflow - Silver Tier")
        self.logger.info("=" * 70)
        self.logger.info(f"Vault: {self.vault_path}")
        self.logger.info(f"Mode: {self.mode}")
        self.logger.info("")

        self.running = True

        # Start components based on mode
        if self.mode == 'full':
            self.logger.info("Starting all components...")

            # Start LinkedIn Watcher
            watcher_proc = self.start_linkedin_watcher()
            if watcher_proc:
                self.processes.append(watcher_proc)

            time.sleep(2)  # Give watcher time to start

            # Start Workflow Coordinator
            coordinator_proc = self.start_workflow_coordinator()
            if coordinator_proc:
                self.processes.append(coordinator_proc)

            time.sleep(2)  # Give coordinator time to start

            # Start Post Executor
            executor_proc = self.start_post_executor()
            if executor_proc:
                self.processes.append(executor_proc)

        elif self.mode == 'executor-only':
            self.logger.info("Starting Post Executor only...")
            executor_proc = self.start_post_executor()
            if executor_proc:
                self.processes.append(executor_proc)

        elif self.mode == 'coordinator-only':
            self.logger.info("Starting Workflow Coordinator only...")
            coordinator_proc = self.start_workflow_coordinator()
            if coordinator_proc:
                self.processes.append(coordinator_proc)

        if not self.processes:
            self.logger.error("❌ No processes started. Exiting.")
            return 1

        self.logger.info("")
        self.logger.info("=" * 70)
        self.logger.info("✅ Workflow Running")
        self.logger.info("=" * 70)
        self.logger.info("")
        self.logger.info("📊 Workflow Steps:")
        self.logger.info("  1. LinkedIn Watcher detects trending topics")
        self.logger.info("  2. Creates files in Needs_Action/")
        self.logger.info("  3. Claude processes them (run: claude-code)")
        self.logger.info("  4. Coordinator moves plans to Pending_Approval/")
        self.logger.info("  5. YOU approve by moving to Approved/")
        self.logger.info("  6. Executor automatically posts to LinkedIn")
        self.logger.info("  7. Completed items moved to Done/")
        self.logger.info("")
        self.logger.info("Press Ctrl+C to stop all components")
        self.logger.info("")

        # Set up signal handler
        def signal_handler(signum, frame):
            self.logger.info("\n🛑 Shutdown signal received...")
            self.running = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Monitor processes
        try:
            while self.running:
                # Check if any process has died
                for proc in self.processes:
                    if proc.poll() is not None:
                        self.logger.warning(f"⚠️ Process {proc.pid} exited with code {proc.returncode}")
                        self.processes.remove(proc)

                if not self.processes:
                    self.logger.error("❌ All processes stopped. Exiting.")
                    break

                time.sleep(1)

        except KeyboardInterrupt:
            self.logger.info("\n🛑 Keyboard interrupt received...")

        # Cleanup
        self.stop_all()
        return 0

    def stop_all(self):
        """Stop all running processes"""
        self.logger.info("🛑 Stopping all components...")

        for proc in self.processes:
            try:
                self.logger.info(f"Stopping process {proc.pid}...")
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.logger.warning(f"Process {proc.pid} did not exit, killing...")
                    proc.kill()
            except Exception as e:
                self.logger.error(f"Error stopping process {proc.pid}: {e}")

        self.processes.clear()
        self.logger.info("✅ All components stopped")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="LinkedIn Auto-Posting Workflow - Silver Tier Implementation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete workflow
  python linkedin_auto_posting.py --vault . --mode full

  # Run only the post executor (if other components already running)
  python linkedin_auto_posting.py --vault . --mode executor-only

  # Run only the workflow coordinator
  python linkedin_auto_posting.py --vault . --mode coordinator-only

Workflow:
  1. LinkedIn Watcher monitors for trending topics → Needs_Action/
  2. Claude reasoning loop processes files → Plans/
  3. Workflow Coordinator moves to → Pending_Approval/
  4. Human approves by moving to → Approved/
  5. Post Executor automatically posts to LinkedIn
  6. Completed items moved to → Done/
        """
    )

    parser.add_argument(
        '--vault',
        default='.',
        help='Path to vault directory (default: current directory)'
    )

    parser.add_argument(
        '--mode',
        choices=['full', 'executor-only', 'coordinator-only'],
        default='full',
        help='Workflow mode (default: full)'
    )

    args = parser.parse_args()

    # Validate vault path
    vault_path = Path(args.vault)
    if not vault_path.exists():
        print(f"❌ Error: Vault path does not exist: {vault_path}")
        return 1

    # Run workflow
    workflow = LinkedInAutoPostingWorkflow(str(vault_path), args.mode)
    return workflow.run()


if __name__ == '__main__':
    sys.exit(main())
