"""LLM-backed but deterministic energy analyst with fallback."""

from __future__ import annotations

from typing import Any

from ai.genai.prompts import SYSTEM_PROMPT
from ai.rag.retriever import retrieve_relevant_documents
from app.services.llm_provider import get_llm_provider


def build_fallback_answer(question: str, campus_id: str, analytics: dict[str, Any], anomalies: dict[str, Any], forecast: dict[str, Any], optimization: dict[str, Any]) -> str:
    text = [f"Campus {campus_id}: model-generated energy analysis."]
    if analytics.get("score") is not None:
        text.append(f"The current AI energy score is {analytics['score']}/100.")
    if anomalies.get("anomalies"):
        top = anomalies["anomalies"][0]
        text.append(f"The strongest anomaly is {top['building']} with {top['deviation_percentage']}% deviation from expected energy.")
    if forecast.get("predicted_peak"):
        text.append(f"The next peak is forecast at {forecast['peak_time']} with {forecast['predicted_peak']} kW.")
    if optimization.get("recommended_action"):
        text.append(f"Recommended action: {optimization['recommended_action']} with {optimization.get('expected_savings', 0)} kWh savings and {optimization.get('expected_cost_savings', 0)} INR savings estimated.")
    if not analytics and not anomalies.get("anomalies"):
        text.append("The campus has insufficient data for a detailed AI analysis; the system is showing the most recent model-derived insights.")
    return " ".join(text)


def generate_ai_answer(question: str, campus_id: str, analytics: dict[str, Any], anomalies: dict[str, Any], forecast: dict[str, Any], optimization: dict[str, Any]) -> dict[str, Any]:
    rag_docs = retrieve_relevant_documents(question, top_k=3)
    llm = get_llm_provider()
    supporting_metrics = []
    if optimization.get("recommended_action"):
        supporting_metrics.append({"label": "Recommended action", "value": optimization["recommended_action"]})
    if forecast.get("predicted_peak"):
        supporting_metrics.append({"label": "Forecast peak", "value": f"{forecast['predicted_peak']} kW at {forecast['peak_time']}"})
    if anomalies.get("anomalies"):
        top = anomalies["anomalies"][0]
        supporting_metrics.append({"label": "Top anomaly", "value": f"{top['building']} ({top['deviation_percentage']}% deviation)"})

    if llm is not None:
        facts = {
            "campus_id": campus_id,
            "analytics": analytics,
            "anomalies": anomalies,
            "forecast": forecast,
            "optimization": optimization,
            "rag": rag_docs,
            "question": question,
        }
        answer = llm.generate(SYSTEM_PROMPT, str(facts))
        if answer and not answer.startswith("[LLM unavailable"):
            return {
                "campus_id": campus_id,
                "answer": answer,
                "sources": [doc["title"] for doc in rag_docs],
                "supporting_metrics": supporting_metrics,
            }

    fallback_answer = build_fallback_answer(question, campus_id, analytics, anomalies, forecast, optimization)
    return {
        "campus_id": campus_id,
        "answer": fallback_answer,
        "sources": [doc["title"] for doc in rag_docs],
        "supporting_metrics": supporting_metrics,
    }
