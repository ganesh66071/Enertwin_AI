"""Energy knowledge base with optional FAISS retrieval and text fallback."""

from __future__ import annotations

import re
from typing import Any

try:  # pragma: no cover
    import faiss
except Exception:  # pragma: no cover
    faiss = None

try:  # pragma: no cover
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover
    SentenceTransformer = None


ENERGY_DOCS = [
    {"title": "HVAC efficiency", "content": "HVAC systems are a major campus energy load. Scheduling, setpoint resets, and occupancy-based control can reduce unnecessary cooling and heating demand."},
    {"title": "Energy conservation", "content": "Energy conservation starts with reducing avoidable loads, aligning schedules to occupancy, and optimizing equipment runtime during off-peak hours."},
    {"title": "Building energy management", "content": "Building energy management systems should coordinate HVAC, lighting, and equipment loads to reduce peak demand and maintain comfortable conditions."},
    {"title": "Peak demand management", "content": "Peak demand can be reduced by shifting non-critical equipment loads outside the daily peak window and by trimming HVAC demand when occupancy is low."},
    {"title": "Lighting efficiency", "content": "Occupancy sensors, daylight dimming, and LED retrofits reduce lighting loads while preserving comfort and safety."},
    {"title": "Equipment scheduling", "content": "Commercial and campus equipment should be scheduled to avoid simultaneous run times that increase energy use and peak demand."},
    {"title": "Occupancy-based HVAC", "content": "Occupancy-aware HVAC scheduling prevents cooling or heating empty spaces and reduces unnecessary energy consumption."},
    {"title": "Carbon reduction", "content": "Lowering HVAC, lighting, and equipment loads reduces both operating cost and carbon emissions from campus electricity use."},
    {"title": "Energy tariffs", "content": "Demand charges and time-of-use tariffs make it valuable to move flexible equipment loads to lower-cost periods and reduce peak demand."},
    {"title": "Energy saving practices", "content": "Energy-saving practices include equipment tuning, lighting schedules, setpoint optimization, and preventive maintenance of chilled water systems."},
    {"title": "Campus energy management", "content": "Campus energy management requires a balanced strategy across building operations, occupancy patterns, and forecasting-informed demand response."},
]


class EnergyKnowledgeBase:
    def __init__(self) -> None:
        self.documents = ENERGY_DOCS
        self.model = None
        self.index = None
        self.embedding_dim = 384
        if SentenceTransformer is not None and faiss is not None:
            try:
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
                self.index = faiss.IndexFlatL2(self.embedding_dim)
            except Exception:
                self.model = None
                self.index = None

    def retrieve(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        if not query or not self.documents:
            return []
        normalized = query.lower()
        scored = []
        terms = re.findall(r"[a-z]+", normalized)
        for doc in self.documents:
            text = f"{doc['title']} {doc['content']}".lower()
            score = 0.0
            for term in terms:
                if term in text:
                    score += 2.0
                if term in doc['title'].lower():
                    score += 3.0
            scored.append({"title": doc["title"], "content": doc["content"], "score": score})
        ranked = sorted(scored, key=lambda x: x["score"], reverse=True)[:top_k]

        if self.model is not None and self.index is not None:
            try:
                embedding = self.model.encode([query])
                self.index.add(embedding.astype("float32"))
                dist, ids = self.index.search(embedding.astype("float32"), min(top_k, len(self.documents)))
                retrieved = []
                for idx in ids[0]:
                    if 0 <= int(idx) < len(self.documents):
                        doc = self.documents[int(idx)]
                        retrieved.append({"title": doc["title"], "content": doc["content"], "score": float(dist[0][ids[0].tolist().index(int(idx))])})
                if retrieved:
                    return retrieved
            except Exception:
                pass

        return [
            {"title": item["title"], "content": item["content"], "score": round(float(item["score"]), 2)}
            for item in ranked
        ]


DEFAULT_KB = EnergyKnowledgeBase()
