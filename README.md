# Bee2Gether

Bee2Gether is a location-based social event app. It combines map discovery, group planning, realtime chat, event comments, notifications, and seeded demo activity for social-product demos.

## Stack

| Layer | Technology |
| --- | --- |
| Frontend | Vue 3, Vite, SCSS |
| Maps | MapLibre GL JS, OpenFreeMap |
| Backend | FastAPI |
| Database | MongoDB Atlas |
| Image storage | Supabase Storage |
| Deployment | Render |
| Realtime | FastAPI WebSockets |

## Features

- Guest access with browser-scoped guest identity
- Registered user accounts
- Viewport-based event discovery on the map
- Event creation with date, start time, end time, tags, image, and place search
- Group creation and group-linked events
- Realtime group chat
- Realtime event comments and attendance updates
- Notifications
- Personal planning views:
  - Attending
  - Saved
  - Agenda
  - Month calendar
- UK-wide seeded demo dataset for presentations

## Project Layout

```text
cloudAppBeeCW-1/
├── backend/
│   ├── main.py
│   ├── repository.py
│   ├── config.py
│   ├── seed_demo_data.py
│   ├── requirements.txt
│   └── tests/
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.mjs
├── render.yaml
└── README.md
```

## Local Development

### Backend

```bash
cd cloudAppBeeCW-1
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Environment variables:

- `MONGODB_URI`
- `MONGODB_DB_NAME`
- `FRONTEND_ORIGIN`
- `SUPABASE_URL`
- `SUPABASE_SECRET_KEY`
- `SUPABASE_BUCKET`

If `MONGODB_URI` is missing, the backend falls back to the in-memory repository for local testing only.

### Frontend

```bash
cd cloudAppBeeCW-1/frontend
npm install
npm run dev
```

The frontend runs on `http://127.0.0.1:5173` and proxies `/api/*` and `/api/realtime` to the backend in local development.

Optional frontend env vars:

- `VITE_API_BASE_URL`
- `VITE_API_CODE`

## Demo Data

Seed the demo dataset from the repo root:

```bash
source .venv/bin/activate
python -m backend.seed_demo_data --reset-and-seed
```

This creates:

- 50 users
- 12 groups
- 75 UK events
- comments
- group chat history
- saved events
- notifications

All seeded demo accounts use:

```text
demo1234567
```

Example seeded user:

```text
harry.clarke
```

If you only want to seed an empty database:

```bash
python -m backend.seed_demo_data --seed-if-empty
```

## Render Deployment

This repo is configured for Render as two services:

- `bee2gether-api` as a Python web service
- `bee2gether-web` as a static site

The deployment config is in [render.yaml](render.yaml).

### Backend service

- Build command:

```text
pip install -r backend/requirements.txt
```

- Start command:

```text
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

- Health check:

```text
/api/health
```

Required backend env vars:

```text
MONGODB_URI
MONGODB_DB_NAME=bee2gether
FRONTEND_ORIGIN=https://<your-frontend>.onrender.com
SUPABASE_URL
SUPABASE_SECRET_KEY
SUPABASE_BUCKET=event-images
```

### Frontend service

- Root directory: `frontend`
- Build command:

```text
npm install && npm run build
```

- Publish directory:

```text
dist
```

Required frontend env vars:

```text
VITE_API_BASE_URL=https://<your-backend>.onrender.com/api
VITE_API_CODE=render-demo
```

Render should rewrite `/*` to `/index.html` for Vue Router routes.

## MongoDB Atlas

When deploying to Render:

1. Open the backend service in Render
2. Copy the outbound IP/CIDR range from `Connect -> Outbound`
3. Add that range to MongoDB Atlas `Network Access`
4. Remove any temporary `0.0.0.0/0` rule once Render connectivity works

## Health Check

The backend exposes:

```text
GET /api/health
```

Expected healthy response:

```json
{"result":true,"status":"ok","database":"mongo"}
```

## Notes

- Map event loading is viewport-based, not “load all events on login”.
- Realtime is used for chat, comments, attendance updates, and notifications.
- Public seeded content is visible to guests and new users; seeded personal history belongs to the seeded demo accounts.
