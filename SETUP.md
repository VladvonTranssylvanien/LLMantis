# LLMantis — Setup

Run these once after cloning. Takes about 5 minutes (was 2, before the
database was added).

## 1. Clone and enter

```bash
git clone git@github.com:VladvonTranssylvanien/LLMantis.git
cd LLMantis
```

## 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows: `venv\Scripts\activate`

Your prompt should now start with `(venv)`. If it doesn't, stop and fix this
before continuing. Everything below assumes it's active.

**You must run `source venv/bin/activate` every time you open a new terminal.**

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Create your local config

```bash
cp .env.example .env
```

Leave `PROVIDER=mock` for now. Mock mode returns fake bot responses, so you can
build and test everything without an API key and without spending money.

Only switch to `PROVIDER=mistral` and add a real `MISTRAL_API_KEY` when you
need to test against a real model. **Mistral is the only provider** — see
`PLAYBOOK.md` §1 for why (no US vendor in the stack).

**Never commit `.env`.** It's in `.gitignore`. It will hold an API key.

## 5. Start the database

Scans, organizations, API keys and branding all live in Postgres now, not
in memory — this step is required even in mock mode:

```bash
docker compose up -d      # starts Postgres, see docker-compose.yml
alembic upgrade head       # applies every migration in alembic/versions/
```

## 6. Check it works

```bash
uvicorn backend.main:app --reload --port 8000
```

In another terminal:

```bash
curl -s localhost:8000/api/health
```

You should get back `{"status":"ok", ...}`. Open http://localhost:8000, pick
a demo bot, press **Run scan**.

## Adding a new dependency

Don't just `pip install`. Add the pinned version to `requirements.txt` and commit
it, so everyone gets the same version.

```bash
pip install somepackage==1.2.3
echo "somepackage==1.2.3" >> requirements.txt
```

## Changed `backend/models.py`?

Generate a migration before committing — never hand-edit the schema or ship
a model change without one:

```bash
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

## Daily routine

```bash
cd LLMantis
source venv/bin/activate
git pull
pip install -r requirements.txt   # in case someone added a dependency
alembic upgrade head              # in case someone added a migration
docker compose up -d              # in case Postgres isn't already running
```

## Auth, if you're building frontend for it

`POST /api/auth/register` / `/login` return `{"access_token": "...", "token_type": "bearer"}`.
Send it back as `Authorization: Bearer <token>` on any 🔒 endpoint (see the
table in `README.md`). Set a real `JWT_SECRET` in `.env` — leaving it empty
logs everyone out on every server restart (that's the intended dev default,
not a bug).
