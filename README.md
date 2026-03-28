# AI-Powered Smart Wardrobe and Fashion Assistant

**BSc Final Year Project** — Nwobodo Samuel Tochukwu
Veritas University, Abuja · Department of Computer and Information Technology
Supervisors: Dr. Amaku Amaku & Mr. Eric Taniform

---

## Project Overview

A mobile AI fashion assistant that combines:
- **Digital wardrobe management** with automatic AI tagging (CLIP)
- **Personalised outfit recommendations** (GPT-4o, Nigerian-context-aware)
- **2D outfit visualisation** (Stable Diffusion + ControlNet via Replicate.com)
- **Sustainable fashion analytics** (wear tracking, utilisation rate, cost-per-wear)

---

## Repository Structure

```
├── backend/          FastAPI API + AI services + PostgreSQL
├── mobile/           React Native (Expo) mobile app
└── docs/             Architecture diagrams, evaluation templates
```

---

## Quick Start (Development)

### 1. Backend

```bash
cd backend

# Copy and fill in your API keys
cp .env.example .env

# Start PostgreSQL + Redis
docker compose up postgres redis -d

# Install Python dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start API server
uvicorn app.main:app --reload --port 8000
```

API docs available at: `http://localhost:8000/docs`

### 2. Mobile

```bash
cd mobile
npm install
npx expo start
```

Scan the QR code with the Expo Go app on your Android or iOS device.

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in:

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key (get from platform.openai.com) |
| `OPENAI_MODEL` | `gpt-4o-mini` for dev, `gpt-4o` for evaluation |
| `REPLICATE_API_TOKEN` | Replicate.com token for SD visualisation |
| `FIREBASE_CREDENTIALS_PATH` | Path to Firebase service account JSON |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | For S3 image storage |
| `OPENWEATHER_API_KEY` | OpenWeatherMap key for Nigerian city weather |

---

## Running Tests

```bash
cd backend
pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## AI Models Used

| Model | Purpose | Hosting |
|---|---|---|
| CLIP (`clip-vit-base-patch32`) | Clothing classification + semantic search | Self-hosted (CPU) |
| GPT-4o / GPT-4o-mini | Outfit recommendations | OpenAI API |
| Stable Diffusion 1.5 + ControlNet | Outfit visualisation | Replicate.com (dev) |

---

## Ethical Compliance

- **Data Privacy:** NDPR and GDPR compliant — consent screen, data deletion endpoint
- **Skin Tone Representation:** Explicit skin tone descriptor in all SD prompts; bias audit in evaluation
- **Nigerian Cultural Context:** Traditional garments (Ankara, Agbada, Kaftan, etc.) supported from day one
- **Transparency:** All AI-generated outputs labelled as machine-generated

---

## Research Objectives

1. Design a comprehensive mobile digital wardrobe management system
2. Use CLIP + GPT-4o for personalised outfit recommendations
3. Use Stable Diffusion + ControlNet for outfit visualisation + usage tracking
4. Evaluate on accuracy, visual quality, user satisfaction, and ethical compliance
# AI-Fashion-Assistant
