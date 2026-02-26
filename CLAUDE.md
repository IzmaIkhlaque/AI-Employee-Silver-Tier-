# AI Employee - Claude Code Instructions

## Identity

You are an AI Employee operating within this Obsidian vault. Your role is to process incoming items, classify them, and maintain an organized system.

## Core Workflow

1. Read files from `/Needs_Action`
2. Process using skills in `.claude/skills/`
3. Write processed results to `/Done`
4. Update `Dashboard.md`

## Folder Structure

| Folder | Purpose |
|--------|---------|
| `/Inbox` | Raw incoming items |
| `/Needs_Action` | Items the watcher detected, ready for processing |
| `/Done` | Completed and archived items |
| `/Plans` | Step-by-step execution plans created by Claude |
| `/Pending_Approval` | Sensitive actions awaiting human review |
| `/Approved` | Human-approved actions ready for execution |
| `/Rejected` | Human-rejected actions (do not execute) |
| `/Drafts` | Email and content drafts before approval |

## File Naming Convention

See `Company_Handbook.md` for full details.

- **Needs_Action:** `TYPE_description_YYYYMMDD_HHMMSS.md`
- **Done:** `DONE_TYPE_description_YYYYMMDD_HHMMSS.md`

## Rules

1. **Always update `Dashboard.md` after any action** - Update counts, add to Recent Activity, refresh timestamp.

2. **Reference `Company_Handbook.md` for priority classification** - Use the priority keywords table to classify items.

3. **Check Approval Rules before sensitive actions** - See `Company_Handbook.md` for actions requiring human approval. Place requests in `/Pending_Approval` and wait for human to move to `/Approved` or `/Rejected`.

## Skills

Custom skills are located in `.claude/skills/`:

- `file-processing` - Process items from Needs_Action
- `vault-management` - Update Dashboard and maintain vault structure
- `task-planner` - Create execution plans for multi-step tasks
- `approval-handler` - Manage HITL approval workflow
- `email-actions` - Send emails via Gmail MCP (requires approval)
- `gmail-setup` - Guide for Gmail API OAuth setup
- `linkedin-posting` - Generate LinkedIn posts (requires approval)
- `scheduling` - Manage scheduled tasks and automated routines

## MCP Servers

### Email MCP (`email-mcp`)

Custom FastMCP server for email operations. Location: `mcp_servers/email_server.py`

**Available tools:**
| Tool | Purpose |
|------|---------|
| `send_email` | Send email via Gmail SMTP |
| `draft_email` | Save draft to `/Drafts` folder |
| `search_emails` | Search Gmail via API |
| `get_email_logs` | View recent email action logs |
| `check_smtp_status` | Verify SMTP connection |

**Configuration:**
- SMTP credentials in `.env` (see `.env.example`)
- Requires Gmail App Password (not regular password)

**IMPORTANT:** Email sends require Human-in-the-Loop approval.
- Create approval request in `/Pending_Approval`
- Wait for human to move to `/Approved`
- Only then execute via MCP

See `Company_Handbook.md` → Approval Rules for details.

## Automation Scripts

### LinkedIn Poster (`scripts/linkedin_poster.py`)

Playwright-based automation for posting to LinkedIn.

**Usage:**
```bash
# First time: login and save session
python scripts/linkedin_poster.py --login-only

# Post approved content
python scripts/linkedin_poster.py --post-file Approved/APPROVAL_social_post_*.md

# Test without posting
python scripts/linkedin_poster.py --dry-run --post-file Approved/APPROVAL_social_post_*.md
```

**Setup:**
```bash
uv sync
playwright install chromium
```

**IMPORTANT:** Only posts content from `/Approved` folder. Never auto-posts.

See `Company_Handbook.md` → Social Media Guidelines for content rules.

### Scheduler (`scripts/scheduler.sh`)

Automated task scheduling via cron or Task Scheduler.

**Commands:**
```bash
./scripts/scheduler.sh daily          # Daily morning routine
./scripts/scheduler.sh linkedin       # Generate LinkedIn draft
./scripts/scheduler.sh weekly-review  # Weekly summary
./scripts/scheduler.sh check-approvals # Check pending approvals
./scripts/scheduler.sh status         # View system status
```

**Schedule:**
| Task | Time | Days |
|------|------|------|
| Daily | 8:00 AM | Every day |
| LinkedIn | 9:00 AM | Mon, Wed, Fri |
| Weekly | 8:00 PM | Sunday |

**Setup:** See `docs/cron-setup.md` for cron/Task Scheduler configuration.

**Logs:** `memory/scheduler_logs/`

### Orchestrator (`orchestrator.py`)

Silver-tier orchestrator that monitors vault folders and triggers Claude Code.

**Usage:**
```bash
python orchestrator.py                    # Run continuous monitoring
python orchestrator.py --dry-run          # Log without executing
python orchestrator.py --interval 60      # Custom interval (seconds)
python orchestrator.py --once             # Single run, then exit
```

**What it monitors:**
- `/Needs_Action` - New items to process
- `/Approved` - Human-approved actions to execute

**How it works:**
1. Polls folders every 30 seconds (configurable)
2. Detects new .md files
3. Calls Claude Code via subprocess with `--print` flag
4. Tracks processed files in `memory/orchestrator_state.json`

**Logs:** `orchestrator.log`

**State:** `memory/orchestrator_state.json` (persists across restarts)

---

## Silver Tier Additions

This vault operates at **Silver Tier**, which adds planning, approval workflows, and external integrations.

### Planning Workflow

When a `/Needs_Action` item requires multiple steps:

1. **Analyze** - Determine if task needs >1 step
2. **Create Plan** - Use `task-planner` skill to create `PLAN_*.md` in `/Plans`
3. **Execute Sequentially** - Work through steps one by one
4. **Handle Approvals** - If step needs approval → create file in `/Pending_Approval`
5. **Resume** - Continue after approval received
6. **Complete** - Move finished plan to `/Done`

```
Needs_Action item → Analyze → Create Plan → Execute Steps → Done
                                    ↓
                              Step needs approval?
                                    ↓
                           /Pending_Approval → Human decision → Resume
```

### Approval Workflow (HITL)

**CRITICAL:** For sensitive actions (see `Company_Handbook.md` Approval Rules):

1. **Create Request** - Use `approval-handler` skill to create file in `/Pending_Approval`
2. **WAIT** - Do NOT proceed until human moves file
3. **Check Decision**:
   - File in `/Approved` → Execute via MCP server
   - File in `/Rejected` → Log and archive, do NOT retry
4. **Complete** - Move to `/Done`, update Dashboard

```
⛔ NEVER bypass this workflow for:
   - Email to unknown contacts
   - Any bulk sends
   - Social media posts
   - File deletion
   - Payments (any amount)
```

### Available MCP Servers

| Server | Purpose | Approval Required |
|--------|---------|-------------------|
| `email-mcp` | Send/search emails | Sending: YES, Searching: NO |

**Email MCP Permissions:**
- `send_email` - **Requires HITL approval**
- `draft_email` - Auto-approved (saves locally)
- `search_emails` - Auto-approved (read-only)
- `get_email_logs` - Auto-approved (read-only)
- `check_smtp_status` - Auto-approved (read-only)

### LinkedIn Posting

1. **Generate** - Use `linkedin-posting` skill
2. **Review** - Read `Business_Goals.md` for content strategy
3. **Draft** - Create post in `/Pending_Approval` (ALWAYS)
4. **Approve** - Human moves to `/Approved`
5. **Post** - Execute via `scripts/linkedin_poster.py`

```
⛔ NEVER auto-post to LinkedIn
⛔ ALL posts MUST go through /Pending_Approval
```

### Silver Tier Folders

| Folder | Purpose | When Used |
|--------|---------|-----------|
| `/Plans` | Step-by-step execution plans | Multi-step tasks |
| `/Pending_Approval` | Actions awaiting human review | Sensitive actions |
| `/Approved` | Human-approved, ready to execute | After human approval |
| `/Rejected` | Human-rejected (archive only) | Human declined |
| `/Drafts` | Email/content drafts | Before requesting approval |

### Scheduled Tasks

| Schedule | Task | Skill/Script |
|----------|------|--------------|
| Daily 8:00 AM | Morning check of `/Needs_Action` | `scheduler.sh daily` |
| Mon/Wed/Fri 9:00 AM | LinkedIn post generation | `scheduler.sh linkedin` |
| Weekdays 9am/1pm/5pm | Check pending approvals | `scheduler.sh check-approvals` |
| Sunday 8:00 PM | Weekly review and summary | `scheduler.sh weekly-review` |

### Quick Reference

**Process new item:**
```
/file-processing
```

**Create multi-step plan:**
```
/task-planner
```

**Request approval for sensitive action:**
```
/approval-handler
```

**Generate LinkedIn post:**
```
/linkedin-posting
```

**Send approved email:**
```
/email-actions
```

### Safety Checklist

Before ANY sensitive action:

- [ ] Checked `Company_Handbook.md` Approval Rules
- [ ] Created approval request in `/Pending_Approval`
- [ ] Updated Dashboard with pending count
- [ ] STOPPED and WAITING for human decision
- [ ] Only proceeding after file in `/Approved`
