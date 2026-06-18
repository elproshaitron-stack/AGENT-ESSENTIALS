# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅        |

Pre-1.0 software: only the latest minor release receives security fixes.

## Reporting a vulnerability

Please **do not** open a public issue for security problems.

- Preferred: open a private report via GitHub Security Advisories
  (repository → **Security** → **Report a vulnerability**).
- Or email the maintainer: **elproshaitron@gmail.com**.

Include a description, reproduction steps, affected version and impact. We aim to
acknowledge within 72 hours and to ship a fix or mitigation for confirmed issues
as quickly as is practical, crediting reporters who wish to be credited.

## Scope notes

The core toolkit is deterministic and has **no required runtime dependencies**
and makes **no network calls**. Network/LLM behavior only exists in optional
extras (`llm`) or in user-supplied plugins/scorers, which are outside this
project's trust boundary.
