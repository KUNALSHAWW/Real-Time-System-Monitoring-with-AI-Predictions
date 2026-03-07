# SECURITY_ACTIONS_PENDING.md — Operator Actions Required

> **Created:** 2026-03-07
> **Priority:** P0 — Must complete before production deployment

## 1. Rotate Compromised API Keys

### GROQ API Key
```bash
# 1. Go to https://console.groq.com/keys
# 2. Delete/revoke old key
# 3. Create new key
# 4. Update your secret manager / deployment config:
#    GROQ_API_KEY=<new-key-value>
```

### HuggingFace Token
```bash
# 1. Go to https://huggingface.co/settings/tokens
# 2. Delete old token
# 3. Create new token with appropriate scopes
# 4. Update your secret manager / deployment config:
#    HUGGINGFACE_API_TOKEN=<new-token-value>
```

## 2. Generate and Set SECRET_KEY

```bash
python scripts/generate_secret.py
# Copy the output and set it in your production environment:
# SECRET_KEY=<generated-value>
```

## 3. Purge Git History (OPTIONAL — Destructive)

The real API keys were in `.env` files which are gitignored and were NOT found
in git history (verified via `git log --all --full-history -- "*.env"`).

However, if you want to be extra cautious:

```bash
# WARNING: This rewrites git history. All collaborators must re-clone.
# Only run after coordinating with the team.

# Option A: git-filter-repo (recommended)
pip install git-filter-repo
git filter-repo --invert-paths --path .env --path backend/.env --force

# Option B: BFG Repo-Cleaner
# java -jar bfg.jar --delete-files .env
# git reflog expire --expire=now --all
# git gc --prune=now --aggressive

# After either option:
git push --force --all
git push --force --tags
```

## 4. Configure Production Environment

```bash
# Set these in your deployment platform (Render, HF Spaces, etc.)
# NEVER put real values in committed files
SECRET_KEY=<from generate_secret.py>
GROQ_API_KEY=<new-rotated-key>
HUGGINGFACE_API_TOKEN=<new-rotated-token>
CORS_ORIGINS_STR=https://your-production-domain.com
AUTO_REMEDIATION_ENABLED=false
ENVIRONMENT=production
```

## 5. Install Pre-Commit Hooks

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```
