import os
from typing import List, Dict, Any

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


def fetch_docs_without_vectors(es, index_pattern="atomic-agent-*", size=50):
    body = {
        "query": {
            "bool": {
                "must_not": {
                    "exists": {"field": "log_vector"}
                }
            }
        }
    }
    resp = es.search(index=index_pattern, body=body, size=size)
    return resp.get("hits", {}).get("hits", [])


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


def update_doc_vector(es, index, doc_id, vector):
    es.update(
        index=index,
        id=doc_id,
        body={"doc": {"log_vector": vector}},
    )


def main():
    es = create_es_client()
    docs = fetch_docs_without_vectors(es)
    if not docs:
        print("[INFO] No docs without log_vector found.")
        return

    print(f"[INFO] Generating embeddings for {len(docs)} documents.")
    for hit in docs:
        source = hit.get("_source", {})
        atomic = source.get("atomic", {})
        text = f"{atomic.get('action', '')} - {atomic.get('message', '')}".strip()
        if not text:
            continue
        try:
            emb = get_azure_openai_embedding(text)
            update_doc_vector(es, hit["_index"], hit["_id"], emb)
            print(f"[OK] Updated {hit['_id']} with vector of length {len(emb)}.")
        except Exception as exc:
            print(f"[ERROR] Failed to update {hit['_id']}: {exc}")


if __name__ == "__main__":
    main()
