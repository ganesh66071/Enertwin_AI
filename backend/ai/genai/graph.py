"""GenAI task orchestration wrapper."""

from __future__ import annotations

from typing import Any


def compose_graph_context(campus_id: str, metrics: dict[str, Any], anomalies: dict[str, Any], forecast: dict[str, Any], optimization: dict[str, Any], rag_docs: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "campus_id": campus_id,
        "metrics": metrics,
        "anomalies": anomalies,
        "forecast": forecast,
        "optimization": optimization,
        "rag": rag_docs,
    }
