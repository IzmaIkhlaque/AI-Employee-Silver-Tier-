#!/bin/bash
#
# Gmail MCP Server Setup Script
# Sets up OAuth credentials for the Gmail MCP server
#

set -e

echo "========================================"
echo "Gmail MCP Server Setup"
echo "========================================"
echo ""

# Get the vault directory (parent of scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT_DIR="$(dirname "$SCRIPT_DIR")"
CREDENTIALS_SOURCE="$VAULT_DIR/config/credentials.json"
GMAIL_MCP_DIR="$HOME/.gmail-mcp"
CREDENTIALS_DEST="$GMAIL_MCP_DIR/gcp-oauth.keys.json"

# Step 1: Check for credentials.json
echo "[1/4] Checking for credentials.json..."
if [ ! -f "$CREDENTIALS_SOURCE" ]; then
    echo "ERROR: credentials.json not found at:"
    echo "  $CREDENTIALS_SOURCE"
    echo ""
    echo "Please complete the Gmail API setup first:"
    echo "  1. Go to console.cloud.google.com"
    echo "  2. Create OAuth 2.0 credentials"
    echo "  3. Download and save as config/credentials.json"
    echo ""
    echo "Or run: /gmail-setup in Claude Code for full instructions"
    exit 1
fi
echo "  Found: $CREDENTIALS_SOURCE"

# Step 2: Create ~/.gmail-mcp directory
echo ""
echo "[2/4] Creating Gmail MCP directory..."
mkdir -p "$GMAIL_MCP_DIR"
echo "  Created: $GMAIL_MCP_DIR"

# Step 3: Copy credentials
echo ""
echo "[3/4] Copying credentials..."
cp "$CREDENTIALS_SOURCE" "$CREDENTIALS_DEST"
echo "  Copied to: $CREDENTIALS_DEST"

# Step 4: Run OAuth authentication
echo ""
echo "[4/4] Starting OAuth authentication..."
echo ""
echo "A browser window will open for Google sign-in."
echo "Please authorize the application to send emails."
echo ""
read -p "Press Enter to continue..."

npx @gongrzhe/server-gmail-autoauth-mcp auth

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Add the MCP server to Claude Code:"
echo "   claude mcp add gmail -- npx -y @gongrzhe/server-gmail-autoauth-mcp"
echo ""
echo "2. Verify the connection:"
echo "   Run /mcp in Claude Code - 'gmail' should be listed"
echo ""
echo "3. The Gmail MCP provides these tools:"
echo "   - send_email: Send emails"
echo "   - search_emails: Search inbox"
echo "   - get_email: Read specific email"
echo ""
