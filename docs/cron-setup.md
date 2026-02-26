# Scheduling Setup Guide

Set up automated scheduling for the AI Employee using cron (Mac/Linux) or Task Scheduler (Windows).

## Quick Start

```bash
# Make scheduler executable
chmod +x scripts/scheduler.sh

# Test it works
./scripts/scheduler.sh status
./scripts/scheduler.sh daily
```

---

## Mac/Linux: Cron Setup

### Edit Crontab

```bash
# Open crontab editor
crontab -e

# View current crontab
crontab -l
```

### Recommended Schedule

Add these lines to your crontab:

```cron
# ===========================================
# AI Employee Scheduled Tasks
# ===========================================

# Daily morning check at 8:00 AM
0 8 * * * /path/to/AI_Employee_Vault/scripts/scheduler.sh daily >> /tmp/ai_employee_daily.log 2>&1

# LinkedIn posts: Monday, Wednesday, Friday at 9:00 AM
0 9 * * 1,3,5 /path/to/AI_Employee_Vault/scripts/scheduler.sh linkedin >> /tmp/ai_employee_linkedin.log 2>&1

# Check pending approvals: Every 4 hours during work hours
0 9,13,17 * * 1-5 /path/to/AI_Employee_Vault/scripts/scheduler.sh check-approvals >> /tmp/ai_employee_approvals.log 2>&1

# Email check: Every 2 hours during work hours
0 8,10,12,14,16,18 * * 1-5 /path/to/AI_Employee_Vault/scripts/scheduler.sh email-check >> /tmp/ai_employee_email.log 2>&1

# Weekly review: Sunday at 8:00 PM
0 20 * * 0 /path/to/AI_Employee_Vault/scripts/scheduler.sh weekly-review >> /tmp/ai_employee_weekly.log 2>&1
```

### Cron Time Format

```
* * * * * command
│ │ │ │ │
│ │ │ │ └── Day of week (0-7, 0=Sunday)
│ │ │ └──── Month (1-12)
│ │ └────── Day of month (1-31)
│ └──────── Hour (0-23)
└────────── Minute (0-59)
```

### Common Patterns

| Pattern | Meaning |
|---------|---------|
| `0 8 * * *` | Daily at 8:00 AM |
| `0 9 * * 1,3,5` | Mon, Wed, Fri at 9:00 AM |
| `0 */2 * * *` | Every 2 hours |
| `0 9-17 * * 1-5` | Hourly, 9am-5pm, Mon-Fri |
| `0 20 * * 0` | Sundays at 8:00 PM |

### Verify Cron is Running

```bash
# Check if cron service is running
# Mac:
sudo launchctl list | grep cron

# Linux:
systemctl status cron

# View cron logs (Mac)
log show --predicate 'process == "cron"' --last 1h

# View cron logs (Linux)
grep CRON /var/log/syslog
```

---

## Windows: Task Scheduler Setup

### Option 1: PowerShell Script

Create `scripts/scheduler.ps1`:

```powershell
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("daily", "linkedin", "weekly-review", "check-approvals", "status")]
    [string]$Task
)

$VaultPath = "$env:USERPROFILE\AI_Employee_Vault"
Set-Location $VaultPath

switch ($Task) {
    "daily" {
        claude --print "Perform your daily morning routine..."
    }
    "linkedin" {
        claude --print "Generate a LinkedIn post draft..."
    }
    "weekly-review" {
        claude --print "Perform your weekly review..."
    }
    "check-approvals" {
        claude --print "Check the approval workflow status..."
    }
    "status" {
        Write-Host "Checking status..."
        Get-ChildItem -Directory | ForEach-Object {
            $count = (Get-ChildItem $_.FullName -File | Measure-Object).Count
            Write-Host "$($_.Name): $count items"
        }
    }
}
```

### Option 2: Task Scheduler GUI

1. **Open Task Scheduler**
   - Press `Win + R`, type `taskschd.msc`, press Enter

2. **Create New Task**
   - Click "Create Task" (not "Create Basic Task")

3. **General Tab**
   - Name: "AI Employee Daily Check"
   - Description: "Run AI Employee daily routine"
   - Check "Run whether user is logged on or not"

4. **Triggers Tab**
   - Click "New..."
   - Begin the task: "On a schedule"
   - Daily, Start: 8:00 AM
   - Click OK

5. **Actions Tab**
   - Click "New..."
   - Action: "Start a program"
   - Program: `bash.exe` (if using WSL) or `powershell.exe`
   - Arguments: `-c "/path/to/scheduler.sh daily"` or `-File scheduler.ps1 -Task daily`

6. **Conditions Tab**
   - Uncheck "Start only if on AC power" (if laptop)

7. **Settings Tab**
   - Check "Run task as soon as possible after scheduled start is missed"

### Create Multiple Tasks

Create separate tasks for each schedule:

| Task Name | Trigger | Command |
|-----------|---------|---------|
| AI Employee Daily | Daily 8:00 AM | `scheduler.sh daily` |
| AI Employee LinkedIn | Mon/Wed/Fri 9:00 AM | `scheduler.sh linkedin` |
| AI Employee Weekly | Sunday 8:00 PM | `scheduler.sh weekly-review` |
| AI Employee Approvals | Every 4 hours | `scheduler.sh check-approvals` |

### Verify Tasks are Running

1. Open Task Scheduler
2. Select your task
3. Check "Last Run Time" and "Last Run Result"
4. Result `0x0` = Success

---

## Verification

### Check Logs

```bash
# View scheduler logs
ls -la memory/scheduler_logs/

# View most recent log
cat memory/scheduler_logs/$(ls -t memory/scheduler_logs | head -1)
```

### Check /Done Folder

```bash
# See recently processed items
ls -lt Done/ | head -10
```

### Check Dashboard

Open `Dashboard.md` and verify:
- "Last Updated" timestamp is recent
- Counts match actual folder contents
- Recent Activity shows scheduled tasks

---

## Troubleshooting

### Cron Job Not Running

1. **Check PATH**: Cron has limited PATH. Use full paths:
   ```cron
   0 8 * * * /usr/local/bin/bash /full/path/to/scheduler.sh daily
   ```

2. **Check permissions**:
   ```bash
   chmod +x scripts/scheduler.sh
   ```

3. **Check Claude Code is available**:
   ```bash
   which claude
   # Use full path in cron: /usr/local/bin/claude
   ```

### Claude Not Found in Cron

Add to top of crontab:
```cron
PATH=/usr/local/bin:/usr/bin:/bin
SHELL=/bin/bash
```

### Windows Task Not Running

1. Check "Run with highest privileges"
2. Ensure user has "Log on as batch job" rights
3. Test manually: `schtasks /run /tn "AI Employee Daily"`

---

## Recommended Schedule Summary

| Task | Time | Days | Purpose |
|------|------|------|---------|
| Daily | 8:00 AM | Every day | Process items, update Dashboard |
| LinkedIn | 9:00 AM | Mon, Wed, Fri | Generate post drafts |
| Approvals | 9am, 1pm, 5pm | Weekdays | Check for pending approvals |
| Email | Every 2 hours | Weekdays | Check Gmail for new emails |
| Weekly Review | 8:00 PM | Sunday | Summarize week's activity |
