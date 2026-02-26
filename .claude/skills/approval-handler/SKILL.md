---
name: approval-handler
description: Manage the Human-in-the-Loop approval workflow. Create approval requests in /Pending_Approval for sensitive actions, monitor /Approved and /Rejected for human decisions.
version: 1.0.0
---

# Approval Handler

**SAFETY LAYER** - Manage human-in-the-loop approvals for sensitive actions.

## Critical Rule

```
⛔ NEVER bypass approval for actions listed in Company_Handbook.md
```

Before executing ANY action, check if it requires approval. If yes, CREATE the approval request and WAIT. Do not proceed without explicit human approval.

---

## When Approval is Required

Reference: `Company_Handbook.md` → Approval Rules

| Action Type | Trigger | Risk Level |
|-------------|---------|------------|
| `email_send` | Email to unknown/new contacts | medium |
| `email_bulk` | Any bulk email sends | high |
| `social_post` | Any social media posts | high |
| `file_delete` | File or folder deletion | medium |
| `payment` | Payments of any amount | high |

### How to Detect

Before executing, ask:

1. **Email?** → Is recipient in known contacts? If NO → approval required
2. **Social media?** → ALWAYS requires approval
3. **Deleting files?** → ALWAYS requires approval
4. **Sending money?** → ALWAYS requires approval
5. **Bulk operation?** → ALWAYS requires approval

---

## Step 1: Create Approval Request

When an action requires approval, create a file in `/Pending_Approval`.

### File Naming

```
APPROVAL_{action}_{target}_{YYYYMMDD_HHMMSS}.md
```

Examples:
- `APPROVAL_email_send_john_doe_20260220_143000.md`
- `APPROVAL_social_post_twitter_20260220_150000.md`
- `APPROVAL_file_delete_old_reports_20260220_160000.md`
- `APPROVAL_payment_vendor_invoice_20260220_170000.md`

### File Format

```markdown
---
type: approval_request
action: {email_send|email_bulk|social_post|file_delete|payment}
target: {recipient email|platform name|file path|payment recipient}
details: {one-line summary of what will happen}
created: {ISO-8601 timestamp}
expires: {ISO-8601 timestamp, 24 hours from creation}
status: pending
risk_level: {low|medium|high}
plan_reference: {path to plan if part of a plan, otherwise: none}
---

# Approval Request: {Action Type}

## Summary

**Action:** {What will be done}
**Target:** {Who/what is affected}
**Risk Level:** {low|medium|high}

## Action Details

{Full description of what will happen if approved}

- **Specific action:** {exactly what will execute}
- **Affected parties:** {who will be impacted}
- **Reversible:** {yes/no}

## Context

{Why this action is being proposed}

- **Triggered by:** {source file or user request}
- **Purpose:** {what this accomplishes}

## Risk Assessment

{Why this is classified at the stated risk level}

---

## Decision Required

### ✅ To Approve

Move this file to the `/Approved` folder.

### ❌ To Reject

Move this file to the `/Rejected` folder.

---

**Expires:** {human-readable expiration time}

_This request will be flagged as expired after 24 hours._
```

---

## Step 2: Wait for Human Decision

After creating the approval request:

1. **Update Dashboard.md** - increment Pending_Approval count
2. **STOP execution** of the current action
3. **Do NOT poll continuously** - check when next invoked

### Checking for Decisions

```bash
# Check for approved requests
ls Approved/

# Check for rejected requests
ls Rejected/
```

---

## Step 3: Handle Approved Actions

When a file appears in `/Approved`:

### 3a. Read the Approval

```bash
cat Approved/APPROVAL_{name}.md
```

Extract:
- What action to execute
- Target/recipient
- Original context

### 3b. Execute the Action

Use the appropriate method:
- **Email:** Gmail MCP server or API
- **Social:** Platform MCP server
- **File delete:** File system operation
- **Payment:** Payment MCP server

### 3c. Log the Result

Create execution log entry:

```markdown
## Execution Log

- **Approved by:** Human (file moved to /Approved)
- **Approved at:** {timestamp when file appeared in /Approved}
- **Executed at:** {timestamp of execution}
- **Result:** {success|failed}
- **Details:** {any relevant output}
```

### 3d. Complete the Workflow

1. Move file to `/Done`:
   ```
   DONE_APPROVAL_{action}_{target}_{timestamp}.md
   ```

2. Update Dashboard.md:
   - Decrement Pending_Approval count
   - Increment Done count
   - Add to Recent Activity:
     ```
     | {timestamp} | Executed approved {action} | ✅ Complete |
     ```

3. If linked to a Plan:
   - Update the plan's step as completed
   - Continue plan execution

---

## Step 4: Handle Rejected Actions

When a file appears in `/Rejected`:

### 4a. Read the Rejection

```bash
cat Rejected/APPROVAL_{name}.md
```

### 4b. Log the Rejection

Add to the file:

```markdown
## Rejection Log

- **Rejected by:** Human (file moved to /Rejected)
- **Rejected at:** {timestamp}
- **Action:** NOT executed
```

### 4c. Complete the Workflow

1. Move file to `/Done`:
   ```
   DONE_REJECTED_{action}_{target}_{timestamp}.md
   ```

2. Update Dashboard.md:
   - Decrement Pending_Approval count
   - Increment Done count
   - Add to Recent Activity:
     ```
     | {timestamp} | Rejected {action} request | ❌ Rejected |
     ```

3. If linked to a Plan:
   - Mark the plan step as `blocked` or `skipped`
   - Add note explaining rejection
   - Ask whether to continue with remaining steps

### 4d. Do NOT Retry

```
⛔ NEVER retry a rejected action
⛔ NEVER create a new approval for the same action
```

If the action is critical to a plan, mark the plan as blocked and await human guidance.

---

## Step 5: Handle Expirations

Check for expired requests (older than 24 hours in `/Pending_Approval`):

### Detection

```python
# Pseudocode
created_time = parse(frontmatter['created'])
if now - created_time > 24 hours:
    mark_as_expired()
```

### Expiration Process

1. Update the file's frontmatter:
   ```yaml
   status: expired
   ```

2. Add expiration notice:
   ```markdown
   ## ⚠️ EXPIRED

   This approval request expired on {expiration_time}.

   No action was taken. If this action is still needed,
   create a new request.
   ```

3. Move to `/Done`:
   ```
   DONE_EXPIRED_{action}_{target}_{timestamp}.md
   ```

4. Update Dashboard.md

---

## Quick Reference

### Approval Actions

| Code | Action | Risk |
|------|--------|------|
| `email_send` | Send email to new contact | medium |
| `email_bulk` | Send bulk emails | high |
| `social_post` | Post to social media | high |
| `file_delete` | Delete files | medium |
| `payment` | Send payment | high |

### File Locations

| Status | Location |
|--------|----------|
| Awaiting decision | `/Pending_Approval` |
| Human approved | `/Approved` |
| Human rejected | `/Rejected` |
| Completed/Archived | `/Done` |

### Status Values

| Status | Meaning |
|--------|---------|
| `pending` | Awaiting human decision |
| `approved` | Human approved, ready to execute |
| `rejected` | Human rejected, do not execute |
| `expired` | 24 hours passed, no decision made |
| `executed` | Action completed successfully |
| `failed` | Action attempted but failed |

---

## Safety Checklist

Before ANY sensitive action, verify:

- [ ] Checked Company_Handbook.md Approval Rules
- [ ] Action requires approval? If yes:
  - [ ] Created approval request in /Pending_Approval
  - [ ] Updated Dashboard.md
  - [ ] STOPPED execution to wait for human
- [ ] Found approval in /Approved before executing
- [ ] Logged execution result
- [ ] Moved completed request to /Done

```
Remember: When in doubt, request approval.
It's better to wait than to act without authorization.
```
