---
name: task-planner
description: Create detailed execution plans for multi-step tasks. When a Needs_Action item requires more than one step, create a Plan.md with checkboxes. Use when processing complex items from /Needs_Action.
version: 1.0.0
---

# Task Planner

Create and execute detailed plans for complex multi-step tasks.

## When to Use This Skill

Use this skill when a `/Needs_Action` item requires **more than one step** to complete, such as:
- Emails requiring research + draft + send
- Requests involving multiple file operations
- Tasks requiring approval workflows
- Any item that can't be resolved in a single action

## Reasoning Loop

```
READ → ANALYZE → PLAN → EXECUTE → VERIFY → UPDATE
```

1. **READ**: Examine the Needs_Action item
2. **ANALYZE**: Break down into discrete steps
3. **PLAN**: Create Plan.md in /Plans
4. **EXECUTE**: Work through steps sequentially
5. **VERIFY**: Check completion criteria
6. **UPDATE**: Move to Done, update Dashboard

---

## Step 1: Read and Analyze the Source Item

```bash
# List items in Needs_Action
ls Needs_Action/

# Read the target item
cat Needs_Action/[filename]
```

Determine:
- What is being requested?
- How many steps are needed?
- Do any steps require approval? (Check `Company_Handbook.md` Approval Rules)

---

## Step 2: Create the Plan File

Create a new file in `/Plans` with this format:

**Filename:** `PLAN_{task_name}_{YYYYMMDD_HHMMSS}.md`

```markdown
---
task: {descriptive name}
source: Needs_Action/{original filename}
created: {ISO-8601 timestamp}
status: in_progress
estimated_steps: {count}
completed_steps: 0
---

# Plan: {Task Name}

## Objective

{1-2 sentences describing what this plan accomplishes}

## Context

This plan was triggered by: `Needs_Action/{filename}`

{Brief summary of the source item}

## Steps

- [ ] Step 1: {description}
  - Requires approval: no
- [ ] Step 2: {description}
  - Requires approval: yes
- [ ] Step 3: {description}
  - Requires approval: no

## Completion Criteria

- [ ] {Criterion 1}
- [ ] {Criterion 2}
- [ ] Source item can be archived
```

---

## Step 3: Execute Steps Sequentially

For each step in the plan:

### 3a. Check if Approval Required

If the step requires approval (per `Company_Handbook.md`):

1. Create approval request in `/Pending_Approval`:

```markdown
---
type: approval_request
plan: Plans/{plan filename}
step: {step number}
action: {what needs approval}
created: {ISO timestamp}
status: pending
---

# Approval Request: {Action Description}

## Plan Reference
- **Plan:** `Plans/{filename}`
- **Step:** {number} of {total}

## Action Details
{Detailed description of what will be done}

## Why Approval Needed
{Reference the rule from Company_Handbook.md}

## Options
- Move this file to `/Approved` to proceed
- Move this file to `/Rejected` to cancel this step
```

2. **PAUSE execution** - do not proceed until file appears in `/Approved` or `/Rejected`

### 3b. Execute Non-Approval Steps

1. Perform the action
2. Update the plan file - check off the step:
   ```markdown
   - [x] Step 1: {description}  ✅ Completed {timestamp}
   ```
3. Update frontmatter:
   ```yaml
   completed_steps: 1
   ```

### 3c. Handle Rejections

If a step is rejected:
1. Update plan status to `blocked`
2. Add note to the step explaining rejection
3. Notify in Dashboard recent activity

---

## Step 4: Complete the Plan

When all steps are done:

### 4a. Verify Completion Criteria

Check all criteria in the plan are satisfied.

### 4b. Update Plan Status

```yaml
status: completed
completed_steps: {total}
completed_at: {ISO timestamp}
```

### 4c. Move Files

1. Move the plan from `/Plans` to `/Done`:
   ```
   DONE_PLAN_{task_name}_{YYYYMMDD_HHMMSS}.md
   ```

2. Move or archive the source Needs_Action item to `/Done`

### 4d. Update Dashboard.md

- Decrement Plans count
- Increment Done count
- Add to Recent Activity:
  ```
  | {timestamp} | Completed PLAN_{name} ({X} steps) | ✅ Complete |
  ```

---

## Example

**Input:** `Needs_Action/EMAIL_client_proposal_request_20260220_100000.md`

**Analysis:**
- Client wants a proposal
- Requires: research, draft, review, send
- Sending email = requires approval

**Plan Created:** `Plans/PLAN_client_proposal_20260220_100500.md`

```markdown
---
task: Client Proposal Response
source: Needs_Action/EMAIL_client_proposal_request_20260220_100000.md
created: 2026-02-20T10:05:00
status: in_progress
estimated_steps: 4
completed_steps: 0
---

# Plan: Client Proposal Response

## Objective

Research client needs and send a tailored proposal.

## Context

This plan was triggered by: `Needs_Action/EMAIL_client_proposal_request_20260220_100000.md`

Client John Smith requested pricing for enterprise services.

## Steps

- [ ] Step 1: Research client company background
  - Requires approval: no
- [ ] Step 2: Draft proposal document
  - Requires approval: no
- [ ] Step 3: Review proposal for accuracy
  - Requires approval: no
- [ ] Step 4: Send proposal email to client
  - Requires approval: yes (email to external contact)

## Completion Criteria

- [ ] Proposal document created
- [ ] Email sent to client
- [ ] Source email archived
```

---

## Quick Reference

| Action | Location |
|--------|----------|
| Create plan | `/Plans/PLAN_{name}_{timestamp}.md` |
| Request approval | `/Pending_Approval/APPROVAL_{action}_{timestamp}.md` |
| Check approvals | Look in `/Approved` and `/Rejected` |
| Complete plan | Move to `/Done/DONE_PLAN_{name}_{timestamp}.md` |
| Update progress | Edit plan frontmatter `completed_steps` |
