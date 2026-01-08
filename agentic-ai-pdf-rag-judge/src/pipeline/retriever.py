# src/pipeline/retriever.py
import argparse, json, numpy as np
from pathlib import Path
from typing import List, Tuple
from sentence_transformers import SentenceTransformer

def _load_index(index_dir: str) -> Tuple[np.ndarray, List[str], dict]:
    idx = Path(index_dir)
    embs = np.fromfile(idx / "embeddings.npy", dtype=np.float32)
    meta = json.loads((idx / "meta.json").read_text(encoding="utf-8"))
    texts = json.loads((idx / "texts.json").read_text(encoding="utf-8"))
    embs = embs.reshape((meta["count"], meta["dim"]))
    return embs, texts, meta

def _embed_query(q: str, model_name: str) -> np.ndarray:
    model = SentenceTransformer(model_name)
    v = model.encode([q], normalize_embeddings=True).astype(np.float32)
    return v[0]

def retrieve(query: str, index_dir: str, top_k: int = 3, embed_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
    embs, texts, meta = _load_index(index_dir)
    qv = _embed_query(query, meta.get("embed_model", embed_model))
    sims = (embs @ qv)  # cosine, because vectors are normalized
    top_idx = np.argsort(-sims)[:top_k]
    results = [(int(i), float(sims[i]), texts[i]) for i in top_idx]
    return results

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--index_dir", default="data/index")
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--embed_model", default="sentence-transformers/all-MiniLM-L6-v2")
    args = ap.parse_args()

    results = retrieve(args.query, args.index_dir, top_k=args.k, embed_model=args.embed_model)
    print("\n[Top-K retrieved passages]\n")
    for rank, (i, score, txt) in enumerate(results, 1):
        print(f"[{rank}] score={score:.4f}  idx={i}\n{txt[:400]}\n")

if __name__ == "__main__":
    main()
