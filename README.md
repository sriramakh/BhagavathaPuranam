# Bhagavatha Puranam

An episode-based animated storybook platform for retelling stories from the Srimad Bhagavatham with recurring character continuity, shloka-aware story planning, and a feedback-driven visual memory system.

## Product Principles

- Character identity comes first. Every recurring character has a canonical identity, aliases, approved forms, visual profiles, and reusable reference assets.
- Generated stories store character IDs, not just names, so Krishna, Yashoda, Narada, Prahlada, and other recurring characters remain visually and narratively consistent.
- Mythological conflict is allowed when handled in devotional, epic, non-graphic framing.
- Scene generation is reviewable. Users approve or edit the scene plan before images are generated.
- The corpus layer stores source metadata and short summaries so episodes can be traced back to shlokas, chapters, or user-provided plots.

## Repository Layout

```text
backend/     FastAPI API, SQLite memory store, Grok Imagine integration
frontend/    Next.js product UI
docs/        Architecture and source notes
```

## Development

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## Image Generation

Grok Imagine is the default image provider. Set:

```env
GROK_API_KEY=...
IMAGE_PROVIDER=grok-imagine
```

If `GROK_API_KEY` is missing, image generation endpoints return a clear configuration error, while character memory and episode planning still work.
