#!/bin/bash
set -e

echo "==> Setting up AI Fashion Assistant dev environment..."

# ── 1. Start PostgreSQL + Redis via Docker Compose ─────────────────────────
echo "==> Starting PostgreSQL and Redis..."
cd /workspaces/*/backend 2>/dev/null || cd "$(find /workspaces -name docker-compose.yml -exec dirname {} \; | head -1)"
docker compose up -d postgres redis
echo "    Waiting for PostgreSQL to be ready..."
sleep 8

# ── 2. Install Python backend dependencies ─────────────────────────────────
echo "==> Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "    Python deps installed."

# ── 3. Build .env from Codespaces secrets ──────────────────────────────────
cp .env.example .env

# Inject secrets from Codespaces environment variables (set in repo settings)
[ -n "$OPENAI_API_KEY" ]          && sed -i "s|OPENAI_API_KEY=.*|OPENAI_API_KEY=$OPENAI_API_KEY|"                   .env
[ -n "$OPENAI_MODEL" ]            && sed -i "s|OPENAI_MODEL=.*|OPENAI_MODEL=${OPENAI_MODEL:-gpt-4o-mini}|"           .env
[ -n "$REPLICATE_API_TOKEN" ]     && sed -i "s|REPLICATE_API_TOKEN=.*|REPLICATE_API_TOKEN=$REPLICATE_API_TOKEN|"     .env
[ -n "$AWS_ACCESS_KEY_ID" ]       && sed -i "s|AWS_ACCESS_KEY_ID=.*|AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID|"           .env
[ -n "$AWS_SECRET_ACCESS_KEY" ]   && sed -i "s|AWS_SECRET_ACCESS_KEY=.*|AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY|" .env
[ -n "$AWS_BUCKET_NAME" ]         && sed -i "s|AWS_BUCKET_NAME=.*|AWS_BUCKET_NAME=$AWS_BUCKET_NAME|"                 .env
[ -n "$OPENWEATHER_API_KEY" ]     && sed -i "s|OPENWEATHER_API_KEY=.*|OPENWEATHER_API_KEY=$OPENWEATHER_API_KEY|"     .env

# Write firebase-credentials.json from secret
if [ -n "$FIREBASE_CREDENTIALS" ]; then
  echo "$FIREBASE_CREDENTIALS" > firebase-credentials.json
  echo "    Firebase credentials written."
fi

echo "    .env configured from Codespaces secrets."

# ── 4. Run Alembic migrations ───────────────────────────────────────────────
echo "==> Running database migrations..."
alembic upgrade head && echo "    Migrations done." || echo "    Migrations skipped (check .env DATABASE_URL)"

# ── 5. Install mobile dependencies ─────────────────────────────────────────
echo "==> Installing mobile (Expo) dependencies..."
MOBILE_DIR="$(find /workspaces -name "package.json" -path "*/mobile/*" -exec dirname {} \; | head -1)"
if [ -n "$MOBILE_DIR" ]; then
  cd "$MOBILE_DIR"
  npm install -q
  echo "    Mobile deps installed."
fi

echo ""
echo "✓ Setup complete!"
echo ""
echo "  Start backend:  cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
echo "  Run tests:      cd backend && pytest --cov=app tests/ -v"
echo "  Start mobile:   cd mobile && npx expo start --tunnel"
echo "  API docs:       http://localhost:8000/docs"
echo ""
