import os
from pathlib import Path

# --- load .env manually ---
p = Path(".env")
if p.exists():
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ[k.strip()] = v.strip().strip('"').strip("'")

print("HOST:", os.getenv("LANGFUSE_HOST"))

try:
    from langfuse import get_client
    c = get_client()
    if hasattr(c, "trace"):
        t = c.trace(name="smoke_test", input={"ok": True})
        t.update(output={"done": True})
        print("✅ Mode:v3 TraceID:", getattr(t, "id", None))
    else:
        raise Exception("no .trace attribute")
except Exception as e:
    print("⚠️ v3 failed:", e)
    from langfuse import Langfuse
    s = Langfuse().span.create(name="smoke_test", input={"ok": True})
    print("✅ Mode:v2 TraceID:", getattr(s, "trace_id", getattr(s, "id", None)))
