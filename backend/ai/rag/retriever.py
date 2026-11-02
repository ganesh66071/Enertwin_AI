"""Retrieval helpers for RAG context."""

from __future__ import annotations

from typing import Any

from ai.rag.knowledge_base import DEFAULT_KB


def retrieve_relevant_documents(question: str, top_k: int = 3) -> list[dict[str, Any]]:
    return DEFAULT_KB.retrieve(question, top_k=top_k)
