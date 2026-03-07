# SECRETS_FOUND.md — Security Incident Report

> **Date discovered:** 2026-03-07
> **Status:** REDACTED — originals removed from working tree
> **Action required:** Rotate all keys listed below immediately

## Secrets Found

| File | Line | Variable | Service | Action Required |
|------|------|----------|---------|-----------------|
| `.env` | 11 | `GROQ_API_KEY` | GROQ Console | Rotate at https://console.groq.com/keys |
| `.env` | 14 | `HUGGINGFACE_API_TOKEN` | HuggingFace | Rotate at https://huggingface.co/settings/tokens |
| `.env` | 94 | `SECRET_KEY` | JWT signing | Generate new: `python scripts/generate_secret.py` |
| `backend/.env` | 11 | `GROQ_API_KEY` | GROQ Console | Rotate at https://console.groq.com/keys |
| `backend/.env` | 14 | `HUGGINGFACE_API_TOKEN` | HuggingFace | Rotate at https://huggingface.co/settings/tokens |
| `backend/.env` | 94 | `SECRET_KEY` | JWT signing | Generate new: `python scripts/generate_secret.py` |

## Rotation Instructions

### 1. GROQ API Key
1. Go to https://console.groq.com/keys
2. Revoke the compromised key
3. Generate a new key
4. Update your deployment secret store with the new key
5. Set `GROQ_API_KEY=<new-key>` in your `.env` files (never commit)

### 2. HuggingFace API Token
1. Go to https://huggingface.co/settings/tokens
2. Revoke the compromised token
3. Generate a new token with appropriate permissions
4. Update your deployment secret store
5. Set `HUGGINGFACE_API_TOKEN=<new-token>` in your `.env` files (never commit)

### 3. JWT SECRET_KEY
1. Generate a new secret: `python scripts/generate_secret.py`
2. Store the output in your deployment secret manager
3. Set `SECRET_KEY=<generated-value>` in production environment
4. Note: changing SECRET_KEY will invalidate all existing JWT tokens

## Git History Purge (Operator-Run ONLY)

**WARNING:** These commands rewrite git history. Coordinate with all contributors before running.

```bash
# Install git-filter-repo (if not already)
# pip install git-filter-repo

# Purge .env files from entire git history
# git filter-repo --invert-paths --path .env --path backend/.env --force

# After purging, force-push to all remotes
# git push --force --all
# git push --force --tags

# All contributors must re-clone after history rewrite
```

## Prevention

- `.env` files are in `.gitignore` — never force-add them
- Pre-commit hooks (gitleaks) are configured to block secret commits
- Use `scripts/remove_local_env.sh` to safely clean local secrets
