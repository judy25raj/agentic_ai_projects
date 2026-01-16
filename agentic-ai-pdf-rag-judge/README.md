## Agentic AI --- PDF RAG + Judge Agent (with Optional Langfuse)

This project demonstrates a **production-style agentic RAG pipeline**
designed to generate **grounded answers from documents** and **validate
response quality** using a Judge Agent.

### What the Pipeline Does

-   Ingests PDFs → chunks text → builds a local embedding index
-   Retrieves the most relevant chunks for a given question
-   Generates a grounded answer using an LLM (Groq)
-   Evaluates the answer with a Judge Agent and produces a scored report
-   Optionally sends traces and spans to **Langfuse** for observability

✅ Designed for portfolio use: clean structure, repeatable scripts, and
no bundled private data.

------------------------------------------------------------------------

## Tech Stack

-   **Python 3.10+**
-   **Local embeddings:** sentence-transformers
-   **LLM generation:** Groq (OpenAI-compatible chat client)
-   **Observability (optional):** Langfuse
-   **PDF parsing:** pypdf

------------------------------------------------------------------------

## Quick Start

### 1) Install

``` bash
python -m venv .venv
# Windows: .\.venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure environment

Copy the template and set keys\
(Groq is required for generation; Langfuse is optional):

``` bash
cp .env.example .env
```

### 3) Add PDFs

Place your PDFs here (ignored by git, safe for portfolio use):

    data/pdfs/

### 4) Ingest PDFs → build vector index

``` bash
python scripts/00_ingest_pdfs.py --pdf_dir data/pdfs --out_dir data/index
```

### 5) Ask a question (Retrieve + Generate)

``` bash
python scripts/01_playground_generate.py   --question "What is the main policy described in the document?"
```

### 6) Run evaluation (Judge Agent)

``` bash
python scripts/02_online_evaluate.py   --data sample_eval.json   --report output/report.json
```

------------------------------------------------------------------------

## Repository Layout

-   `scripts/00_ingest_pdfs.py` --- PDF → chunks → embeddings → local
    index
-   `scripts/01_playground_generate.py` --- retrieve → generate →
    (optional) Langfuse trace
-   `scripts/02_online_evaluate.py` --- dataset → judge → scored report
-   `src/pipeline/retriever.py` --- cosine similarity retrieval
-   `src/pipeline/generator.py` --- grounded LLM answer generation
-   `src/judge/*` --- Judge Agent and scoring utilities
-   `src/observe/*` --- Langfuse tracing helpers (optional)
-   `data/pdfs/` --- input PDFs (gitignored)
-   `data/index/` --- generated vector index (gitignored)

------------------------------------------------------------------------

## Notes

-   This project does **not** perform web search
-   Answers are grounded **only** in ingested PDFs
-   If Langfuse keys are not provided, the pipeline runs normally
    without traces
