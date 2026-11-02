"""Backend integration tests."""

import io

import pandas as pd
import pytest


def test_static_demo_campuses_are_available(client):
    resp = client.get("/api/campuses")
    assert resp.status_code == 200
    names = {campus["name"] for campus in resp.json()["campuses"]}
    assert {"Vignan University", "VIIT", "Vignan Pharma"}.issubset(names)

    overview = client.get("/api/campuses/CAMP001/overview")
    assert overview.status_code == 200
    payload = overview.json()
    assert payload["campus"]["name"] == "Vignan University"
    assert payload["kpis"]["total_energy_kwh"] > 0


def test_create_campus(client):
    resp = client.post("/api/campuses", json={
        "name": "Test Campus",
        "location": "Test City",
        "campus_type": "Educational Campus",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Campus"
    assert "id" in data


def test_list_and_get_campus(client):
    create = client.post("/api/campuses", json={
        "name": "VIIT Test",
        "location": "Visakhapatnam",
        "campus_type": "Engineering Campus",
    })
    campus_id = create.json()["id"]

    listing = client.get("/api/campuses")
    assert listing.status_code == 200
    assert listing.json()["total"] >= 1

    detail = client.get(f"/api/campuses/{campus_id}")
    assert detail.status_code == 200
    assert detail.json()["name"] == "VIIT Test"


def test_campus_data_isolation(client):
    """CRITICAL: Verify analytics are filtered by campus_id."""
    viit = client.post("/api/campuses", json={
        "name": "VIIT",
        "location": "Visakhapatnam",
        "campus_type": "Engineering Campus",
    }).json()

    vignan = client.post("/api/campuses", json={
        "name": "Vignan University",
        "location": "Guntur",
        "campus_type": "University Campus",
    }).json()

    # Upload different datasets
    for campus_id, energy in [(viit["id"], 500), (vignan["id"], 200)]:
        df = pd.DataFrame([
            {"timestamp": "2026-08-01 08:00:00", "building": "Block A", "energy_kwh": energy},
            {"timestamp": "2026-08-01 09:00:00", "building": "Block A", "energy_kwh": energy * 1.1},
            {"timestamp": "2026-08-01 10:00:00", "building": "Block A", "energy_kwh": energy * 0.9},
            {"timestamp": "2026-08-01 11:00:00", "building": "Block A", "energy_kwh": energy * 1.05},
            {"timestamp": "2026-08-01 12:00:00", "building": "Block A", "energy_kwh": energy * 0.95},
        ])
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        resp = client.post(
            f"/api/datasets/upload/{campus_id}",
            files={"file": ("test.csv", buf, "text/csv")},
        )
        assert resp.status_code == 200

    viit_analytics = client.get(f"/api/campuses/{viit['id']}/analytics").json()
    vignan_analytics = client.get(f"/api/campuses/{vignan['id']}/analytics").json()

    viit_total = viit_analytics["kpis"]["total_energy_kwh"]
    vignan_total = vignan_analytics["kpis"]["total_energy_kwh"]

    assert viit_total > vignan_total * 2, f"VIIT ({viit_total}) should have much more energy than Vignan ({vignan_total})"
    assert viit_total != vignan_total


def test_dataset_upload(client):
    campus = client.post("/api/campuses", json={
        "name": "Upload Test",
        "location": "City",
        "campus_type": "General",
    }).json()

    df = pd.DataFrame([
        {"Date": "2026-01-01 10:00", "Building Name": "Lab 1", "Energy Consumption": 150.5},
        {"Date": "2026-01-01 11:00", "Building Name": "Lab 1", "Energy Consumption": 160.0},
        {"Date": "2026-01-01 12:00", "Building Name": "Lab 1", "Energy Consumption": 155.0},
        {"Date": "2026-01-01 13:00", "Building Name": "Lab 1", "Energy Consumption": 148.0},
        {"Date": "2026-01-01 14:00", "Building Name": "Lab 1", "Energy Consumption": 152.0},
    ])
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)

    resp = client.post(
        f"/api/datasets/upload/{campus['id']}",
        files={"file": ("energy.csv", buf, "text/csv")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["records_processed"] == 5


def test_analytics(client):
    campus = client.post("/api/campuses", json={
        "name": "Analytics Test",
        "location": "City",
        "campus_type": "General",
    }).json()

    df = pd.DataFrame([
        {"timestamp": f"2026-08-01 {h:02d}:00:00", "building": "A", "energy": 100 + h}
        for h in range(10)
    ])
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    client.post(f"/api/datasets/upload/{campus['id']}", files={"file": ("d.csv", buf, "text/csv")})

    overview = client.get(f"/api/campuses/{campus['id']}/overview")
    assert overview.status_code == 200
    assert overview.json()["kpis"]["total_energy_kwh"] > 0


def test_anomaly_detection(client):
    campus = client.post("/api/campuses", json={
        "name": "Anomaly Test",
        "location": "City",
        "campus_type": "General",
    }).json()

    energies = [100, 102, 98, 101, 500, 99, 103, 97]  # spike at index 4
    df = pd.DataFrame([
        {"timestamp": f"2026-08-01 {h:02d}:00:00", "building": "A", "energy": e}
        for h, e in enumerate(energies)
    ])
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    client.post(f"/api/datasets/upload/{campus['id']}", files={"file": ("d.csv", buf, "text/csv")})

    resp = client.get(f"/api/campuses/{campus['id']}/anomalies")
    assert resp.status_code == 200
    data = resp.json()
    assert "anomalies" in data


def test_forecast(client):
    campus = client.post("/api/campuses", json={
        "name": "Forecast Test",
        "location": "City",
        "campus_type": "General",
    }).json()

    rows = []
    for day in range(5):
        for hour in range(24):
            rows.append({
                "timestamp": f"2026-08-{day+1:02d} {hour:02d}:00:00",
                "building": "A",
                "energy": 100 + hour * 2,
            })
    df = pd.DataFrame(rows)
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    client.post(f"/api/datasets/upload/{campus['id']}", files={"file": ("d.csv", buf, "text/csv")})

    resp = client.get(f"/api/campuses/{campus['id']}/forecast")
    assert resp.status_code == 200
    data = resp.json()
    assert "forecast" in data


def test_simulation_changes_with_params(client):
    campus = client.post("/api/campuses", json={
        "name": "Sim Test",
        "location": "City",
        "campus_type": "General",
    }).json()

    df = pd.DataFrame([
        {"timestamp": f"2026-08-01 {h:02d}:00:00", "building": "A", "energy": 200, "hvac": 80, "lighting": 40, "equipment": 30}
        for h in range(10)
    ])
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    client.post(f"/api/datasets/upload/{campus['id']}", files={"file": ("d.csv", buf, "text/csv")})

    low = client.post(f"/api/campuses/{campus['id']}/simulate", json={
        "hvac_reduction_percent": 5,
        "lighting_reduction_percent": 0,
        "equipment_reduction_percent": 0,
    }).json()

    high = client.post(f"/api/campuses/{campus['id']}/simulate", json={
        "hvac_reduction_percent": 25,
        "lighting_reduction_percent": 15,
        "equipment_reduction_percent": 10,
        "peak_shift": True,
    }).json()

    assert high["savings"]["energy"] > low["savings"]["energy"]
    assert high["projected"]["energy"] < low["projected"]["energy"]
