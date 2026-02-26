---
name: linkedin-posting
description: Generate and manage LinkedIn posts about the business to generate sales leads. Creates draft posts in /Pending_Approval for human review before posting.
version: 1.0.0
---

# LinkedIn Posting

Generate engaging LinkedIn content to build brand awareness and generate leads.

## Critical Safety Rule

```
⛔ NEVER auto-post to LinkedIn
⛔ ALL posts MUST go through /Pending_Approval first
```

Social media posts always require human approval per `Company_Handbook.md`.

---

## Workflow Overview

```
1. Read Business_Goals.md → Understand the business
2. Generate post ideas → 2-3 per week
3. Create drafts → Save to /Pending_Approval
4. Human reviews → Moves to /Approved or /Rejected
5. Post approved content → Via Playwright automation
6. Log results → Update Dashboard.md
```

---

## Step 1: Understand the Business

Before generating any content, read these files:

```bash
cat Business_Goals.md      # What the business does, target audience
cat Company_Handbook.md    # Social media rules and brand voice
```

Key information to extract:
- **What we do:** Products/services offered
- **Target audience:** Who we're trying to reach
- **Value proposition:** Why customers choose us
- **Brand voice:** Professional, casual, technical, etc.
- **Key topics:** What subjects to post about

---

## Step 2: Generate Post Ideas

Create 2-3 posts per week covering these content types:

### Content Categories

| Type | Purpose | Example |
|------|---------|---------|
| Educational | Teach something valuable | "5 things I learned about X" |
| Insight | Share industry perspective | "Here's what most people miss about Y" |
| Story | Personal/company narrative | "Last week, a client asked me..." |
| Tips | Actionable advice | "Quick tip for anyone doing Z" |
| Question | Engage audience | "What's your biggest challenge with X?" |

### Post Structure

1. **Hook Line** (First line - most important!)
   - Attention-grabbing
   - Creates curiosity
   - Visible in feed preview

2. **Value Content** (3-5 short paragraphs)
   - One idea per paragraph
   - Short sentences
   - Use line breaks for readability

3. **Call to Action**
   - What should reader do next?
   - Follow, comment, share, visit link

4. **Hashtags** (3-5 max)
   - Relevant to topic
   - Mix popular and niche

### Character Limit

- **Maximum:** 3000 characters
- **Ideal:** 1000-1500 characters
- **Hook line:** Under 150 characters

---

## Step 3: Create Draft in /Pending_Approval

### File Naming

```
APPROVAL_social_post_linkedin_{topic}_{YYYYMMDD_HHMMSS}.md
```

### File Format

```markdown
---
type: approval_request
action: social_post
platform: linkedin
topic: {brief topic description}
created: {ISO-8601 timestamp}
expires: {24 hours from creation}
status: pending
character_count: {count}
---

# LinkedIn Post Draft

## Preview

{The actual post content goes here}

---

## Post Metadata

- **Topic:** {what this post is about}
- **Goal:** {what we want to achieve}
- **Target Audience:** {who should see this}
- **Best Time to Post:** {suggested time}

## Hashtags

{#hashtag1} {#hashtag2} {#hashtag3}

---

## Approval Instructions

### ✅ To Approve

Move this file to the `/Approved` folder.

The post will be automatically published to LinkedIn.

### ❌ To Reject

Move this file to the `/Rejected` folder.

Optionally add a note explaining why.

### ✏️ To Edit

Edit the content above, then move to `/Approved`.
```

---

## Step 4: Example Post Generation

### Input: Business_Goals.md says we're an AI automation agency

### Generated Draft:

```markdown
---
type: approval_request
action: social_post
platform: linkedin
topic: ai_automation_benefits
created: 2026-02-23T10:00:00
expires: 2026-02-24T10:00:00
status: pending
character_count: 847
---

# LinkedIn Post Draft

## Preview

Most businesses are still doing manually what AI can do in seconds.

Here's what I've seen change when companies start automating:

→ Email sorting: 2 hours/day → 0 minutes
→ Data entry: 4 hours/week → automated
→ Report generation: 1 day → 5 minutes
→ Customer responses: hours → instant

The ROI isn't just time saved.

It's the mental energy your team gets back.
It's the errors that never happen.
It's the scale you couldn't reach before.

The question isn't "Can we afford to automate?"

It's "Can we afford not to?"

What's one task you wish you could automate today?

#AIAutomation #BusinessEfficiency #FutureOfWork

---

## Post Metadata

- **Topic:** Benefits of AI automation for businesses
- **Goal:** Generate awareness and engagement
- **Target Audience:** Business owners, operations managers
- **Best Time to Post:** Tuesday 9am or Wednesday 12pm

## Hashtags

#AIAutomation #BusinessEfficiency #FutureOfWork
```

---

## Step 5: After Approval

When a post is moved to `/Approved`:

### 5a. Execute the Post

Use the LinkedIn Playwright automation:

```bash
python scripts/linkedin_poster.py --post-file "Approved/APPROVAL_social_post_linkedin_{name}.md"
```

Or via MCP tool (if configured):
```
post_to_linkedin(content: "{post content}")
```

### 5b. Log the Result

Add execution log to the file:

```markdown
## Execution Log

- **Posted at:** {ISO timestamp}
- **Status:** ✅ Successfully posted
- **Post URL:** {if available}
```

### 5c. Complete Workflow

1. Move to `/Done`:
   ```
   DONE_APPROVAL_social_post_linkedin_{topic}_{timestamp}.md
   ```

2. Update Dashboard.md:
   ```
   | {timestamp} | Posted to LinkedIn: {topic} | ✅ Complete |
   ```

---

## Step 6: Handle Rejections

If moved to `/Rejected`:

1. Read any feedback notes added
2. Log the rejection
3. Move to `/Done` with rejected status
4. **Do NOT retry** with the same content

---

## Content Guidelines

### Do's ✅

- Be authentic and helpful
- Share genuine insights
- Use conversational tone
- Include white space
- Ask questions to engage
- Provide value first

### Don'ts ❌

- Don't be salesy or pushy
- Don't use clickbait
- Don't post controversial content
- Don't tag people without relevance
- Don't use more than 5 hashtags
- Don't post identical content repeatedly

---

## Posting Schedule

| Day | Time | Content Type |
|-----|------|--------------|
| Tuesday | 9:00 AM | Educational |
| Thursday | 12:00 PM | Insight/Story |
| Saturday | 10:00 AM | Tips/Question |

Best times: Tue-Thu, 9am-12pm (business hours)

---

## Quick Reference

### Approval Locations

| Status | Location |
|--------|----------|
| Draft awaiting review | `/Pending_Approval` |
| Ready to post | `/Approved` |
| Not posting | `/Rejected` |
| Posted/archived | `/Done` |

### Commands

```bash
# Generate new post draft
/linkedin-posting

# Post approved content
python scripts/linkedin_poster.py --post-file Approved/{filename}

# Check posting history
ls Done/DONE_APPROVAL_social_post_linkedin_*
```
