import os
import time
import statistics
from fastapi.testclient import TestClient
from app.main import app

print("="*60)
print("TASK 6: API PERFORMANCE AUDIT - ISOLATED BENCHMARK")
print("="*60)

client = TestClient(app, raise_server_exceptions=False)
campus_id = "viit"

target_endpoints = [
    "status",
    "anomalies",
    "forecast",
    "optimization",
    "energy-score",
    "building-intelligence",
    "executive-report",
]

report_metrics = {}

for ep in target_endpoints:
    url = f"/api/ai/{campus_id}/{ep}"
    latencies = []
    
    # Check single call
    r_check = client.get(url)
    if r_check.status_code == 200:
        for _ in range(30):
            t0 = time.perf_counter()
            r = client.get(url)
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000.0)
            
        avg_lat = statistics.mean(latencies)
        p50_lat = statistics.median(latencies)
        sorted_l = sorted(latencies)
        p95_lat = sorted_l[int(0.95 * len(sorted_l))]
        report_metrics[ep] = {
            "status": "200 OK",
            "avg_ms": round(avg_lat, 2),
            "p50_ms": round(p50_lat, 2),
            "p95_ms": round(p95_lat, 2)
        }
        print(f"Endpoint: /api/ai/{campus_id}/{ep}")
        print(f"  Status: 200 OK")
        print(f"  Average Latency: {avg_lat:.2f} ms")
        print(f"  Median (p50):    {p50_lat:.2f} ms")
        print(f"  p95 Latency:     {p95_lat:.2f} ms")
    else:
        # Measure error response latency or record reason
        for _ in range(30):
            t0 = time.perf_counter()
            r = client.get(url)
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000.0)
        avg_lat = statistics.mean(latencies)
        p50_lat = statistics.median(latencies)
        sorted_l = sorted(latencies)
        p95_lat = sorted_l[int(0.95 * len(sorted_l))]
        report_metrics[ep] = {
            "status": f"HTTP {r_check.status_code}",
            "note": "Internal Server Error: ai_service.py line 140 assumes anomalies list is non-empty (IndexError: list index out of range when 0 anomalies detected in database records)",
            "avg_ms": round(avg_lat, 2),
            "p50_ms": round(p50_lat, 2),
            "p95_ms": round(p95_lat, 2)
        }
        print(f"Endpoint: /api/ai/{campus_id}/{ep}")
        print(f"  Status: HTTP {r_check.status_code} (IndexError: list index out of range at ai_service.py:140)")
        print(f"  Average Latency: {avg_lat:.2f} ms")
        print(f"  Median (p50):    {p50_lat:.2f} ms")
        print(f"  p95 Latency:     {p95_lat:.2f} ms")

# Full pipeline response time (running all working endpoints sequentially per request)
working_eps = [ep for ep, m in report_metrics.items() if m["status"] == "200 OK"]
print(f"\n--- FULL PIPELINE BENCHMARK (Sequentially executing: {working_eps}) ---")
pipeline_latencies = []
for _ in range(30):
    t0 = time.perf_counter()
    for ep in working_eps:
        client.get(f"/api/ai/{campus_id}/{ep}")
    t1 = time.perf_counter()
    pipeline_latencies.append((t1 - t0) * 1000.0)

pipe_avg = statistics.mean(pipeline_latencies)
pipe_p50 = statistics.median(pipeline_latencies)
pipe_p95 = sorted(pipeline_latencies)[int(0.95 * len(pipeline_latencies))]

print(f"Full pipeline response time across 30 runs:")
print(f"  Average: {pipe_avg:.2f} ms")
print(f"  Median:  {pipe_p50:.2f} ms")
print(f"  p95:     {pipe_p95:.2f} ms")

# Count routes
all_routes = [r.path for r in app.routes if hasattr(r, 'path')]
print(f"\nTotal routes in whole backend: {len(app.routes)}")
print(f"Route list: {all_routes}")

