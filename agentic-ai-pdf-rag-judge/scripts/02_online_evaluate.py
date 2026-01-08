# scripts/02_online_evaluate.py
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple

# --- ensure project root on sys.path ---
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
from tabulate import tabulate
load_dotenv()

# project modules
from src.pipeline.retriever import retrieve
from src.pipeline.generator import generate_answer

# Judge import (class preferred; function fallback)
try:
    from src.judge.judge_agent import JudgeAgent
    _JUDGE_IS_CLASS = True
except Exception:
    _JUDGE_IS_CLASS = False
    from src.judge.judge_agent import evaluate as _judge_evaluate
    class JudgeAgent:
        def __init__(self, model: str | None = None): self.model = model
        def score(self, q, ctxs, a, gt): return _judge_evaluate(q, ctxs, a, gt)
        def evaluate(self, q, ctxs, a, gt): return self.score(q, ctxs, a, gt)

# Langfuse (optional)
try:
    from langfuse import Langfuse
except Exception:
    Langfuse = None


def load_dataset(path: str) -> List[Dict[str, Any]]:
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "rows" in data:
        data = data["rows"]
    if not isinstance(data, list):
        raise ValueError("Dataset must be a JSON list or an object with 'rows'.")
    return data


def ensure_contexts(question: str,
                    row: Dict[str, Any],
                    index_dir: str,
                    top_k: int,
                    embed_model: str) -> Tuple[List[str], Dict[str, Any]]:
    if isinstance(row.get("contexts"), list) and row["contexts"] and isinstance(row["contexts"][0], str):
        ctx = row["contexts"]
        meta = {"used": "provided", "count": len(ctx), "idx": [], "preview": [c[:160] for c in ctx[:3]]}
        return ctx, meta
    results = retrieve(query=question, index_dir=index_dir, top_k=top_k, embed_model=embed_model)
    ctx = [r[2] for r in results]
    meta = {
        "used": "retrieved",
        "count": len(ctx),
        "idx": [int(r[0]) for r in results],
        "preview": [r[2][:160] for r in results],
        "scores": [float(r[1]) for r in results],
    }
    return ctx, meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="Path to JSON dataset")
    ap.add_argument("--report", required=True, help="Path to write JSON report")
    ap.add_argument("--index_dir", default="data/index", help="Vector index directory")
    ap.add_argument("--top_k", type=int, default=int(os.getenv("TOP_K", "3")))
    ap.add_argument("--embed_model", default=os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2"))
    ap.add_argument("--trace_name", default="online_evaluation")
    args = ap.parse_args()

    manual_tag = os.getenv("TRACE_TAG", "provider:groq")

    # Langfuse setup (optional)
    lf = None
    trace = None
    if Langfuse and os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
        lf = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )
        trace = lf.trace(name=args.trace_name, metadata={"top_k": args.top_k})
        trace.update(tags=[manual_tag])
        trace.update(input={
            "dataset": args.data,
            "index_dir": args.index_dir,
            "top_k": args.top_k
        })
    else:
        trace_id = str(uuid.uuid4())

    rows = load_dataset(args.data)
    judge = JudgeAgent()

    table_rows: List[List[str]] = []
    report_items: List[Dict[str, Any]] = []

    for idx, row in enumerate(rows, 1):
        q = row.get("question", "").strip()
        gt = row.get("ground_truth", "") or row.get("ground_truths", "")
        if not q:
            continue

        # retrieval (or use provided contexts)
        contexts, rmeta = ensure_contexts(q, row, index_dir=args.index_dir, top_k=args.top_k, embed_model=args.embed_model)

        if trace:
            trace.span(
                name="retrieval",
                input={"question": q, "idx": idx, "index_dir": args.index_dir, "top_k": args.top_k},
                output={"count": rmeta["count"], "idx": rmeta.get("idx", []), "preview": rmeta.get("preview", [])},
            )

        # generate
        t0 = time.time()
        answer, usage = generate_answer(q, contexts)
        gen_latency_ms = int((time.time() - t0) * 1000)

        if trace:
            trace.generation(
                name="generator.answer",
                model=usage.get("model"),
                input={"question": q, "contexts_count": len(contexts)},
                output={
                    "question": q,
                    "contexts": contexts,   # full contexts like the OpenAI-style view
                    "answer": answer,
                    "usage": usage,
                    "latency_ms": gen_latency_ms
                },
                metadata={"provider": usage.get("provider", "groq")},
            )

        # judge
        t1 = time.time()
        try:
            scores = judge.score(q, contexts, answer, gt)
        except AttributeError:
            scores = judge.evaluate(q, contexts, answer, gt)
        judge_latency_ms = int((time.time() - t1) * 1000)

        if trace:
            trace.generation(
                name="judge.verdict",
                model=scores.get("_model"),
                input={"question": q, "answer": answer[:300], "ground_truth": (gt or "")[:300]},
                output=scores,
                metadata={"provider": scores.get("_provider", "groq"), "latency_ms": judge_latency_ms},
            )

        # table
        table_rows.append([
            q[:28] + ("…" if len(q) > 28 else ""),
            f"{scores.get('faith', 0):.2f}",
            f"{scores.get('relev', 0):.2f}",
            f"{scores.get('prec', 0):.2f}",
            f"{scores.get('recall', 0):.2f}",
            scores.get("verdict", "FAIL"),
        ])

        # report item
        report_items.append({
            "idx": idx,
            "question": q,
            "contexts_used": rmeta,
            "answer": answer,
            "usage": usage,
            "scores": scores,
            "latency": {"gen_ms": gen_latency_ms, "judge_ms": judge_latency_ms},
        })

    # print table
    headers = ["question", "faith", "relev", "prec", "recall", "verdict"]
    if table_rows:
        print(tabulate(table_rows, headers=headers, tablefmt="github"))
    else:
        print("[warn] No rows evaluated.")

    # write report
    out = {
        "trace_id": getattr(trace, "id", None),
        "summary": {"count": len(report_items)},
        "items": report_items,
    }
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[ok] Report written to {args.report}")

    # top-level output summary (compact)
    if trace:
        avg_faith = round(sum(i["scores"]["faith"] for i in report_items) / len(report_items), 2) if report_items else None
        avg_relev = round(sum(i["scores"]["relev"] for i in report_items) / len(report_items), 2) if report_items else None
        trace.update(output={
            "report_path": args.report,
            "items_evaluated": len(report_items),
            "avg_faith": avg_faith,
            "avg_relev": avg_relev
        })

    if lf:
        lf.flush()
        lf.shutdown()


if __name__ == "__main__":
    main()
