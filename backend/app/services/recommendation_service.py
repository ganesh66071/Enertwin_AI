"""AI recommendation engine — facts first, LLM optional for narrative."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.services.analytics_service import calculate_campus_analytics, get_building_analytics, get_campus_overview
from app.services.anomaly_service import get_campus_anomalies
from app.services.llm_provider import format_facts_for_llm, get_llm_provider
from app.services.optimization_service import calculate_optimization_opportunities
from app.utils.data_cleaning import json_safe


def _rule_based_recommendations(
    campus_id: str,
    campus_name: str,
    kpis: dict,
    buildings: list[dict],
    anomalies: dict,
    optimization: dict,
) -> list[dict]:
    """Generate recommendations from computed facts only."""
    recs: list[dict] = []

    if kpis.get("hvac_percentage", 0) > 40:
        saving = round(optimization.get("energy_saved", 0) * 0.4, 2)
        cost = round(optimization.get("cost_saved", 0) * 0.4, 2)
        co2 = round(optimization.get("co2_saved", 0) * 0.4, 2)
        recs.append(
            {
                "title": f"Optimize {campus_name} HVAC Systems",
                "priority": "HIGH",
                "problem": f"HVAC consumes {kpis['hvac_percentage']:.1f}% of total campus energy ({kpis['hvac_energy_kwh']:.0f} kWh).",
                "recommendation": "Implement smart HVAC scheduling aligned with occupancy patterns and adjust setpoints during low-utilization periods.",
                "expected_energy_saving": saving,
                "expected_cost_saving": cost,
                "expected_co2_reduction": co2,
                "expected_monthly_saving": cost,
            }
        )

    for a in anomalies.get("anomalies", [])[:3]:
        if a["severity"] in ("critical", "warning"):
            energy_saving = round(abs(a["actual_energy"] - a["expected_energy"]) * 0.6, 2)
            cost_saving = round(energy_saving * (kpis.get("total_cost", 0) / max(kpis.get("total_energy_kwh", 1), 1)), 2)
            recs.append(
                {
                    "title": f"Address {a['building']} Anomaly",
                    "priority": "HIGH" if a["severity"] == "critical" else "MEDIUM",
                    "problem": f"{a['building']} energy at {a['actual_energy']} kWh vs expected {a['expected_energy']} kWh ({a['deviation_percent']}% deviation). Causes: {'; '.join(a['possible_causes'][:2])}",
                    "recommendation": f"Investigate and remediate root causes in {a['building']}. " + (a["possible_causes"][0] if a["possible_causes"] else ""),
                    "expected_energy_saving": energy_saving,
                    "expected_cost_saving": cost_saving,
                    "expected_co2_reduction": round(energy_saving * 0.68, 2),
                    "expected_monthly_saving": cost_saving,
                }
            )

    if buildings:
        worst = min(buildings, key=lambda b: b["efficiency_score"])
        if worst["efficiency_score"] < 70:
            saving = round(worst["total_energy"] * 0.1, 2)
            cost = round(saving * (kpis.get("total_cost", 0) / max(kpis.get("total_energy_kwh", 1), 1)), 2)
            recs.append(
                {
                    "title": f"Improve {worst['building_name']} Efficiency",
                    "priority": "MEDIUM",
                    "problem": f"{worst['building_name']} has the lowest efficiency score ({worst['efficiency_score']}) with {worst['total_energy']:.0f} kWh total consumption.",
                    "recommendation": "Conduct an energy audit focusing on HVAC runtime, lighting controls, and equipment scheduling.",
                    "expected_energy_saving": saving,
                    "expected_cost_saving": cost,
                    "expected_co2_reduction": round(saving * 0.68, 2),
                    "expected_monthly_saving": cost,
                }
            )

    if kpis.get("lighting_percentage", 0) > 18:
        saving = round(kpis["lighting_energy_kwh"] * 0.12, 2)
        cost = round(saving * (kpis.get("total_cost", 0) / max(kpis.get("total_energy_kwh", 1), 1)), 2)
        recs.append(
            {
                "title": "Optimize Campus Lighting",
                "priority": "MEDIUM",
                "problem": f"Lighting accounts for {kpis['lighting_percentage']:.1f}% of energy ({kpis['lighting_energy_kwh']:.0f} kWh).",
                "recommendation": "Install occupancy-based lighting controls and convert to LED where applicable.",
                "expected_energy_saving": saving,
                "expected_cost_saving": cost,
                "expected_co2_reduction": round(saving * 0.68, 2),
                "expected_monthly_saving": cost,
            }
        )

    if not recs and optimization.get("opportunities"):
        opp = optimization["opportunities"][0]
        recs.append(
            {
                "title": f"Implement {opp['category']}",
                "priority": "MEDIUM",
                "problem": opp["description"],
                "recommendation": f"Target {opp['potential_saving_pct']}% reduction in {opp['category'].lower()}.",
                "expected_energy_saving": opp["energy_kwh"],
                "expected_cost_saving": round(opp["energy_kwh"] * (kpis.get("total_cost", 0) / max(kpis.get("total_energy_kwh", 1), 1)), 2),
                "expected_co2_reduction": round(opp["energy_kwh"] * 0.68, 2),
                "expected_monthly_saving": round(opp["energy_kwh"] * (kpis.get("total_cost", 0) / max(kpis.get("total_energy_kwh", 1), 1)), 2),
            }
        )

    return recs[:8]


def get_recommendations(db: Session, campus_id: str) -> dict[str, Any]:
    """Generate data-grounded recommendations with optional LLM enhancement."""
    overview = get_campus_overview(db, campus_id)
    kpis = overview["kpis"]
    campus = overview["campus"]
    buildings = get_building_analytics(db, campus_id)
    anomalies = get_campus_anomalies(db, campus_id)
    optimization = calculate_optimization_opportunities(db, campus_id)

    recs = _rule_based_recommendations(
        campus_id, campus["name"], kpis, buildings, anomalies, optimization
    )

    llm = get_llm_provider()
    llm_enhanced = False
    if llm and recs:
        facts = {
            "campus": campus,
            "kpis": kpis,
            "anomalies": anomalies,
            "optimization": optimization,
            "buildings": buildings,
        }
        context = format_facts_for_llm(facts)
        system = (
            "You are an energy analyst. Rewrite the recommendation text to be clearer and actionable. "
            "DO NOT invent or change any numerical values. Only improve the problem and recommendation prose."
        )
        for rec in recs[:3]:
            user = f"Facts:\n{context}\n\nRecommendation to improve:\nTitle: {rec['title']}\nProblem: {rec['problem']}\nRecommendation: {rec['recommendation']}"
            enhanced = llm.generate(system, user)
            if enhanced and not enhanced.startswith("[LLM unavailable"):
                rec["recommendation"] = enhanced[:500]
                llm_enhanced = True

    return json_safe(
        {
            "success": True,
            "campus_id": campus_id,
            "recommendations": recs,
            "llm_enhanced": llm_enhanced,
        }
    )


def answer_campus_question(db: Session, campus_id: str, question: str) -> dict[str, Any]:
    """Grounded AI analyst — answers based on campus data only."""
    overview = get_campus_overview(db, campus_id)
    kpis = overview["kpis"]
    campus = overview["campus"]
    buildings = get_building_analytics(db, campus_id)
    anomalies = get_campus_anomalies(db, campus_id)
    optimization = calculate_optimization_opportunities(db, campus_id)

    q_lower = question.lower()
    sources = ["campus_analytics", "building_analytics"]

    # Rule-based grounded answers
    if "building" in q_lower and ("waste" in q_lower or "most" in q_lower or "highest" in q_lower):
        if buildings:
            top = buildings[0]
            answer = (
                f"{top['building_name']} has the highest energy consumption at {top['total_energy']:.0f} kWh "
                f"with an efficiency score of {top['efficiency_score']}. "
                f"It accounts for a significant share of {campus['name']}'s total {kpis['total_energy_kwh']:.0f} kWh consumption."
            )
        else:
            answer = "No building data available for this campus."
        return json_safe({"success": True, "campus_id": campus_id, "question": question, "answer": answer, "sources": sources, "llm_enhanced": False})

    if "hvac" in q_lower and ("save" in q_lower or "reduc" in q_lower):
        import re
        pct_match = re.search(r"(\d+)\s*%", question)
        pct = float(pct_match.group(1)) if pct_match else 15
        from app.services.simulation_service import run_simulation
        sim = run_simulation(db, campus_id, hvac_reduction_percent=pct)
        answer = (
            f"Reducing HVAC by {pct}% at {campus['name']} would save approximately "
            f"{sim['savings']['energy']:.0f} kWh, {sim['savings']['cost']:.0f} in cost, "
            f"and {sim['savings']['co2']:.0f} kg CO2. "
            f"Current HVAC share is {kpis['hvac_percentage']:.1f}% of total energy."
        )
        sources.append("simulation")
        return json_safe({"success": True, "campus_id": campus_id, "question": question, "answer": answer, "sources": sources, "llm_enhanced": False})

    if "optim" in q_lower or "first" in q_lower or "should" in q_lower:
        recs = _rule_based_recommendations(campus_id, campus["name"], kpis, buildings, anomalies, optimization)
        if recs:
            top = recs[0]
            answer = f"Priority recommendation: {top['title']}. {top['problem']} {top['recommendation']} Expected savings: {top['expected_energy_saving']:.0f} kWh."
        else:
            answer = f"{campus['name']} is operating efficiently with an efficiency score of {kpis['efficiency_score']}."
        sources.append("recommendations")
        return json_safe({"success": True, "campus_id": campus_id, "question": question, "answer": answer, "sources": sources, "llm_enhanced": False})

    if "high" in q_lower or "why" in q_lower or "consum" in q_lower:
        top_anomalies = anomalies.get("anomalies", [])[:2]
        parts = [
            f"{campus['name']} total energy is {kpis['total_energy_kwh']:.0f} kWh with peak demand {kpis['peak_demand_kw']:.0f} kW.",
            f"Breakdown: HVAC {kpis['hvac_percentage']:.1f}%, Lighting {kpis['lighting_percentage']:.1f}%, Equipment {kpis['equipment_percentage']:.1f}%.",
            f"Average occupancy is {kpis['average_occupancy']:.1f}%.",
        ]
        if top_anomalies:
            parts.append(f"Key anomaly: {top_anomalies[0]['building']} at {top_anomalies[0]['actual_energy']:.0f} kWh ({top_anomalies[0]['deviation_percent']}% above expected).")
        answer = " ".join(parts)
        sources.append("anomalies")
        return json_safe({"success": True, "campus_id": campus_id, "question": question, "answer": answer, "sources": sources, "llm_enhanced": False})

    # LLM fallback with strict grounding
    facts = format_facts_for_llm({
        "campus": campus, "kpis": kpis, "anomalies": anomalies,
        "optimization": optimization, "buildings": buildings,
    })
    llm = get_llm_provider()
    if llm:
        system = (
            "You are EnerTwin AI analyst. Answer ONLY using the provided campus data. "
            "Never invent numbers. If data is insufficient, say so. Be concise."
        )
        answer = llm.generate(system, f"Campus data:\n{facts}\n\nQuestion: {question}")
        return json_safe({"success": True, "campus_id": campus_id, "question": question, "answer": answer, "sources": sources, "llm_enhanced": True})

    answer = (
        f"Based on {campus['name']} data: total energy {kpis['total_energy_kwh']:.0f} kWh, "
        f"efficiency score {kpis['efficiency_score']}, {len(buildings)} buildings monitored."
    )
    return json_safe({"success": True, "campus_id": campus_id, "question": question, "answer": answer, "sources": sources, "llm_enhanced": False})
