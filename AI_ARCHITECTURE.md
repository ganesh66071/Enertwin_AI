# EnerTwin AI Architecture

## 1. Campus-scoped data pipeline

The AI pipeline is anchored to a single `campus_id` and processes only that campus’s records. It begins with data cleaning, duplicate removal, missing value imputation, invalid value filtering, and hour/day feature creation. All downstream analytics and ML models read from that campus-specific data slice only.

## 2. Feature engineering

The preprocessing stage derives features such as hourly energy, rolling mean/standard deviation, energy change, occupancy ratio, HVAC ratio, lighting ratio, and equipment ratio. These features are used to power anomaly detection and forecasting.

## 3. Anomaly detection

The anomaly engine combines:
- Isolation Forest on the campus feature matrix
- Rolling statistical baseline detection for deviation from expected energy
- Severity scoring based on deviation percentage

Each anomaly includes actual vs expected energy, deviation percentage, anomaly score, root cause, and contributing factors.

## 4. Forecasting

The forecasting model uses lag features and rolling windows for energy demand prediction. The pipeline trains per campus and produces hourly predictions for a 24h horizon.

## 5. Optimization engine

Optimization uses a weighted reduction model across HVAC, lighting, and equipment adjustments. This produces multiple scenarios, calculates energy savings, cost savings, CO2 reduction, and ROI, and selects the most feasible recommendation.

## 6. Insight engine

The insight layer converts raw ML outputs into deterministic, structured facts before GenAI formatting. It summarises the major anomalies, forecast peaks, and optimization opportunities for the campus.

## 7. RAG knowledge layer

The retrieval layer uses a compact energy knowledge base. It indexes documents such as HVAC efficiency, lighting efficiency, peak demand management, and campus energy management. The retriever uses keyword-driven matching with optional vector engine support when available.

## 8. GenAI analyst

The GenAI layer consumes the structured analytics and RAG context and explains the numerical results in human-readable language. It explicitly avoids inventing numbers and falls back to deterministic model insights when LLM access is unavailable.

## 9. API flow

- `GET /api/ai/{campus_id}/status`
- `GET /api/ai/{campus_id}/anomalies`
- `GET /api/ai/{campus_id}/forecast`
- `GET /api/ai/{campus_id}/optimization`
- `GET /api/ai/{campus_id}/energy-score`
- `GET /api/ai/{campus_id}/building-intelligence`
- `GET /api/ai/{campus_id}/executive-report`
- `POST /api/ai/{campus_id}/chat`

The existing campus routes remain intact, while the new AI endpoints sit on top of the same FastAPI backend and campus data model.
