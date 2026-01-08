# Atomic Agent Observability on Azure with Elastic Stack & Vector Search

This document explains the project at a high level so you can present it in interviews or as part of a portfolio.

## Overview

- A Python-based Atomic Agent runs on an Azure VM.
- The agent emits structured JSON logs and Elastic APM traces.
- Elastic Agent ships logs to an Elastic Cloud deployment on Azure.
- An ingest pipeline parses and enriches logs as they are indexed.
- A separate embeddings job reads logs, generates vector embeddings and stores them in the log_vector field.
- A semantic search demo script performs kNN search against log_vector.
- Kibana dashboards and APM UI are used to visualize system behavior and errors.

Use this together with README.md when you describe the solution to others.
