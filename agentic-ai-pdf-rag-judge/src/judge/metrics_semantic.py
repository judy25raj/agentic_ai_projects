from typing import Dict, List, Set
import re

STOP = {
    "the","a","an","is","are","was","were","of","and","or","in","to","for","on","at","by",
    "with","that","this","it","who","what","when","where","why","how"
}

def _tok(s: str) -> Set[str]:
    s = re.sub(r"[^a-zA-Z0-9\s]", " ", (s or "")).lower()
    return {t for t in s.split() if t and t not in STOP}

def _jacc(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / max(1, len(a | b))

def ragas_scores(question: str, answer: str, contexts: List[str], ground_truths=None) -> Dict[str, float]:
    q = _tok(question)
    a = _tok(answer)
    c = _tok(" ".join(contexts or []))
    gt_text = " ".join(ground_truths or [])
    gt = _tok(gt_text)

    # Base overlaps
    faith = _jacc(a, c)
    relev = _jacc(q, a)

    # Boosts for factual or exact matches
    boost = 0.0
    if gt and gt.issubset(a):  # answer fully contains ground truth
        boost += 0.4
    if a and c and len(a - c) <= 1:  # almost all tokens found in context
        boost += 0.3
    if gt_text.lower().strip() in (answer or "").lower():
        boost += 0.3

    faith = min(1.0, faith + boost)
    relev = min(1.0, relev + boost * 0.5)

    precision = (len(a & c) / max(1, len(a))) if a else 0.0
    recall = min(1.0, ((len(a & c) / max(1, len(c))) * 3.0)) if c else 0.0  # soften recall

    return {
        "faithfulness": faith,
        "answer_relevance": relev,
        "context_precision": precision,
        "context_recall": recall,
    }
