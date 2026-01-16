# ⭐ Agentic AI Systems & Cloud Observability

**Author:** Judy Raj  

This repository contains **production-style Agentic AI and Cloud Observability projects** demonstrating how modern AI systems can be designed to be **grounded, evaluable, observable, and operationally reliable**.

The focus is on **real-world engineering practices**, not toy demos:
- Clear agent responsibilities  
- Deterministic and structured outputs  
- Evaluation and quality control  
- Secure configuration  
- End-to-end observability  

These projects reflect how **AI systems are built, monitored, and trusted in production environments**.

---

## 🧠 What This Portfolio Demonstrates

- Agentic AI workflows (multi-agent orchestration)
- Retrieval-Augmented Generation (RAG)
- Automated evaluation using Judge Agents
- Cloud-native deployment on Azure
- Observability-first design (logs, metrics, traces)
- Secure configuration and production hygiene
- Interview-ready documentation and structure

---

## 📌 Featured Projects

---

## 🔹 Project 1: Agentic AI — PDF RAG + Judge Agent  
📁 **Folder:** `agentic-ai-pdf-rag-judge`

### Problem Addressed
LLM-based systems must produce **grounded answers** and provide **confidence in output quality**. This project demonstrates how multiple AI agents collaborate to ensure accuracy, relevance, and traceability when answering questions from documents.

### Architecture Flow
- PDF documents are ingested and chunked  
- A **Retriever Agent** performs vector-based semantic search  
- A **Generator Agent** produces a grounded answer using retrieved context  
- A **Judge Agent** evaluates answer quality and relevance  
- Structured JSON outputs are produced for scoring and traceability  
- *(Optional)* Traces and spans are emitted to **Langfuse** for observability  

### Key Capabilities
- Multi-agent workflow (Retriever → Generator → Judge)
- Local vector embeddings and semantic search
- LLM-driven grounded answer generation
- Automated evaluation and scoring
- Deterministic, structured outputs
- Optional observability with Langfuse

### Tech & Skills
**Python · Agentic AI · RAG · Vector Embeddings · LLM Evaluation · Prompt Engineering · Observability**

📌 **Status:** ✅ Complete (Portfolio / Interview-ready)

---

## 🔹 Project 2: Atomic Agent on Azure with Elastic Observability  
📁 **Folder:** `atomic-agent-azure-elastic-observability`

### Problem Addressed
AI agents running in production must be **observable, debuggable, and auditable**. This project focuses on **operational visibility** rather than model accuracy alone.

### Architecture Flow
- Atomic agent runs on an Azure Linux VM  
- Agent emits structured logs and system metrics  
- Data flows through Elastic ingest pipelines  
- Elasticsearch indexes the telemetry  
- Kibana dashboards provide real-time visibility  

### Key Capabilities
- Atomic agent execution model
- Azure VM–based deployment
- Structured JSON logging
- Centralized metrics and dashboards
- Infrastructure and observability views in Kibana
- Production-style telemetry pipeline

### Tech & Skills
**Azure · Elastic Stack · Observability · Cloud Operations · Automation · Platform Engineering**

📌 **Status:** ✅ Complete (Portfolio / Interview-ready)

---

## 📁 Repository Structure

```
agentic_ai_projects/
├── agentic-ai-pdf-rag-judge/
│   ├── README.md
│   ├── scripts/
│   ├── src/
│   ├── data/              # gitignored
│   └── .env.example
│
├── atomic-agent-azure-elastic-observability/
│   ├── agent/
│   ├── elastic/
│   ├── embeddings/
│   ├── docs/
│   ├── screenshots/
│   └── README.md
│
├── .gitignore
└── README.md
```

---

## 🔐 Security & Configuration

- Sensitive values are **never committed**
- Environment variables are managed using `.env` files
- Each project includes a `.env.example` template
- `.gitignore` enforces safe portfolio practices

---

## ▶️ How to Use This Repository

Each project is **self-contained**.

1. Navigate into a project folder  
2. Read the project-specific `README.md`  
3. Follow setup and execution instructions  

This allows reviewers to explore projects independently without confusion.

---

## 👩‍💻 About the Author

Senior Platform & Automation Engineer with extensive experience in:
- Enterprise application development  
- Automation and production support  
- Cloud infrastructure and observability  
- Agentic AI system design and evaluation  

Currently focused on **Agentic AI architectures**, **AI evaluation frameworks**, **Python automation**, and **cloud observability** in regulated and production-grade environments.

This repository emphasizes **implementation-focused engineering** over academic demonstrations.

---

## 🏁 Portfolio Notes

- All projects are **complete and intentional**
- Code and documentation reflect **production thinking**
- Designed for **interviews, technical discussions, and hiring reviews**
