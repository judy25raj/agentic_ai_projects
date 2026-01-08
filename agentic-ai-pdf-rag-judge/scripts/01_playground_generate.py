# scripts/01_playground_generate.py
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import List

# --- ensure project root on sys.path ---
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv()

# project modules
from src.pipeline.retriever import retrieve
from src.pipeline.generator import generate_answer

# Langfuse (optional)
try:
    from langfuse import Langfuse
except Exception:
    Langfuse = None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--question", required=True, help="User question")
    ap.add_argument("--index_dir", default="data/index", help="Vector index directory")
    ap.add_argument("--top_k", type=int, default=int(os.getenv("TOP_K", "3")))
    ap.add_argument("--embed_model", default=os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2"))
    args = ap.parse_args()

    manual_tag = os.getenv("TRACE_TAG", "provider:groq")

    # ---- Langfuse top-level trace ----
    lf = None
    trace = None
    if Langfuse and os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
        lf = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST", "https://us.cloud.langfuse.com"),
        )
        trace = lf.trace(name="playground_generate", metadata={"top_k": args.top_k})
        # attach manual tag (shows in UI Tags)
        trace.update(tags=[manual_tag])
        # top-level input (so it appears in Traces table)
        trace.update(input={
            "question": args.question,
            "index_dir": args.index_dir,
            "top_k": args.top_k
        })

    # ---- Retrieve contexts ----
    results = retrieve(query=args.question, index_dir=args.index_dir, top_k=args.top_k, embed_model=args.embed_model)
    contexts: List[str] = [r[2] for r in results]
    ctx_idx: List[int] = [int(r[0]) for r in results]
    ctx_previews: List[str] = [r[2][:160] for r in results]

    if trace:
        trace.span(
            name="retrieval",
            input={"question": args.question, "index_dir": args.index_dir, "top_k": args.top_k},
            output={"contexts_idx": ctx_idx, "contexts_preview": ctx_previews},
        )

    # ---- Generate with Groq ----
    t0 = time.time()
    answer, usage = generate_answer(args.question, contexts)
    latency_ms = int((time.time() - t0) * 1000)

    if trace:
        # child event with full payload
        trace.generation(
            name="generator.answer",
            model=usage.get("model"),
            input={"question": args.question, "contexts_count": len(contexts)},
            output={
                "question": args.question,
                "contexts": contexts,   # FULL contexts (to match your OpenAI view)
                "answer": answer,
                "usage": usage,
                "latency_ms": latency_ms
            },
            metadata={"provider": usage.get("provider", "groq")},
        )
        # top-level output (visible in Traces table)
        trace.update(output={
            "question": args.question,
            "contexts": contexts,      # full contexts at the trace level
            "answer": answer,
            "usage": usage
        })

    # ---- Print result JSON ----
    out = {
        "trace_id": getattr(trace, "id", None),
        "question": args.question,
        "contexts_idx": ctx_idx,
        "contexts_preview": ctx_previews,
        "answer": answer,
        "usage": usage,
        "latency_ms": latency_ms,
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))

    if lf:
        lf.flush()
        lf.shutdown()


if __name__ == "__main__":
    main()
