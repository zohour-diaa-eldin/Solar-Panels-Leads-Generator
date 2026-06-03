# Solar Lead AI

Solar Lead AI is a full-stack geospatial AI MVP for solar panel sales lead generation. It helps a solar company rank promising sales areas, analyze building footprints, and score rooftop opportunities with explainable lead-scoring logic.

The current demo focuses on France real-data screening and building-level analysis, with a Cairo/Egypt demo mode still available.

## What It Does

- Ranks candidate sales areas in France using solar, weather, and commercial roof proxies.
- Fetches real building footprints from OpenStreetMap sources when available.
- Stores projects and buildings in PostgreSQL + PostGIS.
- Scores buildings by rooftop solar opportunity.
- Shows buildings on an interactive Leaflet map.
- Explains each AI Lead Score with weighted components.
- Works without a Google Solar API key by using PVGIS and mockable providers.

## Demo Highlights

The dashboard includes:

- Country selector: France or Egypt demo.
- Best Sales Areas ranking for France.
- Interactive map with selectable ranked areas and building polygons.
- Layer selector for solar, temperature, and lead score analysis.
- Summary cards for total buildings, opportunity counts, and roof area.
- Top 20 leads table.
- Building detail panel with scoring explanation and recommended sales action.

## Map Layers

The map can be switched between three business views:

| Layer | Meaning | How to Read It |
|---|---|---|
| `Solar Potential` | Shows areas with stronger expected solar production. | Higher solar score means better expected PV output from PVGIS data. |
| `Temperature` | Shows heat risk and temperature suitability. | Higher heat risk can reduce panel efficiency, so this layer helps separate strong sun from excessive heat exposure. |
| `AI Lead Score` | Shows the final sales opportunity score after building analysis. | This is the most actionable layer for sales teams because it combines solar, roof area, existing panels, building type, and accessibility. |

In short:

- `Solar Potential`: where the sun/PV output is strongest.
- `Temperature`: where heat may become a performance risk.
- `AI Lead Score`: where the company should prioritize sales outreach.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite, Leaflet |
| Backend | Python, FastAPI, Pydantic |
| Database | PostgreSQL, PostGIS |
| ORM / GIS | SQLAlchemy, GeoAlchemy2, Shapely, PyProj |
| External data | PVGIS, Open-Meteo, OpenStreetMap |
| Deployment | Docker Compose |

## Architecture

```text
frontend/
  React + TypeScript dashboard
  Leaflet map
  France area ranking UI
  Building details and lead table

backend/
  FastAPI routes
  PostGIS models
  OSM building ingestion
  PVGIS solar provider
  Weather provider
  Lead scoring engine
  Mockable AI/vision providers

database/
  PostgreSQL + PostGIS
  Projects
  Buildings
  Geometry and scoring metadata
```

## Data Sources

| Source | Used For | Status |
|---|---|---|
| PVGIS | France solar potential and estimated PV output | Live API, no key required |
| Open-Meteo Archive | Historical temperature and summer max temperature | Live API, no key required |
| OpenStreetMap / Overpass | Building footprints | Live API when available |
| OpenStreetMap Map API | Building fallback for sampled small bboxes | Live API when available |
| Google Solar API | Future premium building-level solar integration | Optional placeholder |
| Panel Detection Provider | Existing solar panel detection | Mocked for MVP |

External public APIs can be rate-limited or temporarily unavailable. The app is designed to degrade gracefully and label fallback data instead of failing the demo.

## Lead Scoring Model

The current building score is explainable and weighted as:

| Component | Weight |
|---|---:|
| Estimated solar potential | 30% |
| Usable roof area | 25% |
| No existing solar panels | 20% |
| Building type priority | 15% |
| Accessibility / proximity proxy | 10% |

Building type priority:

- High: industrial, commercial, warehouse, school, hospital, retail, office.
- Medium: residential, apartment, house.
- Lower: unknown or low-confidence building type.

For France, PVGIS-backed solar data is used when Google Solar API is not configured. Temperature context is also included in the scoring explanation.

## France Workflow

1. Open the frontend.
2. Keep `Country = France`.
3. Click `Rank France`.
4. Review `Best Sales Areas`.
5. Select a ranked area, such as Marseille-Aix Industrial Corridor.
6. Switch map layers between:
   - `Solar Potential`
   - `Temperature`
   - `AI Lead Score`
7. Click `Analyze Buildings`.
8. Click a building polygon to inspect the lead score explanation.

The app creates a project for the selected French area, fetches buildings, stores them in PostGIS, scores them, and shows the top sales leads.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Backend health check and active provider mode |
| `POST` | `/api/projects` | Create a project |
| `GET` | `/api/projects/demo` | Create or fetch Cairo demo project |
| `GET` | `/api/projects/{id}` | Fetch project details |
| `POST` | `/api/projects/{id}/analyze-bbox` | Fetch buildings and score leads inside a bbox |
| `GET` | `/api/projects/{id}/buildings` | Return project buildings as GeoJSON |
| `GET` | `/api/projects/{id}/summary` | Return summary cards and top leads |
| `GET` | `/api/buildings/{id}` | Return one building as GeoJSON with scoring metadata |
| `POST` | `/api/france/rank-areas` | Rank candidate France sales areas |

Example France ranking request:

```bash
curl -X POST http://localhost:8000/api/france/rank-areas \
  -H "Content-Type: application/json" \
  -d '{"limit": 5, "include_weather": true, "include_pvgis": true}'
```

## Quick Start

Prerequisites:

- Docker Desktop
- Docker Compose

From the repository root:

```bash
cp .env.example .env
docker compose up --build -d
```

Open:

- Frontend: http://localhost:5173
- Backend docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

On Windows PowerShell, if Docker is installed but not available in the current shell:

```powershell
$env:Path = 'C:\Program Files\Docker\Docker\resources\bin;' + $env:Path
docker compose up --build -d
```

If the Docker engine is not running, open Docker Desktop first.

## Environment Variables

Copy `.env.example` to `.env`.

| Variable | Purpose | Required |
|---|---|---|
| `DATABASE_URL` | Backend database connection string | Yes in non-Compose runs |
| `GOOGLE_SOLAR_API_KEY` | Optional Google Solar API key | No |
| `OVERPASS_URL` | Primary Overpass endpoint | No |
| `OVERPASS_FALLBACK_URLS` | Comma-separated Overpass mirror list | No |
| `OSM_MAP_API_URL` | OSM Map API fallback endpoint | No |
| `PVGIS_URL` | PVGIS API endpoint | No |
| `OPEN_METEO_ARCHIVE_URL` | Open-Meteo archive endpoint | No |
| `FRANCE_WEATHER_YEAR` | Historical weather year used for ranking | No |
| `VITE_API_BASE_URL` | Frontend backend URL | No |

No API keys are hardcoded.

## Local Development Without Docker

Backend:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/solar_leads
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

You still need a local PostgreSQL + PostGIS database for backend development without Docker.

## Testing the Demo

Backend health:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "provider": "france_pvgis_plus_mock"
}
```

Check running containers:

```bash
docker compose ps
```

Follow backend logs:

```bash
docker compose logs -f backend
```

Build the frontend:

```bash
docker compose run --rm frontend npm run build
```

## Extension Points

The codebase is intentionally modular:

- `backend/app/services/solar_provider.py`
  - `GoogleSolarProvider`: optional Google Solar API integration.
  - `FranceAwareSolarProvider`: PVGIS-backed provider for France.
  - `MockSolarProvider`: deterministic fallback.
- `backend/app/services/france_ranking.py`
  - Ranks French sales areas using solar, weather, roof proxy, commercial priority, and accessibility.
- `backend/app/services/weather_provider.py`
  - Fetches historical temperature data.
- `backend/app/services/overpass_service.py`
  - Fetches buildings from Overpass and OSM Map API.
- `backend/app/services/panel_detection_provider.py`
  - Mocked panel detection with TODO hooks for satellite imagery and object detection.
- `backend/app/services/scoring.py`
  - Explainable weighted lead scoring.

## Roadmap

- Add persistent caching for PVGIS, weather, and OSM responses.
- Add Alembic migrations.
- Replace mocked panel detection with a YOLO/segmentation pipeline.
- Add Sentinel Hub or Copernicus satellite imagery support.
- Add user accounts and saved sales campaigns.
- Add CSV/GeoJSON export for sales teams.
- Add real Google Solar API buildingInsights support where coverage and cost make sense.

## Public Repo Notes

- This is an MVP/POC, not a production sales intelligence platform.
- External API availability and rate limits can affect live results.
- Data quality is surfaced in responses where fallbacks are used.
- Review OpenStreetMap, PVGIS, Open-Meteo, and any future provider terms before commercial deployment.
