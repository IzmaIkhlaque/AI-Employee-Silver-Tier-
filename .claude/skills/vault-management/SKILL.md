---
name: vault-management
description: Manage the Obsidian vault - update Dashboard.md, track file counts across folders, maintain the folder structure.
version: 1.0.0
---

# Vault Management

Maintain the AI Employee vault structure and keep Dashboard.md up to date.

## Counting Files in Each Folder

Count markdown files in each folder:

```bash
# Count Inbox items
ls -1 Inbox/*.md 2>/dev/null | wc -l

# Count Needs_Action items
ls -1 Needs_Action/*.md 2>/dev/null | wc -l

# Count Done items
ls -1 Done/*.md 2>/dev/null | wc -l
```

## Updating Dashboard.md

### Update Today's Summary

Replace the counts in the summary table:

```markdown
## Today's Summary

| Folder | Count |
|--------|-------|
| Inbox | [current count] |
| Needs_Action | [current count] |
| Done | [current count] |
```

### Update Recent Activity Table

Add new entries to the top of the activity table:

```markdown
## Recent Activity

| Timestamp | Action | Status |
|-----------|--------|--------|
| YYYY-MM-DD HH:MM:SS | [action description] | [status] |
```

**Action examples:**
- "Processed EMAIL from client"
- "Filed invoice to Done"
- "System health check"

**Status values:**
- ✅ Complete
- ⏳ In Progress
- ❌ Failed

### Update System Status Section

Update component status and last check time:

```markdown
## System Status

| Component | Status | Last Check |
|-----------|--------|------------|
| File Watcher | [status] | [timestamp] |
| Claude Code | [status] | [timestamp] |
```

**Status values:**
- 🟢 Running
- 🟡 Idle
- 🔴 Not Started

### Update Last Updated Timestamp

Always update the header timestamp when making any changes:

```markdown
**Last Updated:** YYYY-MM-DD HH:MM:SS
```

## Maintaining Folder Structure

Ensure these folders always exist:
- `/Inbox` - New items waiting to be triaged
- `/Needs_Action` - Items requiring processing
- `/Done` - Completed items

```bash
# Verify folder structure
mkdir -p Inbox Needs_Action Done
```
