# Agentic AI — PDF RAG + Judge Agent (with optional Langfuse)

This project demonstrates an **agentic RAG pipeline** that:
1) **Ingests PDFs** → chunks text → builds a local embedding index  
2) **Retrieves** the most relevant chunks for a question  
3) **Generates** a grounded answer using an LLM (Groq)  
4) **Evaluates** the answer with a **Judge Agent** and outputs a scored report  
5) (Optional) Sends **traces/spans** to **Langfuse** for observability

> ✅ Designed for portfolio use: clean structure, repeatable scripts, and no bundled private data.

---

## Tech Stack
- Python 3.10+
- Local embeddings: `sentence-transformers`
- LLM generation: `groq` (OpenAI-compatible chat client)
- Optional observability: `langfuse`
- PDF parsing: `pypdf`

---

## Quick Start

### 1) Install
```bash
python -m venv .venv
# Windows: .\.venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure environment
Copy the template and set keys (Groq is required for generation; Langfuse optional):
```bash
cp .env.example .env
```

### 3) Add PDFs
Place your PDFs here (ignored by git, safe for portfolio):
```
data/pdfs/
```

### 4) Ingest PDFs → build vector index
```bash
python scripts/00_ingest_pdfs.py --pdf_dir data/pdfs --out_dir data/index
```

### 5) Ask a question (Retrieve + Generate)
```bash
python scripts/01_playground_generate.py --question "What is the main policy described in the document?"
```

### 6) Run evaluation (Judge Agent)
```bash
python scripts/02_online_evaluate.py --data sample_eval.json --report output/report.json
```

---

## Repository Layout
- `scripts/00_ingest_pdfs.py` — PDF → chunks → embeddings → local index
- `scripts/01_playground_generate.py` — retrieve → generate → (optional) trace
- `scripts/02_online_evaluate.py` — dataset → judge → report
- `src/pipeline/retriever.py` — cosine retrieval over embeddings
- `src/pipeline/generator.py` — LLM answer generation (grounded in retrieved context)
- `src/judge/*` — Judge Agent + scoring utilities
- `src/observe/*` — Langfuse tracing helpers (optional)
- `data/pdfs/` — your PDFs (gitignored)
- `data/index/` — generated index (gitignored)

---

## Notes
- This project does **not** perform web search. Answers are grounded only in your ingested PDFs.
- If Langfuse keys are not provided, the pipeline still runs normally (without traces).

