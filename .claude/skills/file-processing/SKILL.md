---
name: file-processing
description: Process new items that appear in /Needs_Action folder. Read the file, classify priority using Company_Handbook.md keywords, create a summary, and move to /Done.
version: 1.0.0
---

# File Processing

Process files from the Needs_Action folder and move completed items to Done.

## Workflow

### Step 1: Read the file from /Needs_Action

```bash
# List files in Needs_Action
ls Needs_Action/

# Read the target file
cat Needs_Action/[filename]
```

### Step 2: Extract key information

Identify and extract:
- **Type**: What kind of item is this? (email, request, task, question, etc.)
- **From**: Who is this from? (person, system, unknown)
- **What's needed**: What action or response is required?

### Step 3: Classify priority using Company_Handbook.md

Read `Company_Handbook.md` and match keywords to determine priority:

| Priority | Keywords |
|----------|----------|
| 🔴 Critical | urgent, emergency, asap |
| 🟠 High | important, deadline, invoice |
| 🟡 Medium | question, update, follow-up |
| 🟢 Low | fyi, no rush |

Scan the file content for these keywords (case-insensitive).

### Step 4: Create processed version in /Done

Create a new file in `/Done` with the naming convention:
`DONE_TYPE_description_YYYYMMDD_HHMMSS.md`

Include in the processed file:
```markdown
# Processed: [Original Title]

**Original File:** [filename]
**Processed:** [timestamp]
**Priority:** [emoji + level]

## Summary
[2-3 sentence summary of what this item was about]

## Key Information
- **Type:** [type]
- **From:** [source]
- **Action Needed:** [what was required]

## Status
[What was done or determined]
```

### Step 5: Update Dashboard.md

After processing, update the Dashboard:
1. Increment Done count
2. Decrement Needs_Action count
3. Add entry to Recent Activity table
4. Update Last Updated timestamp

## Example

**Input file:** `Needs_Action/EMAIL_client_question_20260218_100000.md`

**Output file:** `Done/DONE_EMAIL_client_question_20260218_100000.md`
