# PromptGuard — Setup

Run these once after cloning. Takes 2 minutes.

## 1. Clone and enter

```bash
git clone git@github.com:VladvonTranssylvanien/promptguard.git
cd promptguard
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

Only switch to `PROVIDER=anthropic` and add a real key when we test for real.

**Never commit `.env`.** It's in `.gitignore`. It will hold an API key.

## 5. Check it works

```bash
python -m backend.selfcheck
```

## Adding a new dependency

Don't just `pip install`. Add the pinned version to `requirements.txt` and commit
it, so everyone gets the same version.

```bash
pip install somepackage==1.2.3
echo "somepackage==1.2.3" >> requirements.txt
```

## Daily routine

```bash
cd promptguard
source venv/bin/activate
git pull
pip install -r requirements.txt   # in case someone added a dependency
```
