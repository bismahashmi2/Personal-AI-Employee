#!/usr/bin/env python3
"""
Check if AI Employee system is running
"""
import psutil
import sys
from pathlib import Path

def is_running():
    """Check if silver_tier_main.py is running"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and 'silver_tier_main.py' in ' '.join(cmdline):
                return True, proc.info
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False, None

def main():
    running, proc_info = is_running()
    vault_path = Path(__file__).parent.parent / "AI_Employee_Vault"

    print("=" * 50)
    print("AI Employee System Status Check")
    print("=" * 50)

    if running:
        print(f"✅ System is RUNNING")
        print(f"   PID: {proc_info['pid']}")
        print(f"   Command: {' '.join(proc_info['cmdline'])}")
    else:
        print("❌ System is NOT running")
        print("\nTo start the system:")
        print(f"  cd {vault_path}")
        print(f"  source .venv2/bin/activate")
        print(f"  python silver_tier_main.py --vault {vault_path}")

    print("\nTo check logs:")
    print("  journalctl -u ai-employee.service -f  # systemd")
    print("  tail -f /var/log/ai_employee.log     # cron")
    print("=" * 50)

    return 0 if running else 1

if __name__ == "__main__":
    sys.exit(main())
