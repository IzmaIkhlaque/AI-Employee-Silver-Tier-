---
name: email-actions
description: Send emails using the Gmail MCP server. Use when an approved action requires sending an email. Always check /Approved folder first - never send without approval.
version: 1.0.0
---

# Email Actions

Send and manage emails using the Gmail MCP server.

## Critical Safety Rule

```
⛔ NEVER send an email without approval
```

Before sending ANY email to an external or unknown contact, you MUST:
1. Have a file in `/Approved` authorizing the send
2. Verify the approval matches the intended recipient
3. Only then execute the send

---

## Prerequisites

The Email MCP server must be configured:

```bash
# 1. Configure SMTP credentials in .env
cp .env.example .env
# Edit .env with your Gmail app password

# 2. Install dependencies
uv sync

# 3. Add MCP to Claude Code
claude mcp add email-mcp -- uv run python mcp_servers/email_server.py
```

Verify with `/mcp` command - should show `email-mcp` in the list.

---

## Available MCP Tools

### send_email

Send an email via Gmail SMTP. **Requires approval first!**

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `to` | string | Yes | Recipient email(s), comma-separated |
| `subject` | string | Yes | Email subject line |
| `body` | string | Yes | Email body (plain text or HTML) |
| `cc` | string | No | CC recipients |
| `bcc` | string | No | BCC recipients |
| `html` | bool | No | Treat body as HTML (default: false) |

**Example:**
```
send_email(
  to: "john@example.com",
  subject: "Project Update",
  body: "Hello John,\n\nHere is the update..."
)
```

### draft_email

Save an email draft without sending. Drafts go to `/Drafts` folder.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `to` | string | Yes | Intended recipient(s) |
| `subject` | string | Yes | Email subject line |
| `body` | string | Yes | Email body content |
| `cc` | string | No | CC recipients |
| `notes` | string | No | Internal notes about the draft |

**Example:**
```
draft_email(
  to: "client@example.com",
  subject: "Proposal",
  body: "Dear Client...",
  notes: "Needs review before sending"
)
```

### search_emails

Search Gmail for emails (uses Gmail API via OAuth).

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Gmail search query |
| `max_results` | int | No | Max results (default: 10) |

**Example queries:**
- `from:john@example.com`
- `subject:invoice`
- `is:unread`
- `after:2026/02/01`

### get_email_logs

Retrieve recent email action logs.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | int | No | Number of logs (default: 20) |

### check_smtp_status

Check if SMTP is configured and can connect.

No parameters. Returns connection status.

---

## Workflow: Sending an Approved Email

### Step 1: Verify Approval Exists

```bash
# Check for approved email actions
ls Approved/APPROVAL_email_*
```

Read the approval file to get:
- Recipient (`target` in frontmatter)
- Subject and body context
- Original request reference

### Step 2: Draft the Email

Before sending, create a draft for review:

```markdown
## Email Draft

**To:** {recipient}
**Subject:** {subject}
**CC:** {if any}

---

{body text}

---

**Approval Reference:** Approved/APPROVAL_email_{name}.md
```

### Step 3: Send the Email

Use the MCP tool:

```
send_email(
  to: "{recipient from approval}",
  subject: "{subject}",
  body: "{body text}"
)
```

### Step 4: Log the Result

After sending, update the approval file:

```markdown
## Execution Log

- **Sent at:** {ISO timestamp}
- **To:** {recipient}
- **Subject:** {subject}
- **Status:** ✅ Sent successfully
- **Message ID:** {if available}
```

### Step 5: Complete Workflow

1. Move approval file to `/Done`:
   ```
   DONE_APPROVAL_email_{target}_{timestamp}.md
   ```

2. Update Dashboard.md:
   - Add to Recent Activity:
     ```
     | {timestamp} | Sent email to {recipient} | ✅ Complete |
     ```

3. If part of a Plan:
   - Check off the email step in the plan

---

## Error Handling

### MCP Server Unavailable

If the Email MCP is not connected:

```markdown
## Error Log

- **Attempted:** {timestamp}
- **Error:** Email MCP server not available
- **Action:** Email NOT sent

### Resolution Steps
1. Verify MCP is running: `/mcp`
2. Reconnect: `claude mcp add email-mcp -- uv run python mcp_servers/email_server.py`
3. Check SMTP config: `check_smtp_status()`
```

Keep the approval file in `/Approved` - do not move to Done until successfully sent.

### SMTP Authentication Error

If SMTP login fails:

1. Verify `.env` has correct `SMTP_USER` and `SMTP_PASSWORD`
2. Ensure you're using a Gmail App Password (not regular password)
3. Check: `check_smtp_status()`

### Send Failure

If send fails for other reasons:

```markdown
## Error Log

- **Attempted:** {timestamp}
- **Error:** {error message}
- **Action:** Email NOT sent - will retry
```

Notify human of the failure in Dashboard.md Recent Activity.

---

## Email Templates

### Reply to Inquiry

```
Subject: Re: {original subject}

Hello {name},

Thank you for reaching out.

{response content}

Best regards,
{signature}
```

### Follow-up

```
Subject: Following up: {topic}

Hello {name},

I wanted to follow up on {topic/previous conversation}.

{follow-up content}

Best regards,
{signature}
```

### Acknowledgment

```
Subject: Received: {item}

Hello {name},

This confirms receipt of {item/document/request}.

{next steps if any}

Best regards,
{signature}
```

---

## Quick Reference

### Approval Check Locations

| Check | Location |
|-------|----------|
| Pending approvals | `/Pending_Approval/APPROVAL_email_*` |
| Approved sends | `/Approved/APPROVAL_email_*` |
| Rejected sends | `/Rejected/APPROVAL_email_*` |
| Completed sends | `/Done/DONE_APPROVAL_email_*` |

### MCP Commands

| Action | Tool |
|--------|------|
| Send email | `send_email(to, subject, body)` |
| Save draft | `draft_email(to, subject, body)` |
| Search inbox | `search_emails(query)` |
| View logs | `get_email_logs(limit)` |
| Check SMTP | `check_smtp_status()` |

### Safety Checklist

Before EVERY send:

- [ ] Approval file exists in `/Approved`
- [ ] Recipient matches approval target
- [ ] Subject/content matches approval context
- [ ] Draft reviewed for accuracy
- [ ] MCP server connected (`/mcp`)
