"""LLM provider abstraction for recommendations and analyst."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from app.core.config import get_settings

settings = get_settings()


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        pass


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage, SystemMessage

            llm = ChatOpenAI(api_key=self.api_key, model=self.model, temperature=0.2)
            response = llm.invoke(
                [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
            )
            return response.content
        except Exception as exc:
            return f"[LLM unavailable: {exc}]"


def get_llm_provider() -> Optional[LLMProvider]:
    if not settings.llm_configured:
        return None
    if settings.llm_provider.lower() == "openai":
        return OpenAIProvider(settings.llm_api_key, settings.llm_model)
    return OpenAIProvider(settings.llm_api_key, settings.llm_model)


def format_facts_for_llm(facts: dict[str, Any]) -> str:
    """Serialize analytics facts for LLM context."""
    lines = []
    campus = facts.get("campus", {})
    lines.append(f"Campus: {campus.get('name')} ({campus.get('campus_type')})")
    kpis = facts.get("kpis", {})
    lines.append(f"Total energy: {kpis.get('total_energy_kwh')} kWh")
    lines.append(f"HVAC: {kpis.get('hvac_percentage')}% | Lighting: {kpis.get('lighting_percentage')}% | Equipment: {kpis.get('equipment_percentage')}%")
    lines.append(f"Total cost: {kpis.get('total_cost')} | CO2: {kpis.get('total_co2')} kg")
    lines.append(f"Efficiency score: {kpis.get('efficiency_score')}")

    anomalies = facts.get("anomalies", {}).get("anomalies", [])[:5]
    if anomalies:
        lines.append("Top anomalies:")
        for a in anomalies:
            lines.append(f"  - {a['building']}: {a['actual_energy']} kWh (expected {a['expected_energy']}), {a['deviation_percent']}% deviation")

    opt = facts.get("optimization", {})
    if opt.get("opportunities"):
        lines.append(f"Optimization potential: save {opt.get('energy_saved')} kWh, {opt.get('cost_saved')} cost")

    buildings = facts.get("buildings", [])[:5]
    if buildings:
        lines.append("Top buildings by energy:")
        for b in buildings:
            lines.append(f"  - {b['building_name']}: {b['total_energy']} kWh")

    return "\n".join(lines)
