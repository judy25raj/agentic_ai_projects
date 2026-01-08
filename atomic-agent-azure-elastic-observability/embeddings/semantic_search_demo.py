import os
import sys
from typing import List

from elasticsearch import Elasticsearch
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def get_env(name, default=""):
    value = os.getenv(name)
    return value if value else default


def create_es_client():
    endpoint = get_env("ES_ENDPOINT")
    api_key = get_env("ES_API_KEY")
    if not endpoint or not api_key:
        raise RuntimeError("ES_ENDPOINT and ES_API_KEY must be set.")
    return Elasticsearch(endpoint, api_key=api_key, verify_certs=True)


def get_azure_openai_embedding(text: str) -> List[float]:
    endpoint = get_env("AZURE_OPENAI_ENDPOINT")
    api_key = get_env("AZURE_OPENAI_API_KEY")
    deployment = get_env("AZURE_OPENAI_EMBED_DEPLOYMENT")
    if not endpoint or not api_key or not deployment:
        raise RuntimeError("Azure OpenAI environment variables are not fully set.")

    url = f"{endpoint}/openai/deployments/{deployment}/embeddings?api-version=2023-05-15"
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key,
    }
    payload = {"input": text}
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data["data"][0]["embedding"]


def main():
    if len(sys.argv) < 2:
        print("Usage: python semantic_search_demo.py 'your query text'")
        sys.exit(1)

    query_text = sys.argv[1]
    print(f"[INFO] Semantic search for: {query_text!r}")

    es = create_es_client()
    query_vector = get_azure_openai_embedding(query_text)

    body = {
        "knn": {
            "field": "log_vector",
            "query_vector": query_vector,
            "k": 5,
            "num_candidates": 25
        }
    }
    resp = es.search(index="atomic-agent-*", body=body)
    hits = resp.get("hits", {}).get("hits", [])
    print(f"[INFO] Got {len(hits)} hits.")
    for hit in hits:
        src = hit.get("_source", {})
        atomic = src.get("atomic", {})
        print("-" * 60)
        print("Score:", hit.get("_score"))
        print("Timestamp:", atomic.get("timestamp"))
        print("Agent:", atomic.get("agent_id"))
        print("Action:", atomic.get("action"))
        print("Status:", atomic.get("status"))
        print("Message:", atomic.get("message"))


if __name__ == "__main__":
    main()
