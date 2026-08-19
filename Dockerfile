# LLMantis application image.
#
# Only what backend/config.py actually reads at runtime is copied in:
# attacks/, demo/, frontend/ (ATTACKS_DIR, DEMO_DIR, FRONTEND_DIR) plus
# alembic/ so migrations can be run in this same image. Everything else -
# lab/, calibration/, tools/, Brand/, the markdown - stays out. A smaller
# image is a smaller thing to get wrong, and lab/ carries an Azure key on a
# developer machine.

FROM python:3.13-slim

# Runs as a normal user. If the app is ever tricked into writing somewhere,
# it does so as an account that owns nothing.
RUN useradd --create-home --uid 10001 llmantis

WORKDIR /app

# Dependencies before code, so editing a Python file does not reinstall them.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Chromium for backend/art50engine.py, plus the system libraries it needs. This is
# the single largest thing in the image (~400 MB with the browser) and it is here
# rather than in a separate service because the Art.-50 check is an endpoint of
# this app, not a pipeline stage. --with-deps installs the apt packages Chromium
# links against; without them the browser is present and every launch fails.
# INSTALL SOMEWHERE THE APP USER CAN REACH.
#
# Playwright installs into the HOME of whoever runs the install. This ran as root
# and the app drops to USER llmantis at the bottom of the file, so 656 MB of
# Chromium landed in /root/.cache/ms-playwright while the running app looked in
# /home/llmantis/.cache/ms-playwright — and /root is 0700, so it could not have
# been read even if it had been found. The Art.-50 check failed on every click in
# production with "Executable doesn't exist", pointing at a binary that existed
# one directory away.
#
# Diagnosed and proven on the server by Bogdan (dc47816, reverted only because
# this file is Vlad's): PLAYWRIGHT_BROWSERS_PATH set BEFORE the install puts the
# browsers in a shared path, and a+rX makes them readable by the app user.
# Measured on production afterwards: Chromium 151 launched and a real check ran
# 12 probes across 20 pages in 81.7 s.
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN python -m playwright install --with-deps chromium && \
    chmod -R a+rX /ms-playwright && \
    rm -rf /root/.cache/pip

COPY backend/  ./backend/
COPY attacks/  ./attacks/
COPY demo/     ./demo/
COPY frontend/ ./frontend/
COPY alembic/  ./alembic/
COPY alembic.ini ./

USER llmantis

# No .env in the image. Configuration arrives as environment variables from
# compose; config.py's load_dotenv() is a no-op when the file is absent, so a
# secret can never be baked into a layer.
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
