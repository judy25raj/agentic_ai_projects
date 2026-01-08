# scripts/00_ingest_pdfs.py
import argparse, json, sys
from pathlib import Path
from typing import List, Iterable
import numpy as np
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

def chunk_text(text: str, max_chars: int, overlap: int) -> Iterable[str]:
    if not text:
        return
    start = 0
    n = len(text)
    if max_chars <= 0:
        max_chars = 800
    if overlap < 0:
        overlap = 0
    while start < n:
        end = min(start + max_chars, n)
        yield text[start:end].strip()
        if end >= n:
            break
        start = max(0, end - overlap)

def iter_pdf_chunks(pdf_path: Path, max_pages: int, max_chars: int, overlap: int) -> Iterable[str]:
    reader = PdfReader(str(pdf_path))
    pages = reader.pages[:max_pages] if max_pages > 0 else reader.pages
    for i, pg in enumerate(pages, 1):
        try:
            txt = pg.extract_text() or ""
        except Exception:
            txt = ""
        for ch in chunk_text(txt, max_chars=max_chars, overlap=overlap):
            if ch:
                yield ch

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf_dir", required=True, help="Folder with PDFs")
    ap.add_argument("--out_dir", required=True, help="Folder to write index files")
    ap.add_argument("--embed_model", default="sentence-transformers/all-MiniLM-L6-v2")
    ap.add_argument("--batch_size", type=int, default=64, help="Embedding batch size")
    ap.add_argument("--max_pages", type=int, default=40, help="Limit pages per PDF (0 = no limit)")
    ap.add_argument("--max_chars", type=int, default=600, help="Chunk size")
    ap.add_argument("--overlap", type=int, default=60, help="Chunk overlap")
    args = ap.parse_args()

    pdf_dir = Path(args.pdf_dir)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(pdf_dir.glob("*.pdf"))
    if not pdfs:
        print(f"[ingest] No PDFs found in {pdf_dir}", file=sys.stderr)
        print(json.dumps({"status":"empty","indexed_chunks":0,"dim":0}))
        return

    print(f"[ingest] PDFs: {len(pdfs)} | model: {args.embed_model}", flush=True)
    model = SentenceTransformer(args.embed_model)

    all_texts: List[str] = []
    all_embs: List[np.ndarray] = []

    batch: List[str] = []
    for p in pdfs:
        print(f"[ingest] Reading {p.name}", flush=True)
        for ch in iter_pdf_chunks(p, max_pages=args.max_pages, max_chars=args.max_chars, overlap=args.overlap):
            batch.append(ch)
            if len(batch) >= args.batch_size:
                em = model.encode(batch, normalize_embeddings=True)
                all_embs.append(em.astype(np.float32))
                all_texts.extend(batch)
                print(f"[ingest]  embedded +{len(batch)} (total {len(all_texts)})", flush=True)
                batch = []

    if batch:
        em = model.encode(batch, normalize_embeddings=True)
        all_embs.append(em.astype(np.float32))
        all_texts.extend(batch)
        print(f"[ingest]  embedded +{len(batch)} (total {len(all_texts)})", flush=True)

    if not all_texts:
        print(json.dumps({"status":"empty","indexed_chunks":0,"dim":0}))
        return

    embs = np.vstack(all_embs)
    meta = {
        "embed_model": args.embed_model,
        "dim": int(embs.shape[1]),
        "count": int(embs.shape[0]),
        "batch_size": args.batch_size,
        "max_pages": args.max_pages,
        "max_chars": args.max_chars,
        "overlap": args.overlap,
    }

    (out / "embeddings.npy").write_bytes(embs.astype(np.float32).tobytes())
    (out / "texts.json").write_text(json.dumps(all_texts, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(json.dumps({"status":"ok","indexed_chunks":meta["count"],"dim":meta["dim"]}, indent=2), flush=True)

if __name__ == "__main__":
    main()
