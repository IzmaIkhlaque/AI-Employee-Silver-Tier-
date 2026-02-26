# Company Handbook

## Purpose

This file defines how the AI Employee behaves when processing files and tasks. It serves as the single source of truth for all operational rules and ensures consistent, predictable behavior across all automated actions.

---

## File Processing Rules

- When a new file appears in `/Needs_Action`, read it and determine what action is needed
- Create a summary and move the processed result to `/Done`
- Update `Dashboard.md` after every action

---

## Priority Keywords

| Priority | Keywords |
|----------|----------|
| 🔴 Critical | urgent, emergency, asap |
| 🟠 High | important, deadline, invoice |
| 🟡 Medium | question, update, follow-up |
| 🟢 Low | fyi, no rush |

---

## Naming Convention

- **Needs_Action:** `TYPE_description_YYYYMMDD_HHMMSS.md`
- **Done:** `DONE_TYPE_description_YYYYMMDD_HHMMSS.md`
- **Plans:** `PLAN_description_YYYYMMDD_HHMMSS.md`
- **Pending_Approval:** `APPROVAL_description_YYYYMMDD_HHMMSS.md`

---

## Approval Rules

The following actions require human approval before execution. Claude will create a request in `/Pending_Approval` and wait for it to be moved to `/Approved` or `/Rejected`.

| Action | Approval Required |
|--------|-------------------|
| Email to unknown contacts | ✅ Yes |
| Any bulk sends | ✅ Yes |
| Social media posts | ✅ Always |
| File deletion | ✅ Yes |
| Payments (any amount) | ✅ Yes |

### Approval Workflow

1. Claude creates a plan/request in `/Pending_Approval`
2. Human reviews the request
3. Human moves file to `/Approved` or `/Rejected`
4. Claude checks and proceeds accordingly

---

## Social Media Guidelines

### LinkedIn Posting

**Content Rules:**
- All posts must align with `Business_Goals.md`
- Maximum 3000 characters per post
- 3-5 hashtags maximum
- No controversial or political content
- No competitor mentions
- Professional, helpful tone

**Post Structure:**
1. Hook line (attention-grabbing first sentence)
2. Value content (3-5 short paragraphs)
3. Call to action
4. Relevant hashtags

**Posting Schedule:**
- Target: 2-3 posts per week
- Best times: Tue-Thu, 9am-12pm
- Never post on major holidays

**Brand Voice:**
- Professional but approachable
- Educational and insightful
- Authentic, not salesy
- Helpful first, promotional second

**IMPORTANT:** All social media posts require human approval. Never auto-post.
