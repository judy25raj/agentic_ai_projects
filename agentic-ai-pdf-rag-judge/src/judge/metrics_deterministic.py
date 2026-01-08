from typing import Dict, List
import re

def jaccard(a: str, b: str) -> float:
    a_set, b_set = set(a.lower().split()), set(b.lower().split())
    if not a_set or not b_set:
        return 0.0
    return len(a_set & b_set) / max(1, len(a_set | b_set))

def format_checks(answer: str) -> Dict[str, float]:
    return {
        'too_short': 1.0 if len(answer.strip()) < 10 else 0.0,
        'contains_forbidden': 1.0 if re.search(r'(password|ssn)', answer, re.I) else 0.0,
    }

def context_overlap_score(answer: str, contexts: List[str]) -> float:
    ctx_tokens = set(' '.join(contexts).lower().split())
    ans_tokens = set(answer.lower().split())
    if not ans_tokens:
        return 0.0
    return len(ans_tokens & ctx_tokens) / max(1, len(ans_tokens))

def correctness_vs_gt(answer: str, gts: List[str]) -> float:
    if not gts:
        return 0.0
    return max(jaccard(answer, gt) for gt in gts)
