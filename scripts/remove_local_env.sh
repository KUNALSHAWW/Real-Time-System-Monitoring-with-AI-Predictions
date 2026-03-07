#!/bin/bash
# scripts/remove_local_env.sh
# Safely remove local .env files and remind developer to rotate keys
set -e

echo "================================================================"
echo "  LOCAL SECRETS CLEANUP"
echo "================================================================"
echo ""
echo "This script will remove local .env files containing secrets."
echo "BEFORE running this, ensure you have:"
echo "  1. Rotated your GROQ API key at https://console.groq.com/keys"
echo "  2. Rotated your HuggingFace token at https://huggingface.co/settings/tokens"
echo "  3. Generated a new SECRET_KEY: python scripts/generate_secret.py"
echo "  4. Stored new values in your deployment secret manager"
echo ""
echo "Files to remove:"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

for envfile in "$REPO_ROOT/.env" "$REPO_ROOT/backend/.env" "$REPO_ROOT/agent/.env"; do
    if [ -f "$envfile" ]; then
        echo "  [FOUND]   $envfile"
    else
        echo "  [MISSING] $envfile"
    fi
done

echo ""
read -p "Delete the above .env files? (y/N): " confirm
if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
    for envfile in "$REPO_ROOT/.env" "$REPO_ROOT/backend/.env" "$REPO_ROOT/agent/.env"; do
        if [ -f "$envfile" ]; then
            rm "$envfile"
            echo "  Deleted: $envfile"
        fi
    done
    echo ""
    echo "Done. Copy .env.example files and fill in new (rotated) values."
else
    echo "Aborted. No files deleted."
fi
