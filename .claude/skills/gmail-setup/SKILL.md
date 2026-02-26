---
name: gmail-setup
description: Guide for setting up Gmail API OAuth credentials. Use when the user needs to configure Gmail access for the watcher or MCP server.
version: 1.0.0
---

# Gmail API Setup Guide

Set up Gmail API access for the AI Employee to read, send, and manage emails.

## Prerequisites

- Google account
- Python 3.8+
- uv package manager

## Step-by-Step Setup

### Step 1: Access Google Cloud Console

Go to [console.cloud.google.com](https://console.cloud.google.com)

Sign in with your Google account.

### Step 2: Create or Select a Project

- Click the project dropdown at the top
- Select an existing project OR click **New Project**
- If creating new: enter a project name (e.g., "AI-Employee-Gmail") and click **Create**

### Step 3: Enable the Gmail API

1. Navigate to **APIs & Services** → **Library**
2. Search for "Gmail API"
3. Click on **Gmail API**
4. Click **Enable**

### Step 4: Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **External** (or Internal if using Workspace)
3. Fill in required fields:
   - App name: "AI Employee"
   - User support email: your email
   - Developer contact: your email
4. Click **Save and Continue**
5. Add scopes (optional for now, can be configured later)
6. Add your email as a test user
7. Click **Save and Continue**

### Step 5: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Application type: **Desktop App**
4. Name: "AI Employee Desktop"
5. Click **Create**

### Step 6: Download Credentials

1. Click the download icon next to your new OAuth client
2. Save the file as `credentials.json`
3. Move it to your project's config folder:

```bash
mv ~/Downloads/client_secret_*.json config/credentials.json
```

### Step 7: First Run Authorization

On first run, the application will:
1. Open your default browser
2. Ask you to sign in to Google
3. Request permission to access Gmail
4. After authorization, `config/token.json` is created automatically

The token will be refreshed automatically on subsequent runs.

## Required Python Packages

Install the following packages:

```bash
uv add google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

| Package | Purpose |
|---------|---------|
| `google-api-python-client` | Core Google API client library |
| `google-auth-httplib2` | HTTP transport for authentication |
| `google-auth-oauthlib` | OAuth 2.0 flow handling |

## File Structure

After setup, your config folder should contain:

```
config/
├── credentials.json    # OAuth client credentials (from Google Console)
└── token.json          # Auto-generated after first authorization
```

## Common Scopes

Depending on your needs, you may use these Gmail scopes:

| Scope | Permission |
|-------|------------|
| `gmail.readonly` | Read emails only |
| `gmail.send` | Send emails |
| `gmail.modify` | Read, send, delete, manage labels |
| `gmail.compose` | Create and send new emails |

## Troubleshooting

### "Access Denied" Error
- Ensure your email is added as a test user in OAuth consent screen
- Check that Gmail API is enabled

### "Invalid Client" Error
- Re-download credentials.json from Google Console
- Ensure the file is valid JSON

### Token Expired
- Delete `config/token.json` and re-run to re-authorize
