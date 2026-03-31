# Bee2Gether

Bee2Gether is a location-based social event app. It replaces the original paid Google Maps and Azure dependencies with a free-tier-friendly stack that can be run locally or deployed as a demo.

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vue 3, Vite, SCSS, MapLibre GL JS, OpenFreeMap |
| Backend | FastAPI |
| Database | MongoDB Atlas or in-memory fallback for local testing |
| Image Storage | Supabase Storage or inline data URL fallback |
| Deployment | Render static site + Render Python web service |

## Project Layout

```
cloudAppBeeCW-1/
├── api/                    # Legacy Vercel Python entrypoint
├── backend/
│   ├── main.py             # FastAPI compatibility app
│   ├── repository.py       # MongoDB + in-memory repositories
│   ├── config.py           # Environment-driven configuration
│   ├── .env.example        # New backend environment template
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── store/
│   │   └── api.js
│   ├── package.json
│   ├── vite.config.mjs
│   └── server.js
├── render.yaml
└── vercel.json
```

## What Changed

- Google Maps was replaced with MapLibre GL JS and OpenFreeMap.
- Google Places autocomplete was replaced with free-text geocoding via Nominatim plus a “use current location” flow.
- Azure Functions were replaced with a single FastAPI app that preserves the old endpoint names.
- Azure Cosmos DB was replaced with a repository layer that supports MongoDB Atlas and a local in-memory fallback.
- Azure Blob Storage was replaced with optional Supabase uploads and an inline-image fallback for local demos.
- Old embedded Azure connection strings and function keys were scrubbed from active source files.

## Local Development

### 1. Backend

```bash
cd cloudAppBeeCW-1
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

Defaults:

- If `MONGODB_URI` is not set, the backend runs with an in-memory repository.
- If `SUPABASE_URL` and `SUPABASE_SECRET_KEY` are not set, uploaded images are stored inline on the event document as data URLs.

Environment variables live in [`backend/.env.example`](backend/.env.example).

### Demo Data Seeding

To populate the database with a repeatable UK-wide demo social graph:

```bash
cd cloudAppBeeCW-1
source .venv/bin/activate
python -m backend.seed_demo_data
```

This seeds:

- 50 users
- 12 groups
- 75 upcoming UK events
- comments, group chat, saved events, and notifications

All seeded demo users share the same login password:

```text
demo1234567
```

If you only want to populate an empty database:

```bash
python -m backend.seed_demo_data --seed-if-empty
```

### 2. Frontend

```bash
cd cloudAppBeeCW-1/frontend
npm install
npm run dev
```

The Vite dev server proxies `/api/*` requests to `http://localhost:8000` by default.

Optional frontend env vars:

- `VITE_API_BASE_URL` to call a remote backend directly instead of using the local proxy
- `VITE_API_CODE` if you want to keep the old query param shape with a custom demo token

Guest access now uses a browser-scoped guest session instead of a single shared `guest` account, so guest history persists per browser across reloads.

## Render Deployment

This repo is ready to run on Render as two services from the same Git repo:

- `bee2gether-api` as a Render `Web Service`
- `bee2gether-web` as a Render `Static Site`

The repo includes [`render.yaml`](render.yaml) so you can create both services from a single Blueprint.

### 1. Create the Blueprint

In Render:

1. Click `New` -> `Blueprint`
2. Connect this GitHub repo
3. Confirm Render detects [`render.yaml`](render.yaml)
4. Create both services

### 2. Backend Service Settings

The Blueprint config uses:

```text
buildCommand: pip install -r backend/requirements.txt
startCommand: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
healthCheckPath: /api/health
```

Required backend env vars:

```text
MONGODB_URI
MONGODB_DB_NAME=bee2gether
FRONTEND_ORIGIN=https://<your-frontend-service>.onrender.com
SUPABASE_URL
SUPABASE_SECRET_KEY
SUPABASE_BUCKET=event-images
```

### 3. Frontend Service Settings

The Blueprint config uses:

```text
rootDir: frontend
buildCommand: npm install && npm run build
staticPublishPath: frontend/dist
```

Required frontend env vars:

```text
VITE_API_BASE_URL=https://<your-backend-service>.onrender.com/api
VITE_API_CODE=render-demo
```

The static site also includes a rewrite rule so Vue Router routes resolve to `index.html`.

### 4. MongoDB Atlas Allowlist

For Atlas, allowlist the Render outbound CIDR range(s) for the backend service region. Do this in Atlas:

1. `Network Access`
2. Add the outbound CIDR range(s) shown in the Render backend service's `Connect` -> `Outbound` section
3. Remove temporary `0.0.0.0/0` after Render connectivity is confirmed

### 5. Render Health Check

The backend now exposes:

```text
GET /api/health
```

Render uses this endpoint for zero-downtime deploy health checks.

## Optional Vercel Deployment

If you still want to use Vercel, the legacy configuration remains in place.

- `vercel.json` is configured to build the Vue frontend and expose the Python API entrypoint from `api/index.py`.
- Root [`requirements.txt`](requirements.txt) is present for Vercel's Python runtime, and [`.python-version`](.python-version) pins deployment to Python 3.12.
- For a real persistent demo, set:
  - `MONGODB_URI`
  - `MONGODB_DB_NAME`
  - `FRONTEND_ORIGIN`
  - `SUPABASE_URL`
  - `SUPABASE_SECRET_KEY`
  - `SUPABASE_BUCKET`

### Exact Vercel Environment Variables

Use these values in Vercel Project Settings -> Environment Variables for both `Production` and `Preview` unless noted otherwise:

```text
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster-url>/<db>?retryWrites=true&w=majority
MONGODB_DB_NAME=bee2gether
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_SECRET_KEY=<supabase-secret-key>
SUPABASE_BUCKET=event-images
FRONTEND_ORIGIN=*
```

Do not set these for a same-project Vercel deployment unless you intentionally want different behavior:

```text
VITE_API_BASE_URL
USE_MEMORY_DB
```

Optional:

```text
VITE_API_CODE=vercel-demo
```

That variable only changes the compatibility query string sent by the frontend. The backend does not require it.

### Where To Get Each Value

- `MONGODB_URI`: MongoDB Atlas -> Database -> Connect -> Drivers
- `MONGODB_DB_NAME`: the logical database name you want this app to use, for example `bee2gether`
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_SECRET_KEY`: Supabase -> Project Settings -> API Keys -> secret key
- `SUPABASE_BUCKET`: the public storage bucket name you create for event images, for example `event-images`
- `FRONTEND_ORIGIN`: `*` is the simplest choice here because the frontend and API are served from the same Vercel project and preview URLs change per deployment

The backend still accepts the legacy `SUPABASE_SERVICE_ROLE_KEY` env var as a fallback, but `SUPABASE_SECRET_KEY` is now the preferred name and should be used for new deployments.

### Vercel Deploy Steps

```bash
cd cloudAppBeeCW-1
vercel
```

Then:

1. Set the environment variables above in Vercel.
2. Redeploy once after adding them.
3. For production, run `vercel --prod`.

For local parity with Vercel:

```bash
vercel dev
```

You can copy from [`.env.vercel.example`](.env.vercel.example) when entering the variables.

## Verification

Backend compatibility tests:

```bash
cd cloudAppBeeCW-1
source .venv/bin/activate
python -m unittest backend/tests/test_fastapi_app.py
```

This suite exercises:

- user creation and login
- group creation
- event creation
- group event embedding
- map event retrieval

## Legacy Code

The old Azure Function directories are still present for reference during the migration, but the new app entrypoint is [`backend/main.py`](backend/main.py). They are no longer part of the active deployment path.
