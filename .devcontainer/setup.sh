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

# ── 3. Copy .env.example → .env if .env doesn't exist ─────────────────────
if [ ! -f .env ]; then
  cp .env.example .env
  echo "    Created .env from .env.example — fill in your API keys!"
fi

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
