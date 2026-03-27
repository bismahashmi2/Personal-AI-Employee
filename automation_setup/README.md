# Silver Tier Point 7: OS-Level Scheduling Setup

This directory contains setup scripts for automatically starting the AI Employee system using OS-level schedulers.

## Option A: Cron (Linux/Mac)

### 1. Edit your crontab
```bash
crontab -e
```

### 2. Add this line (modify paths as needed)
```bash
@reboot cd /mnt/d/Code/hackathon0/AI_Employee_Vault && /home/youruser/.venv2/bin/python silver_tier_main.py --vault /mnt/d/Code/hackathon0/AI_Employee_Vault >> /var/log/ai_employee.log 2>&1
```

### 3. Set up log rotation (optional)
Create `/etc/logrotate.d/ai-employee`:
```
/var/log/ai_employee.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

## Option B: systemd (Modern Linux)

### 1. Create service file
```bash
sudo nano /etc/systemd/system/ai-employee.service
```

Paste:
```ini
[Unit]
Description=AI Employee Silver Tier System
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/mnt/d/Code/hackathon0/AI_Employee_Vault
Environment="PATH=/home/youruser/.venv2/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
ExecStart=/home/youruser/.venv2/bin/python silver_tier_main.py --vault /mnt/d/Code/hackathon0/AI_Employee_Vault
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Enable and start
```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-employee.service
sudo systemctl start ai-employee.service
sudo systemctl status ai-employee.service
```

### 3. View logs
```bash
sudo journalctl -u ai-employee.service -f
```

## Option C: Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: "At system startup"
4. Action: Start a program
   - Program: `C:\path\to\python.exe`
   - Arguments: `silver_tier_main.py --vault "C:\path\to\AI_Employee_Vault"`
   - Start in: `C:\path\to\AI_Employee_Vault`
5. Check "Run with highest privileges"
6. Configure for: Windows 10/11

## Verification

After setup, verify your system is running:
```bash
# For systemd
systemctl status ai-employee

# For cron
ps aux | grep silver_tier_main

# Check log
tail -f /var/log/ai_employee.log
```

## Quick Test Script

A helper script to check if the system is running:

```bash
python /mnt/d/Code/hackathon0/AI_Employee_Vault/automation_setup/check_status.py
```

## Notes

- The `scheduler.py` in the code handles periodic tasks (every 15 min processing, daily briefing, weekly audit)
- OS-level scheduler just ensures the Python process is always running
- For production, consider using a process manager like `supervisord` or `pm2`
