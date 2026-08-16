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
