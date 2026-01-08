from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Tuple, Set

from dotenv import load_dotenv
load_dotenv()

from groq import Groq

JUDGE_MODEL = os.getenv("GROQ_CHAT_MODEL", os.getenv("DEFAULT_MODEL", "llama-3.3-70b-versatile"))

SYSTEM_PROMPT = """You are an evaluation judge for a RAG system.
You MUST return a strictly-valid JSON object with EXACTLY this schema (all keys present):

{
  "scores": {
    "faithfulness": <float 0..1>,
    "relevance": <float 0..1>,
    "precision": <float 0..1>,
    "recall": <float 0..1>,
    "correctness_det": <float 0..1>
  },
  "format_issues": {
    "too_short": <0 or 1>,
    "contains_forbidden": <0 or 1>
  },
  "verdict": "<PASS or FAIL>",
  "reasons": [<short strings>]
}

Definitions:
- faithfulness: answer is supported by contexts (no hallucinations).
- relevance: answer addresses the question.
- precision: answer avoids extra info not supported by contexts/ground truth.
- recall: answer covers key facts from ground truth.
- correctness_det: overall correctness when objective (0..1).

Rules:
- Output ONLY the JSON. No prose, no backticks, no extra keys.
- If ground truth is empty, set recall=0.0 but still fill other fields.
"""

def _client() -> Groq:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is not set")
    return Groq(api_key=key)

def _make_messages(question: str, contexts: List[str], answer: str, ground_truth: str):
    ctx_joined = "\n---\n".join(contexts or [])
    user = f"""Question:
{question}

Contexts:
{ctx_joined}

Ground truth (may be empty):
{ground_truth}

Assistant answer:
{answer}
"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]

def _safe_load_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end+1])
            except Exception:
                pass
    return {}

def _tokset(s: str) -> Set[str]:
    return set(t for t in (s or "").lower().split() if t.isascii())

def _fallback_precision_recall(contexts: List[str], answer: str, ground_truth: str) -> Tuple[float, float]:
    ans = _tokset(answer)
    if not ans:
        return 0.0, 0.0
    ctx = _tokset(" ".join(contexts or []))
    gt = _tokset(ground_truth or "")
    # precision: fraction of answer tokens that are present in contexts (naive but robust)
    precision = len(ans & ctx) / len(ans) if ans else 0.0
    # recall: fraction of ground-truth tokens covered by answer (0 if no GT)
    recall = (len(gt & ans) / len(gt)) if gt else 0.0
    return float(precision), float(recall)

def _normalize_scores(obj: Dict[str, Any],
                      contexts: List[str],
                      answer: str,
                      ground_truth: str) -> Tuple[Dict[str, Any], Dict[str, float]]:
    """
    Returns (structured_for_langfuse, flat_for_table).
    Ensures all required fields exist; computes precision/recall if missing.
    """
    # If flat keys came back, lift to schema
    if "scores" not in obj:
        obj = {
            "scores": {
                "faithfulness": float(obj.get("faith", obj.get("faithfulness", 0)) or 0),
                "relevance": float(obj.get("relev", obj.get("relevance", 0)) or 0),
                "precision": float(obj.get("prec", obj.get("precision", 0)) or 0),
                "recall": float(obj.get("recall", 0) or 0),
                "correctness_det": float(obj.get("correctness_det", 0) or 0),
            },
            "format_issues": {
                "too_short": int(obj.get("too_short", 0) or 0),
                "contains_forbidden": int(obj.get("contains_forbidden", 0) or 0),
            },
            "verdict": obj.get("verdict", "FAIL"),
            "reasons": obj.get("reasons", []),
        }

    scores = obj.setdefault("scores", {})
    # fill missing using fallbacks
    if "precision" not in scores or "recall" not in scores or scores.get("precision") in (None, "") or scores.get("recall") in (None, ""):
        p, r = _fallback_precision_recall(contexts, answer, ground_truth)
        scores["precision"] = float(scores.get("precision", p) or p)
        scores["recall"] = float(scores.get("recall", r) or r)

    # make sure all numeric fields exist
    for k in ["faithfulness", "relevance", "precision", "recall", "correctness_det"]:
        scores[k] = float(scores.get(k, 0) or 0)

    obj["format_issues"] = obj.get("format_issues", {"too_short": 0, "contains_forbidden": 0})
    obj["verdict"] = obj.get("verdict", "FAIL")
    obj["reasons"] = obj.get("reasons", [])

    flat = {
        "faith": scores["faithfulness"],
        "relev": scores["relevance"],
        "prec": scores["precision"],
        "recall": scores["recall"],
    }
    return obj, flat

class JudgeAgent:
    def __init__(self, model: str | None = None):
        self.model = model or JUDGE_MODEL
        self.client = _client()

    def evaluate(self, question: str, contexts: List[str], answer: str, ground_truth: str) -> Dict[str, Any]:
        msgs = _make_messages(question, contexts, answer, ground_truth)
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=msgs,
            temperature=0.0,
            max_tokens=256,
        )
        raw = (resp.choices[0].message.content or "").strip()
        obj = _safe_load_json(raw)

        structured, flat = _normalize_scores(obj, contexts, answer, ground_truth)

        return {
            "faith": flat["faith"],
            "relev": flat["relev"],
            "prec": flat["prec"],
            "recall": flat["recall"],
            "verdict": structured.get("verdict", "FAIL"),
            "_raw": structured,     # structured object for Langfuse
            "_model": self.model,
            "_provider": "groq",
        }

    # alias used elsewhere
    def score(self, question: str, contexts: List[str], answer: str, ground_truth: str) -> Dict[str, Any]:
        return self.evaluate(question, contexts, answer, ground_truth)
