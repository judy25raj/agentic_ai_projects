# Atomic Agent – Azure + Elastic Observability (Logs, APM, Metrics) + Vector Search Demo

This project demonstrates an **atomic agent** pattern running on an Azure VM (or locally) that emits **structured JSON logs**, produces **Elastic APM traces/transactions**, and includes example assets for **Elastic Agent / ingest pipelines** and **vector-search (embeddings) workflows**.

> ✅ This repo is **safe to publish**: it contains **no credentials**, and includes a `.env.example` template.

---

## What’s included

- **Atomic agent simulator** (`agent/atomic_agent.py`)
  - Generates realistic action events (success/failure, latency)
  - Writes structured logs to a rotating log file
  - Sends APM transactions/spans to Elastic APM (optional)

- **Elastic assets** (`elastic/`)
  - Example Elastic Agent / integration config
  - Index template
  - Ingest pipeline

- **Embeddings demos** (`embeddings/`)
  - Example scripts showing how you could generate embeddings
  - Example semantic search demo

- **Write-up** (`docs/project_report.md`)
  - Narrative project report / implementation notes

---

## Repo structure

```
atomic-agent-azure-elastic-observability/
├─ agent/
│  ├─ atomic_agent.py
│  ├─ config.yaml
│  └─ requirements.txt
├─ elastic/
├─ embeddings/
├─ docs/
├─ .env.example
└─ .gitignore
```

---

## Quick run (local)

1) Create a virtual env and install dependencies:

```bash
cd agent
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

2) Copy environment variables (optional APM):

```bash
cd ..
copy .env.example .env   # Windows PowerShell: Copy-Item .env.example .env
```

3) Run the agent:

```bash
python agent/atomic_agent.py
```

Logs will be written to the file configured in `agent/config.yaml` (default: `agent.log`).

---

## Configuration

- `agent/config.yaml` controls agent behavior (interval, success rate, actions list, etc.)
- `.env` controls Elastic APM settings (server url, service name, token)

---

## Security note

Do **not** commit `.env`, keys, or VM SSH material. This repo includes a `.gitignore` that blocks common secret/key file patterns.

---

## Resume keywords

Azure • Elastic Stack • Elastic APM • Observability • Structured Logging • Ingest Pipelines • Index Templates • Vector Search • Embeddings • Python Automation
