#!/usr/bin/env python3
"""Generate a cryptographically secure SECRET_KEY for production use."""
import secrets

if __name__ == "__main__":
    key = secrets.token_hex(32)
    print(f"Generated SECRET_KEY (64 hex chars):\n\n  {key}\n")
    print("Set this in your production environment:")
    print(f"  export SECRET_KEY={key}")
