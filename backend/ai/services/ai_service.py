"""Core orchestration service for campus AI, ML, and GenAI."""

from __future__ import annotations

from typing import Any

from app.models.campus import Campus
from app.services.analytics_service import calculate_campus_analytics, get_building_analytics, get_campus_overview
from app.services.dataset_service import get_campus_records
from app.services.optimization_service import calculate_optimization_opportunities
from app.services.simulation_service import run_simulation
from ai.anomaly.detector import detect_anomalies_for_campus
from ai.forecasting.forecaster import forecast_campus
from ai.insights.insight_engine import build_insights
from ai.models.model_manager import get_or_train_model
from ai.optimization.optimizer import choose_best_scenario, generate_scenarios
from ai.rag.retriever import retrieve_relevant_documents
from ai.genai.analyst import generate_ai_answer


def get_ai_status(campus_id: str, db: Any) -> dict[str, Any]:
    records = get_campus_records(db, campus_id)
    try:
        get_or_train_model(campus_id, records)
    except Exception:
        pass
    return {
        "data_ready": bool(records),
        "preprocessing": "complete" if records else "pending",
        "anomaly_detection": "ready" if records else "pending",
        "forecasting": "ready" if records else "pending",
        "optimization": "ready" if records else "pending",
        "rag": "ready",
        "genai": "ready",
    }


def get_campus_ai_anomalies(db: Any, campus_id: str) -> dict[str, Any]:
    records = get_campus_records(db, campus_id)
    return detect_anomalies_for_campus(campus_id, records)


def get_campus_ai_forecast(db: Any, campus_id: str) -> dict[str, Any]:
    records = get_campus_records(db, campus_id)
    result = forecast_campus(campus_id, records, horizon_hours=24)
    result["forecast_horizon"] = "24h"
    return result


def get_campus_ai_optimization(db: Any, campus_id: str) -> dict[str, Any]:
    kpis = calculate_campus_analytics(db, campus_id)
    baseline_energy = float(kpis.get("total_energy_kwh", 0.0))
    baseline_peak = float(kpis.get("peak_demand_kw", 0.0))
    tariff = 8.2
    scenarios = generate_scenarios(baseline_energy, baseline_peak, tariff, 0.68)
    recommended = choose_best_scenario(scenarios)
    return {
        "campus_id": campus_id,
        "baseline_energy": round(baseline_energy, 2),
        "baseline_peak": round(baseline_peak, 2),
        "scenarios": scenarios,
        "recommended_action": recommended.get("recommended_action", "Scenario A"),
        "expected_savings": recommended.get("expected_savings", 0),
        "expected_cost_savings": recommended.get("expected_cost_savings", 0),
        "expected_co2_reduction": recommended.get("expected_co2_reduction", 0),
        "roi": recommended.get("roi", 0),
    }


def get_energy_score(db: Any, campus_id: str) -> dict[str, Any]:
    kpis = calculate_campus_analytics(db, campus_id)
    anomalies = get_campus_ai_anomalies(db, campus_id)
    score = min(100, max(0, int(30 * (100 - min(100, kpis.get("hvac_percentage", 0))) / 100 + 20 * (1 - min(1, anomalies.get("anomalies_detected", 0) / 10)) + 20 * (1 - min(1, kpis.get("peak_demand_kw", 0) / max(kpis.get("maximum_energy_kwh", 1), 1))) + 15 * (1 - min(1, kpis.get("hvac_percentage", 0) / 50)) + 15 * (1 - min(1, kpis.get("average_occupancy", 0) / 100)))))
    return {
        "campus_id": campus_id,
        "score": score,
        "score_breakdown": {
            "energy_efficiency": round(30 * (100 - min(100, kpis.get("hvac_percentage", 0))) / 100, 2),
            "anomaly_frequency": round(20 * (1 - min(1, anomalies.get("anomalies_detected", 0) / 10)), 2),
            "peak_demand": round(20 * (1 - min(1, kpis.get("peak_demand_kw", 0) / max(kpis.get("maximum_energy_kwh", 1), 1))), 2),
            "hvac_efficiency": round(15 * (1 - min(1, kpis.get("hvac_percentage", 0) / 50)), 2),
            "occupancy_efficiency": round(15 * (1 - min(1, kpis.get("average_occupancy", 0) / 100)), 2),
        },
    }


def get_building_intelligence(db: Any, campus_id: str) -> dict[str, Any]:
    buildings = get_building_analytics(db, campus_id)
    if not buildings:
        return {"campus_id": campus_id, "highest_consumption_building": None, "most_inefficient_building": None, "highest_anomaly_building": None, "buildings": []}
    buildings_sorted = sorted(buildings, key=lambda item: item["total_energy"], reverse=True)
    highest = buildings_sorted[0]
    most_inefficient = min(buildings, key=lambda item: item["efficiency_score"])
    highest_anomaly = max(buildings, key=lambda item: item["anomaly_count"]) if any(item["anomaly_count"] for item in buildings) else highest
    return {
        "campus_id": campus_id,
        "highest_consumption_building": highest["building_name"],
        "most_inefficient_building": most_inefficient["building_name"],
        "highest_anomaly_building": highest_anomaly["building_name"],
        "buildings": buildings,
    }


def get_campus_comparison(db: Any) -> list[dict[str, Any]]:
    comparison = []
    for campus_id in ["CAMP001", "CAMP002", "CAMP003"]:
        try:
            campus = db.query(Campus).filter(Campus.id == campus_id).first()
            kpis = calculate_campus_analytics(db, campus_id)
            anomalies = get_campus_ai_anomalies(db, campus_id)
            optimization = get_campus_ai_optimization(db, campus_id)
            score = get_energy_score(db, campus_id)
            comparison.append({
                "campus_id": campus_id,
                "campus_name": campus.name if campus else campus_id,
                "total_energy": kpis.get("total_energy_kwh", 0),
                "energy_per_occupant": round(kpis.get("total_energy_kwh", 0) / max(kpis.get("average_occupancy", 1), 1), 2),
                "peak_demand": kpis.get("peak_demand_kw", 0),
                "efficiency_score": score.get("score", 0),
                "co2": kpis.get("total_co2", 0),
                "anomaly_count": anomalies.get("anomalies_detected", 0),
                "optimization_potential": optimization.get("expected_savings", 0),
            })
        except Exception:
            continue
    return comparison


def get_executive_report(db: Any, campus_id: str) -> dict[str, Any]:
    overview = get_campus_overview(db, campus_id)
    kpis = overview["kpis"]
    anomalies = get_campus_ai_anomalies(db, campus_id)
    forecast = get_campus_ai_forecast(db, campus_id)
    optimization = get_campus_ai_optimization(db, campus_id)
    report = {
        "campus_id": campus_id,
        "executive_summary": {
            "energy_performance": f"Campus consumed {kpis.get('total_energy_kwh', 0):,.0f} kWh.",
            "key_issue": f"HVAC contributes {kpis.get('hvac_percentage', 0):.1f}% of the campus energy profile.",
            "anomaly": f"{anomalies['anomalies'][0]['building']} exceeded expected consumption by {anomalies['anomalies'][0]['deviation_percentage']}%.",
            "forecast": f"Peak demand is expected at {forecast.get('peak_time', 'next peak window')}.",
            "recommendation": f"Optimize {optimization.get('recommended_action', 'core HVAC scheduling')} actions.",
            "impact": f"Estimated savings: {optimization.get('expected_cost_savings', 0):,.0f} INR/month.",
        },
        "detail": {
            "energy_performance": kpis.get("total_energy_kwh", 0),
            "optimization": optimization,
        },
        "sources": ["ML anomaly detection", "Forecasting engine", "Optimization engine"],
    }
    return report


def chat_with_ai(db: Any, campus_id: str, message: str) -> dict[str, Any]:
    overview = get_campus_overview(db, campus_id)
    kpis = overview["kpis"]
    anomalies = get_campus_ai_anomalies(db, campus_id)
    forecast = get_campus_ai_forecast(db, campus_id)
    optimization = get_campus_ai_optimization(db, campus_id)
    docs = retrieve_relevant_documents(message, top_k=3)
    answer = generate_ai_answer(message, campus_id, {"score": get_energy_score(db, campus_id)["score"], "kpis": kpis}, anomalies, forecast, optimization)
    return {
        "campus_id": campus_id,
        "answer": answer["answer"],
        "sources": docs and [doc["title"] for doc in docs] or answer["sources"],
        "supporting_metrics": answer["supporting_metrics"],
    }
