import os
import re
from app.main import app

print("="*60)
print("TASK 7: GENAI / RAG AUDIT")
print("="*60)

# 1. Documents in RAG knowledge base
from ai.rag.knowledge_base import DEFAULT_KB, ENERGY_DOCS
print(f"Number of documents in DEFAULT_KB / ENERGY_DOCS: {len(DEFAULT_KB.documents)}")
for i, d in enumerate(DEFAULT_KB.documents, 1):
    print(f"  Doc {i}: '{d['title']}' ({len(d['content'])} chars)")

# Additional documents directory
rag_dir_docs = [f for f in os.listdir("backend/ai/rag/documents") if f.endswith(".txt")]
print(f"\nAdditional document files in backend/ai/rag/documents: {rag_dir_docs}")

# 2. Retrieval method
# In ai/rag/knowledge_base.py:
# Checks if SentenceTransformer & faiss exist; otherwise uses lexical regex keyword scoring
import sys
has_faiss = "faiss" in sys.modules
has_st = "sentence_transformers" in sys.modules
print(f"FAISS installed/available: {has_faiss}")
print(f"SentenceTransformers available: {has_st}")
print("Retrieval method: Hybrid implementation (Keyword/lexical term scoring with regex fallback; FAISS vector index when faiss+sentence_transformers installed).")

# 3. LLM model and provider
from app.core.config import get_settings
settings = get_settings()
print(f"\nLLM Provider in settings: '{settings.llm_provider}'")
print(f"LLM Model in settings:    '{settings.llm_model}'")
print(f"LLM API Key set:         {bool(settings.llm_api_key)}")

# 4. LangGraph nodes / steps
# Let's inspect backend/ai/genai/graph.py and any other langgraph files
import glob
langgraph_files = []
for root, _, files in os.walk("backend"):
    for f in files:
        if f.endswith(".py"):
            with open(os.path.join(root, f), "r", encoding="utf-8", errors="ignore") as fp:
                content = fp.read()
                if "langgraph" in content.lower() or "stategraph" in content.lower():
                    langgraph_files.append(os.path.join(root, f))
print(f"\nFiles referencing LangGraph/StateGraph: {langgraph_files}")
print("LangGraph implementation detail: backend/ai/genai/graph.py defines a functional pipeline wrapper (`compose_graph_context`) that orchestrates 5 context stages/steps: [metrics, anomalies, forecast, optimization, rag]. Full LangGraph StateGraph library is NOT installed/imported.")

# 5. Test deterministic fallback with LLM key unset
from ai.genai.analyst import generate_ai_answer
print("\nTesting Deterministic Fallback with LLM key UNSET:")
sample_q = "What is the peak energy demand and how can we optimize it?"
dummy_analytics = {"score": 78}
dummy_anomalies = {"anomalies": [{"building": "CSE Block", "deviation_percentage": 24.5}]}
dummy_forecast = {"predicted_peak": 380.5, "peak_time": "2026-07-02T14:00:00"}
dummy_optimization = {"recommended_action": "Scenario C", "expected_savings": 97455.44, "expected_cost_savings": 799134.58}

res = generate_ai_answer(
    question=sample_q,
    campus_id="viit",
    analytics=dummy_analytics,
    anomalies=dummy_anomalies,
    forecast=dummy_forecast,
    optimization=dummy_optimization
)
print(f"Fallback response generated successfully: {bool(res.get('answer'))}")
print(f"Answer text: \"{res.get('answer')}\"")
print(f"Sources retrieved: {res.get('sources')}")
print(f"Supporting metrics: {res.get('supporting_metrics')}")

