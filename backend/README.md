# EnerTwin AI Backend

Autonomous AI Energy Intelligence & Optimization Platform — FastAPI backend for the EnerTwin hackathon demo.

## Tech Stack

- Python 3.11+, FastAPI, Uvicorn, Pydantic
- SQLAlchemy + PostgreSQL
- Pandas, NumPy, Scikit-learn, XGBoost
- Optional LLM integration (OpenAI via LangChain)

## Quick Start (Windows)

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Copy environment file and configure PostgreSQL:

```powershell
copy .env.example .env
```

Create the database (PostgreSQL):

```sql
CREATE DATABASE enertwin;
```

Seed demo campuses (VIIT, Vignan University, MVV & MK Park):

```powershell
python seed_demo_data.py
```

Run the API:

```powershell
uvicorn app.main:app --reload
```

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Demo Campus IDs

| ID                  | Name              | Profile                                    |
| ------------------- | ----------------- | ------------------------------------------ |
| `viit`              | VIIT              | Engineering, high daytime/equipment load   |
| `vignan-university` | Vignan University | University + evening hostel peaks          |
| `mvv-mk-park`       | MVV & MK Park     | Residential, morning/evening + EV charging |

Each campus has **isolated** energy records — analytics always filter by `campus_id`.

## Key Endpoints

| Method | Endpoint                             | Description                |
| ------ | ------------------------------------ | -------------------------- |
| POST   | `/api/campuses`                      | Create campus              |
| GET    | `/api/campuses`                      | List campuses              |
| GET    | `/api/campuses/{id}/overview`        | Dashboard overview         |
| GET    | `/api/campuses/{id}/analytics`       | KPIs                       |
| GET    | `/api/campuses/{id}/energy-trend`    | Time series                |
| GET    | `/api/campuses/{id}/buildings`       | Building analytics         |
| GET    | `/api/campuses/{id}/anomalies`       | Anomaly detection          |
| GET    | `/api/campuses/{id}/forecast`        | Energy forecast            |
| GET    | `/api/campuses/{id}/optimization`    | Optimization opportunities |
| POST   | `/api/campuses/{id}/simulate`        | What-if simulation         |
| GET    | `/api/campuses/{id}/recommendations` | AI recommendations         |
| POST   | `/api/campuses/{id}/ask`             | AI analyst Q&A             |
| POST   | `/api/datasets/upload/{campus_id}`   | Upload CSV/XLSX dataset    |

## Dataset Upload

Supports flexible column names (`Energy Consumption`, `energy_kwh`, etc.). Missing fields are **deterministically derived** — never NaN/null in responses.

## Testing

```powershell
pytest tests/ -v
```

Tests use in-memory SQLite. The critical test verifies VIIT and Vignan University analytics are isolated.

## Environment Variables

See `.env.example` for:

- `DATABASE_URL` — PostgreSQL connection string
- `FIREBASE_*` — Optional Firebase token validation
- `LLM_API_KEY` — Optional LLM for recommendations/analyst
- `FRONTEND_URL` — CORS origin (default `http://localhost:3000`)

## Architecture

```
app/
├── api/          # REST route handlers
├── core/         # Config, DB, security
├── models/       # SQLAlchemy models
├── schemas/      # Pydantic request/response
├── services/     # Business logic
├── ml/           # Anomaly detection, forecasting
└── utils/        # Data mapping, cleaning, calculations
```

## Frontend Integration

Base URL: `http://localhost:8000/api`

CORS is configured for the Next.js frontend at `http://localhost:3000`. No frontend changes required — connect fetch calls to these endpoints when ready.
