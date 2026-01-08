# src/observe/tracer.py  — Langfuse v2, explicit init, robust fallback + minimal logging
import os, time
from typing import Any, Dict, Optional

try:
    from langfuse import Langfuse
except Exception:
    Langfuse = None  # type: ignore

def _mk_client():
    pk = os.getenv("LANGFUSE_PUBLIC_KEY")
    sk = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST") or os.getenv("LANGFUSE_BASE_URL")
    if not (pk and sk and host):
        print("[tracer] Missing LANGFUSE_* envs; pk/sk/host required")
        return None, None
    if Langfuse is None:
        print("[tracer] langfuse SDK not importable")
        return None, None
    # Try both param names (some v2 builds used base_url)
    for kwargs in (
        {"public_key": pk, "secret_key": sk, "host": host},
        {"public_key": pk, "secret_key": sk, "base_url": host},
    ):
        try:
            client = Langfuse(**kwargs)
            # detect surface
            mode = "trace" if hasattr(client, "trace") else ("span" if hasattr(client, "span") else None)
            if mode:
                return client, mode
        except Exception as e:
            # try next kwargs variant
            continue
    print("[tracer] Failed to init Langfuse client with provided host:", host)
    return None, None

class Tracer:
    def __init__(self) -> None:
        self.client, self.mode = _mk_client()

    def start(self, name: str, input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        span = {
            "name": name, "input": input or {}, "output": None,
            "start": time.time(), "end": None,
            "span_obj": None, "trace_id": None
        }
        if not self.client:
            return span
        try:
            if self.mode == "trace":
                # v2 flavor exposing .trace(...)
                tr = self.client.trace(name=name, input=input or {})
                span["span_obj"] = tr
                # many builds expose id as the trace id
                span["trace_id"] = getattr(tr, "id", None) or getattr(tr, "trace_id", None)
            elif self.mode == "span":
                sp = self.client.span.create(name=name, input=input or {})
                span["span_obj"] = sp
                span["trace_id"] = getattr(sp, "trace_id", None) or getattr(sp, "id", None)
        except Exception as e:
            print("[tracer] start() error:", repr(e))
        return span

    def child(self, parent_trace_id: Optional[str], name: str, input: Optional[Dict[str, Any]] = None):
        return self.start(name, input)

    def end(self, span: Dict[str, Any], output: Optional[Dict[str, Any]] = None) -> Optional[str]:
        span["end"] = time.time()
        sp = span.get("span_obj")
        if not sp:
            return span.get("trace_id")
        try:
            if output is not None and hasattr(sp, "update"):
                sp.update(output=output)
            if hasattr(sp, "end"):
                sp.end()
        except Exception as e:
            print("[tracer] end() error:", repr(e))
        return span.get("trace_id")
