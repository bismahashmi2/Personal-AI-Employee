#!/bin/bash
# Setup cron job for AI Employee auto-start

VAULT_PATH="/mnt/d/Code/hackathon0/AI_Employee_Vault"
VENV_PYTHON="$VAULT_PATH/.venv2/bin/python"
LOG_FILE="/var/log/ai_employee.log"
CRON_JOB="@reboot cd $VAULT_PATH && $VENV_PYTHON silver_tier_main.py --vault $VAULT_PATH >> $LOG_FILE 2>&1"

echo "Setting up cron job for AI Employee..."
echo ""
echo "Cron job to be added:"
echo "$CRON_JOB"
echo ""

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "silver_tier_main.py"; then
    echo "Cron job already exists. Remove it first:"
    echo "  crontab -e"
    exit 1
fi

# Add the cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
echo "✅ Cron job added successfully!"
echo ""
echo "To verify: crontab -l"
echo ""
echo "Note: Logs will be written to: $LOG_FILE"
echo "      Make sure the log directory exists and is writable."
