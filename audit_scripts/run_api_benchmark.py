import os
import time
import statistics
import logging
from fastapi.testclient import TestClient

# Disable sqlalchemy logging for benchmark
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

from app.main import app
from app.core.database import SessionLocal
from app.models.campus import Campus

print("="*60)
print("TASK 6: API PERFORMANCE AUDIT (MEASURING EXACT NUMBERS)")
print("="*60)

client = TestClient(app)

endpoints = [
    "status",
    "anomalies",
    "forecast",
    "optimization",
    "energy-score",
    "building-intelligence",
    "executive-report"
]

campus_id = "viit"
results = {}

for ep in endpoints:
    url = f"/api/ai/{campus_id}/{ep}"
    latencies = []
    
    # 1 warmup call
    res = client.get(url)
    status_code = res.status_code
    
    if status_code == 200:
        for _ in range(30):
            t0 = time.perf_counter()
            r = client.get(url)
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000.0)
            
        avg_lat = statistics.mean(latencies)
        p50_lat = statistics.median(latencies)
        sorted_l = sorted(latencies)
        p95_lat = sorted_l[int(0.95 * len(sorted_l))]
        results[ep] = {
            "status": "200 OK",
            "avg": round(avg_lat, 2),
            "p50": round(p50_lat, 2),
            "p95": round(p95_lat, 2)
        }
        print(f"Endpoint: /api/ai/{campus_id}/{ep}")
        print(f"  Status: 200 OK | Avg: {avg_lat:.2f} ms | p50: {p50_lat:.2f} ms | p95: {p95_lat:.2f} ms")
    else:
        results[ep] = {
            "status": f"HTTP {status_code}",
            "error": res.text,
            "avg": "NOT AVAILABLE",
            "p50": "NOT AVAILABLE",
            "p95": "NOT AVAILABLE"
        }
        print(f"Endpoint: /api/ai/{campus_id}/{ep}")
        print(f"  Status: HTTP {status_code} | Note: Threw 500 because {res.json().get('detail', res.text)}")

# Benchmark full pipeline for endpoints that succeed
working_endpoints = [ep for ep, data in results.items() if data.get("avg") != "NOT AVAILABLE"]
pipeline_latencies = []
if working_endpoints:
    for _ in range(30):
        t0 = time.perf_counter()
        for ep in working_endpoints:
            client.get(f"/api/ai/{campus_id}/{ep}")
        t1 = time.perf_counter()
        pipeline_latencies.append((t1 - t0) * 1000.0)
        
    print(f"\nFull Pipeline Response Time for {len(working_endpoints)} endpoints ({campus_id}):")
    print(f"  Endpoints included: {working_endpoints}")
    print(f"  Average: {statistics.mean(pipeline_latencies):.2f} ms")
    print(f"  Median (p50): {statistics.median(pipeline_latencies):.2f} ms")
    print(f"  p95: {sorted(pipeline_latencies)[int(0.95 * len(pipeline_latencies))]:.2f} ms")

print(f"\nTotal API routes defined in FastAPI backend: {len(app.routes)}")
print("="*60)

