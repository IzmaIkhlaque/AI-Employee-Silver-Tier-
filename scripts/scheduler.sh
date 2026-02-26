#!/bin/bash
#
# AI Employee Scheduled Tasks
#
# Usage:
#   ./scheduler.sh daily          - Morning routine
#   ./scheduler.sh linkedin       - Generate LinkedIn post draft
#   ./scheduler.sh weekly-review  - Weekly summary
#   ./scheduler.sh check-approvals - Check for pending approvals
#   ./scheduler.sh email-check    - Check Gmail for new emails
#

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT_PATH="${VAULT_PATH:-$(dirname "$SCRIPT_DIR")}"
LOG_DIR="$VAULT_PATH/memory/scheduler_logs"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Logging function
log() {
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $1" | tee -a "$LOG_DIR/scheduler_$TIMESTAMP.log"
}

log "Starting scheduler task: $1"
log "Vault path: $VAULT_PATH"

case "$1" in
    daily)
        # Run daily morning check: process /Needs_Action, update Dashboard
        log "Running daily morning routine..."
        cd "$VAULT_PATH"

        claude --print "
Perform your daily morning routine:

1. Check /Needs_Action for any new items
2. Process each item using the file-processing skill
3. Check /Approved for any actions ready to execute
4. Update Dashboard.md with current folder counts
5. Report any items that need human attention

Be thorough but concise. Update the Dashboard timestamp.
" 2>&1 | tee -a "$LOG_DIR/daily_$TIMESTAMP.log"

        log "Daily routine completed"
        ;;

    linkedin)
        # Generate LinkedIn post drafts (2-3 per week)
        log "Generating LinkedIn post draft..."
        cd "$VAULT_PATH"

        claude --print "
Generate a LinkedIn post draft using the linkedin-posting skill.

1. Read Business_Goals.md to understand the business and content strategy
2. Check the Content Calendar for today's content type
3. Generate an engaging post following the guidelines
4. Save the draft to /Pending_Approval with proper frontmatter:
   - type: approval_request
   - action: social_post
   - platform: linkedin
   - created: (ISO timestamp)
   - status: pending

Make sure the post is under 3000 characters and includes 3-5 hashtags.
" 2>&1 | tee -a "$LOG_DIR/linkedin_$TIMESTAMP.log"

        log "LinkedIn draft generation completed"
        ;;

    weekly-review)
        # Weekly task review
        log "Running weekly review..."
        cd "$VAULT_PATH"

        claude --print "
Perform your weekly review:

1. Count completed tasks in /Done from the past 7 days
2. Check for stale items in /Pending_Approval (older than 48 hours)
3. Review any items in /Rejected that need follow-up
4. Check /Plans for any incomplete plans
5. Update Dashboard.md with a weekly summary section
6. List any items that need immediate attention

Provide a brief summary of the week's activity.
" 2>&1 | tee -a "$LOG_DIR/weekly_$TIMESTAMP.log"

        log "Weekly review completed"
        ;;

    check-approvals)
        # Check for items awaiting approval
        log "Checking pending approvals..."
        cd "$VAULT_PATH"

        claude --print "
Check the approval workflow status:

1. List all items in /Pending_Approval
2. Flag any items older than 24 hours as needing attention
3. Check /Approved for items ready to execute
4. Check /Rejected for items that need acknowledgment
5. Update Dashboard.md Pending Approvals section

Report what needs human attention.
" 2>&1 | tee -a "$LOG_DIR/approvals_$TIMESTAMP.log"

        log "Approval check completed"
        ;;

    email-check)
        # Run Gmail watcher once
        log "Checking for new emails..."
        cd "$VAULT_PATH"

        # Run the Gmail watcher for one cycle
        if [ -f "watchers/gmail_watcher.py" ]; then
            python watchers/gmail_watcher.py --vault-path "$VAULT_PATH" &
            WATCHER_PID=$!
            sleep 30  # Let it run one cycle
            kill $WATCHER_PID 2>/dev/null || true
            log "Email check completed"
        else
            log "Gmail watcher not found"
        fi
        ;;

    status)
        # Show current system status
        log "Checking system status..."
        cd "$VAULT_PATH"

        echo "=== AI Employee Status ==="
        echo ""
        echo "Folder Counts:"
        echo "  Inbox:            $(ls -1 Inbox 2>/dev/null | wc -l | tr -d ' ')"
        echo "  Needs_Action:     $(ls -1 Needs_Action 2>/dev/null | wc -l | tr -d ' ')"
        echo "  Plans:            $(ls -1 Plans 2>/dev/null | wc -l | tr -d ' ')"
        echo "  Pending_Approval: $(ls -1 Pending_Approval 2>/dev/null | wc -l | tr -d ' ')"
        echo "  Approved:         $(ls -1 Approved 2>/dev/null | wc -l | tr -d ' ')"
        echo "  Rejected:         $(ls -1 Rejected 2>/dev/null | wc -l | tr -d ' ')"
        echo "  Done:             $(ls -1 Done 2>/dev/null | wc -l | tr -d ' ')"
        echo ""
        echo "Recent Logs:"
        ls -lt "$LOG_DIR" 2>/dev/null | head -5
        ;;

    help|--help|-h)
        echo "AI Employee Scheduler"
        echo ""
        echo "Usage: ./scheduler.sh <command>"
        echo ""
        echo "Commands:"
        echo "  daily           - Run daily morning routine"
        echo "  linkedin        - Generate LinkedIn post draft"
        echo "  weekly-review   - Run weekly task review"
        echo "  check-approvals - Check pending approvals"
        echo "  email-check     - Check Gmail for new emails"
        echo "  status          - Show current system status"
        echo "  help            - Show this help message"
        echo ""
        echo "Environment:"
        echo "  VAULT_PATH      - Override vault path (default: parent of scripts/)"
        ;;

    *)
        echo "Unknown command: $1"
        echo "Run './scheduler.sh help' for usage"
        exit 1
        ;;
esac

log "Task completed: $1"
