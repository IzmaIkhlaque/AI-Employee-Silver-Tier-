---
name: scheduling
description: Manage scheduled tasks for the AI Employee. Handles daily routines, LinkedIn posting schedule, and weekly reviews.
version: 1.0.0
---

# Scheduling

Manage the AI Employee's scheduled tasks and automated routines.

## Overview

The AI Employee runs on a schedule defined by cron (Mac/Linux) or Task Scheduler (Windows). This skill documents what each scheduled task does.

---

## Scheduled Tasks

### 1. Daily Morning Routine

**Schedule:** Every day at 8:00 AM
**Command:** `./scripts/scheduler.sh daily`

**What it does:**
1. Check `/Needs_Action` for new items
2. Process each item using `file-processing` skill
3. Check `/Approved` for actions ready to execute
4. Update `Dashboard.md` with current counts
5. Report items needing human attention

**Expected output:**
- Items moved from `/Needs_Action` to `/Done`
- Dashboard updated with correct counts
- Log file in `memory/scheduler_logs/daily_*.log`

---

### 2. LinkedIn Post Generation

**Schedule:** Monday, Wednesday, Friday at 9:00 AM
**Command:** `./scripts/scheduler.sh linkedin`

**What it does:**
1. Read `Business_Goals.md` for context
2. Check Content Calendar for today's content type
3. Generate engaging post following guidelines
4. Save draft to `/Pending_Approval`

**Expected output:**
- New file in `/Pending_Approval`:
  `APPROVAL_social_post_linkedin_{topic}_{timestamp}.md`
- Dashboard updated with new pending count
- Log file in `memory/scheduler_logs/linkedin_*.log`

**Human action required:**
- Review the draft
- Move to `/Approved` to post, or `/Rejected` to discard

---

### 3. Weekly Review

**Schedule:** Sunday at 8:00 PM
**Command:** `./scripts/scheduler.sh weekly-review`

**What it does:**
1. Count completed tasks in `/Done` from past 7 days
2. Flag stale items in `/Pending_Approval` (>48 hours)
3. Review `/Rejected` items for follow-up
4. Check `/Plans` for incomplete plans
5. Update Dashboard with weekly summary

**Expected output:**
- Weekly summary added to Dashboard
- Stale items flagged for attention
- Log file in `memory/scheduler_logs/weekly_*.log`

---

### 4. Approval Check

**Schedule:** Every 4 hours during work hours (9am, 1pm, 5pm)
**Command:** `./scripts/scheduler.sh check-approvals`

**What it does:**
1. List all items in `/Pending_Approval`
2. Flag items older than 24 hours
3. Check `/Approved` for items to execute
4. Check `/Rejected` for acknowledgment
5. Update Dashboard Pending Approvals section

**Expected output:**
- Dashboard Pending Approvals section updated
- Approved items executed
- Log file in `memory/scheduler_logs/approvals_*.log`

---

### 5. Email Check

**Schedule:** Every 2 hours during work hours
**Command:** `./scripts/scheduler.sh email-check`

**What it does:**
1. Run Gmail watcher for one cycle
2. Check for unread important emails
3. Create action files in `/Needs_Action`
4. Update processed email IDs

**Expected output:**
- New email items in `/Needs_Action`
- `memory/gmail_processed_ids.json` updated
- Log file in `memory/scheduler_logs/`

---

## Running Tasks Manually

You can run any scheduled task manually:

```bash
# Run daily routine now
./scripts/scheduler.sh daily

# Generate LinkedIn post now
./scripts/scheduler.sh linkedin

# Run weekly review now
./scripts/scheduler.sh weekly-review

# Check pending approvals
./scripts/scheduler.sh check-approvals

# Check system status
./scripts/scheduler.sh status
```

---

## Schedule Configuration

### Current Schedule

| Task | Time | Days | Cron Expression |
|------|------|------|-----------------|
| Daily | 8:00 AM | Daily | `0 8 * * *` |
| LinkedIn | 9:00 AM | Mon, Wed, Fri | `0 9 * * 1,3,5` |
| Approvals | 9am, 1pm, 5pm | Weekdays | `0 9,13,17 * * 1-5` |
| Email | Every 2 hours | Weekdays | `0 8,10,12,14,16,18 * * 1-5` |
| Weekly | 8:00 PM | Sunday | `0 20 * * 0` |

### Modifying the Schedule

1. Edit crontab: `crontab -e`
2. Change timing as needed
3. Save and verify: `crontab -l`

See `docs/cron-setup.md` for detailed instructions.

---

## Logs and Monitoring

### Log Location

All scheduler logs are saved to:
```
memory/scheduler_logs/
├── daily_2026-02-23_08-00-00.log
├── linkedin_2026-02-23_09-00-00.log
├── weekly_2026-02-23_20-00-00.log
└── ...
```

### Viewing Logs

```bash
# List recent logs
ls -lt memory/scheduler_logs/ | head -10

# View specific log
cat memory/scheduler_logs/daily_2026-02-23_08-00-00.log

# Follow latest log
tail -f memory/scheduler_logs/$(ls -t memory/scheduler_logs | head -1)
```

### Checking Status

```bash
./scripts/scheduler.sh status
```

Shows:
- Current folder counts
- Recent log files
- System health

---

## Troubleshooting

### Task Didn't Run

1. Check if cron is running:
   ```bash
   crontab -l  # Verify entries exist
   ```

2. Check logs for errors:
   ```bash
   cat memory/scheduler_logs/daily_*.log | tail -50
   ```

3. Run manually to test:
   ```bash
   ./scripts/scheduler.sh daily
   ```

### Claude Not Found

Ensure Claude Code is in PATH. Add to crontab:
```cron
PATH=/usr/local/bin:/usr/bin:/bin
```

### Permissions Error

```bash
chmod +x scripts/scheduler.sh
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `./scripts/scheduler.sh daily` | Run daily routine |
| `./scripts/scheduler.sh linkedin` | Generate LinkedIn draft |
| `./scripts/scheduler.sh weekly-review` | Run weekly summary |
| `./scripts/scheduler.sh check-approvals` | Check approval queue |
| `./scripts/scheduler.sh email-check` | Check for new emails |
| `./scripts/scheduler.sh status` | View system status |
| `./scripts/scheduler.sh help` | Show help |
