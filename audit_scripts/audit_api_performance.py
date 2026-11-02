import time
import statistics
import requests
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.campus import Campus

print("="*60)
print("TASK 6: API PERFORMANCE AUDIT")
print("="*60)

# Total number of endpoints in whole backend
routes = app.routes
print(f"Total API routes in FastAPI backend: {len(routes)}")
for r in routes:
    methods = getattr(r, 'methods', None)
    path = getattr(r, 'path', None)
    name = getattr(r, 'name', None)
    if path:
        print(f"  {methods} {path} (name: {name})")

endpoints = [
    "status",
    "anomalies",
    "forecast",
    "optimization",
    "energy-score",
    "building-intelligence",
    "executive-report",
]

campus_id = "viit"
client = TestClient(app)

print(f"\n--- BENCHMARKING GET ENDPOINTS FOR CAMPUS '{campus_id}' (30 requests each) ---")

pipeline_total_latencies = []

for ep in endpoints:
    url = f"/api/ai/{campus_id}/{ep}"
    latencies = []
    
    # Warmup 1 request
    res = client.get(url)
    if res.status_code != 200:
        print(f"ERROR: {url} returned status {res.status_code}: {res.text}")
        continue
        
    for _ in range(30):
        t0 = time.perf_counter()
        r = client.get(url)
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)
        
    avg_lat = statistics.mean(latencies)
    p50_lat = statistics.median(latencies)
    latencies_sorted = sorted(latencies)
    # p95 index: int(0.95 * 30) = 28
    p95_lat = latencies_sorted[int(0.95 * len(latencies_sorted))]
    
    print(f"Endpoint: /api/ai/{campus_id}/{ep}")
    print(f"  Status code: {r.status_code}")
    print(f"  Average latency: {avg_lat:.2f} ms")
    print(f"  Median (p50):    {p50_lat:.2f} ms")
    print(f"  p95 latency:     {p95_lat:.2f} ms")

print(f"\n--- FULL PIPELINE BENCHMARK (All 7 endpoints sequentially per campus) ---")
for _ in range(30):
    t0 = time.perf_counter()
    for ep in endpoints:
        client.get(f"/api/ai/{campus_id}/{ep}")
    t1 = time.perf_counter()
    pipeline_total_latencies.append((t1 - t0) * 1000.0)

print(f"Full pipeline response time for campus '{campus_id}' across 30 runs:")
print(f"  Average: {statistics.mean(pipeline_total_latencies):.2f} ms")
print(f"  Median:  {statistics.median(pipeline_total_latencies):.2f} ms")
print(f"  p95:     {sorted(pipeline_total_latencies)[int(0.95*len(pipeline_total_latencies))]:.2f} ms")
print("="*60)

