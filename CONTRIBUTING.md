# Contributing

## Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and fill in your values
3. Install Python dependencies: `pip install -r backend/requirements.txt`
4. Install pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

## Pre-Commit Hooks

This repo uses [pre-commit](https://pre-commit.com/) with:

- **gitleaks**: Detects secrets (API keys, tokens) before they are committed
- **detect-aws-credentials**: Blocks AWS credential commits
- **detect-private-key**: Blocks private key commits

Run manually on all files:
```bash
pre-commit run --all-files
```

## Branch Naming

- `feat/<scope>/description` — new features
- `fix/<scope>/description` — bug fixes
- `chore/<scope>/description` — maintenance
- `ci/<scope>/description` — CI/CD changes

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(self-heal): add memory leak detector
fix(backend): enforce SECRET_KEY in production
chore(security): remove hardcoded secrets
```

## Running Tests

```bash
# All tests
pytest -q

# Specific test file
pytest tests/test_self_heal.py -v
```

## Security

- **NEVER** commit `.env` files or real API keys
- Use `REDACTED_<SERVICE>_KEY` placeholders in example files
- All destructive remediation code defaults to `dry_run=True`
- `AUTO_REMEDIATION_ENABLED` must be explicitly set to `true` in production
