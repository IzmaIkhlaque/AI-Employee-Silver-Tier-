# Personal AI Employee — Silver Tier

## What It Is

A personal AI employee that monitors multiple sources (files, Gmail), processes items using Claude Code, and executes actions through MCP servers. Features Human-in-the-Loop (HITL) approval for sensitive actions, automated LinkedIn posting, and scheduled tasks.

## Tier

**Silver** — Multi-source monitoring, MCP integrations, HITL approval workflow, LinkedIn automation, scheduled tasks.

## Architecture

```
External Sources (Gmail, Files, LinkedIn)
        │
        ▼
┌── Perception Layer (Watchers) ──┐
│  Gmail Watcher │ File Watcher   │
└────────────┬───────────────────┘
             │ Creates .md files
             ▼
┌── Obsidian Vault ──────────────────────────────┐
│  /Needs_Action → /Plans → /Pending_Approval    │
│  Dashboard.md  │ Company_Handbook.md           │
└────────────┬───────────────────────────────────┘
             ▼
┌── Claude Code ─────────────────┐
│  Read → Think → Plan → Act     │
│  Uses skills from .claude/     │
└────────────┬───────────────────┘
             ▼
┌── HITL ────────────┐    ┌── MCP Servers ──┐
│ /Pending_Approval  │ →  │ Gmail MCP       │
│     ↓              │    │ (send email)    │
│ /Approved          │    │                 │
│     ↓              │    │ LinkedIn        │
│ Execute Action     │    │ (Playwright)    │
└────────────────────┘    └─────────────────┘
             │
             ▼
┌── /Done ───────────┐
│ Archived results   │
│ Audit trail        │
└────────────────────┘
```

## Tech Stack

| Component | Purpose |
|-----------|---------|
| Claude Code | AI processing, planning, and task execution |
| Obsidian | Vault interface and dashboard viewing |
| Python + watchdog | File system monitoring |
| Gmail API | Email monitoring and sending |
| FastMCP | Custom MCP server for email |
| Playwright | LinkedIn browser automation |
| Cron / Task Scheduler | Scheduled task execution |

## Silver Tier Components

| Component | Description |
|-----------|-------------|
| **File Watcher** | Monitors drop folder, creates action items |
| **Gmail Watcher** | Monitors inbox for important emails |
| **Email MCP** | Send emails via Gmail SMTP (with approval) |
| **LinkedIn Poster** | Playwright automation for posting |
| **Orchestrator** | Monitors folders, triggers Claude Code |
| **Scheduler** | Cron-based daily/weekly routines |
| **HITL Workflow** | Human approval for sensitive actions |

## Prerequisites

- Claude Code CLI
- Python 3.13+
- uv (Python package manager)
- Obsidian
- Node.js v24+
- Gmail account (for email features)
- LinkedIn account (for posting features)

## Quick Start

### 1. Clone and Install

```bash
# Clone repo
git clone <repo-url>
cd AI_Employee_Vault

# Install Python dependencies
uv sync

# Install Playwright browser
playwright install chromium
```

### 2. Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit .env with your settings:
# - SMTP_USER: Your Gmail address
# - SMTP_PASSWORD: Gmail App Password (not regular password)
```

### 3. Gmail API Setup

```bash
# Follow the gmail-setup skill instructions
# Or run the setup script:
./scripts/setup_gmail_mcp.sh
```

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create project → Enable Gmail API
3. Create OAuth 2.0 credentials (Desktop App)
4. Download as `config/credentials.json`
5. Run watcher once to complete OAuth flow

### 4. MCP Server Setup

```bash
# Add Email MCP to Claude Code
claude mcp add email-mcp -- uv run python mcp_servers/email_server.py

# Verify connection
# Run /mcp in Claude Code
```

### 5. Open in Obsidian

```
File → Open Vault → Select AI_Employee_Vault folder
```

### 6. Start the System

```bash
# Option A: Run orchestrator (monitors folders, triggers Claude)
python orchestrator.py

# Option B: Run watchers separately
python watchers/filesystem_watcher.py &
python watchers/gmail_watcher.py &

# Option C: Set up cron for scheduled tasks
crontab -e
# Add entries from docs/cron-setup.md
```

### 7. Test It

```bash
# Drop a file into watch folder
cp test.txt ~/AI_Drop/

# Check /Needs_Action in Obsidian
# Watch it get processed to /Done
```

## Folder Structure

```
AI_Employee_Vault/
├── Inbox/                  # Raw incoming items
├── Needs_Action/           # Items ready for processing
├── Plans/                  # Multi-step execution plans
├── Pending_Approval/       # Actions awaiting human approval
├── Approved/               # Human-approved actions
├── Rejected/               # Human-rejected actions
├── Drafts/                 # Email/content drafts
├── Done/                   # Completed items
├── memory/                 # Persistent state files
├── config/                 # Credentials and tokens
├── watchers/               # Python file watchers
│   ├── base_watcher.py
│   ├── filesystem_watcher.py
│   └── gmail_watcher.py
├── mcp_servers/            # MCP server implementations
│   └── email_server.py
├── scripts/                # Automation scripts
│   ├── scheduler.sh
│   └── linkedin_poster.py
├── docs/                   # Documentation
│   └── cron-setup.md
├── .claude/skills/         # Agent skills
├── orchestrator.py         # Folder monitor + Claude trigger
├── Dashboard.md            # Real-time status
├── Company_Handbook.md     # Rules and approval policies
├── Business_Goals.md       # Content strategy
└── CLAUDE.md               # Claude Code instructions
```

## Agent Skills

| Skill | Description |
|-------|-------------|
| `file-processing` | Process items from /Needs_Action, classify priority |
| `vault-management` | Update Dashboard.md, track file counts |
| `task-planner` | Create step-by-step plans for complex tasks |
| `approval-handler` | Manage HITL approval workflow |
| `email-actions` | Send emails via MCP (requires approval) |
| `gmail-setup` | Guide for Gmail API OAuth setup |
| `linkedin-posting` | Generate LinkedIn post drafts |
| `scheduling` | Manage scheduled tasks |

## HITL Approval Workflow

Sensitive actions require human approval:

```
1. Claude creates request → /Pending_Approval
2. Human reviews in Obsidian
3. Human moves file:
   → /Approved (proceed with action)
   → /Rejected (cancel, don't retry)
4. Claude executes or archives
5. Result logged in /Done
```

**Actions requiring approval:**
- Email to unknown contacts
- Bulk email sends
- Social media posts
- File deletion
- Payments (any amount)

## Scheduled Tasks

| Schedule | Task | Command |
|----------|------|---------|
| Daily 8:00 AM | Process /Needs_Action | `scheduler.sh daily` |
| Mon/Wed/Fri 9:00 AM | Generate LinkedIn draft | `scheduler.sh linkedin` |
| Weekdays 9am/1pm/5pm | Check approvals | `scheduler.sh check-approvals` |
| Sunday 8:00 PM | Weekly review | `scheduler.sh weekly-review` |

Setup: See `docs/cron-setup.md`

## MCP Servers

### Email MCP (`email-mcp`)

| Tool | Purpose | Approval |
|------|---------|----------|
| `send_email` | Send via Gmail SMTP | Required |
| `draft_email` | Save to /Drafts | Auto |
| `search_emails` | Search Gmail | Auto |
| `get_email_logs` | View action logs | Auto |
| `check_smtp_status` | Test connection | Auto |

## Security Notes

- **Credentials:** Store in `.env` (gitignored) and `config/` folder
- **App Passwords:** Use Gmail App Passwords, not regular passwords
- **Approval Workflow:** Never bypass for sensitive actions
- **Token Storage:** OAuth tokens in `config/token.json`
- **Audit Trail:** Actions logged in `/Done` and `memory/` files

## Upgrading to Gold Tier

Gold tier adds:
- Full autonomous agent loop
- Comprehensive audit logging
- PM2 process management
- Multi-agent coordination
- Advanced error recovery
- Real-time monitoring dashboard

## License

MIT
