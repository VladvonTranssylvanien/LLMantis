# 🔐 Secrets Management

**CRITICAL: Never commit API keys, passwords, or credentials to git.**

This document explains how LLMantis handles secrets securely.

---

## ✅ What's Protected

| Secret | Location | Status | Who Sets It |
|--------|----------|--------|------------|
| `MISTRAL_API_KEY` | `.env` (not committed) | ✅ User provides | Developer / DevOps |
| `DATABASE_URL` | `.env` (not committed) | ✅ User provides | DevOps |
| `JWT_SECRET` | `.env` (not committed) | ✅ Signs login tokens — see below | Developer / DevOps |
| Postgres password | `.env` + `docker-compose.yml` | ✅ Dev-only, changes in prod | DevOps |
| User passwords | `users.password_hash` in Postgres | ✅ bcrypt, plaintext never stored | Each user |
| LLMantis API keys (`llm_live_...`) | Issued via `POST /api/keys`, hash stored in Postgres | ✅ shown to the caller once, never recoverable | Whoever calls the endpoint, if a member of the org |

⚠️ The code reads **three** model credentials today (`backend/config.py`):
`MISTRAL_API_KEY`, `AZURE_KEY` (the judge, when `PROVIDER=azure`, which is
the default), and `TARGET_KEY` (the deployment under attack in `mode="model"`).
Whichever provider is in use, the rule that matters is the one in this file:
the key lives in `.env`, never in the repository, and never in a chat message.

### `JWT_SECRET` — signs every login token

Generate one with `python -c "import secrets; print(secrets.token_hex(32))"`
and set it in `.env`. Leave it empty in dev and the app generates a random
one at startup instead of refusing to run — but that also invalidates every
existing login token on the next restart, on purpose, so a real secret gets
set before anyone mistakes this for production-ready. Rotating it logs
everyone out immediately (same idea as revoking an API key).

---

## 📋 Setup Instructions

### 1. Get Your API Keys

**Mistral (the LLM provider the code reads today):**
```
1. Go to https://console.mistral.ai
2. Login
3. Click "API Keys" → "Generate New Key"
4. Copy the key (starts with sk-...)
```

### 2. Set Up .env File

```bash
# Copy template
cp .env.example .env

# Edit .env and fill in your API keys
nano .env
```

Your `.env` should look like:
```
PROVIDER=mistral
MISTRAL_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx
DATABASE_URL=postgresql+psycopg://llmantis:llmantis_dev_password@localhost:5432/llmantis
...
```

### 3. Verify .env is Gitignored

```bash
# Check: .env should be in .gitignore
grep "^\.env$" .gitignore

# Verify: .env should NOT be staged
git status | grep ".env"  # should show nothing
```

---

## ⚠️ DO NOT

❌ **NEVER hardcode secrets in code:**
```python
# BAD - NEVER DO THIS
API_KEY = "sk-xxxxx"
password = "mypassword123"
```

❌ **NEVER commit .env file:**
```bash
git add .env  # DO NOT DO THIS
```

❌ **NEVER share API keys in chat, email, or Slack:**
- Keys are compromised if exposed
- Rotate immediately if leaked

❌ **NEVER print secrets in logs:**
```python
# BAD
print(f"Using key: {api_key}")

# GOOD
print(f"Using key: sk-***REDACTED***")
```

---

## ✅ DO

✅ **Always load secrets from environment:**
```python
# GOOD
api_key = os.getenv("MISTRAL_API_KEY")
if not api_key:
    raise LLMError("MISTRAL_API_KEY not set in .env")
```

✅ **Always check .gitignore before committing:**
```bash
git status  # Make sure .env is NOT listed
```

✅ **Always use .env.example (without secrets):**
```bash
# .env.example shows structure, has no real secrets
cat .env.example
```

✅ **Always rotate keys after security incidents:**
```
1. Delete old key in console
2. Generate new key
3. Update .env with new key
4. Restart application
```

---

## 🚀 Production Deployment

### GitHub Secrets (for CI/CD)

```bash
# Store secrets in GitHub, not in code
Settings → Secrets and Variables → Actions → New Repository Secret

MISTRAL_API_KEY=sk-xxxxx
DATABASE_URL=postgresql+...
```

### Azure / Hetzner Environment

```bash
# Set environment variables on server
export MISTRAL_API_KEY=sk-xxxxx
export DATABASE_URL=postgresql+...
```

### Docker Secrets (for containerized deployment)

```dockerfile
# DO NOT include secrets in Dockerfile
# Use --env-file or -e flags instead
docker run \
  --env-file .env.prod \
  -e MISTRAL_API_KEY=${MISTRAL_API_KEY} \
  llmantis:latest
```

---

## 🔍 Audit Secrets

```bash
# Check: no secrets in git history
git log -p --all | grep -i "sk-\|api.key"

# Check: no secrets in current code
grep -r "sk-\|api.key" backend/ --include="*.py" | grep -v "getenv\|config"

# Check: .env is gitignored
git check-ignore .env
```

---

## 📞 If You Accidentally Leaked a Secret

1. **Immediately rotate the key** (delete old, generate new in the Mistral console)
2. **Update .env** with the new key
3. **Restart the application**
4. **Notify the team** (in case it was pushed to GitHub)
5. **Run git history audit** to verify no old keys remain

---

## LLMantis API keys (`llm_live_...`) — different from the above

These are keys **we issue** so a customer can call our API programmatically
(a CI/CD pipeline, an integration) — the opposite direction from the secrets
above, which are keys **we use** to call someone else's API.

- Generated by `POST /api/keys`, shown in the response **exactly once**.
  We store only `sha256(key)` — if it's lost, revoke it and issue a new one,
  there is no recovery.
- Requires being logged in and a member of that `org_id` (see technical debt
  #9 in `PROJECT-STATE.md`, resolved 16.08) — minting a key for an
  organization you don't belong to is a 403.

## Links

- **Mistral Console:** https://console.mistral.ai
- **.env template:** `.env.example` (safe to commit)
- **Gitignore rules:** `.gitignore` (line 2: `.env`)
