# src/pipeline/generator.py
from __future__ import annotations

import os
from typing import List, Tuple, Dict

from dotenv import load_dotenv
from groq import Groq

# Ensure .env is read whenever this module is imported
load_dotenv()

# ---- Model resolution with graceful fallbacks (handles Groq deprecations) ----
# If an old/deprecated model is configured, we transparently switch to a supported one.
_MODEL_FALLBACKS = {
    "llama-3.1-70b-versatile": "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant": "llama-3.3-70b-versatile",
}

def _resolve_model() -> str:
    # Preference order: DEFAULT_MODEL -> GROQ_CHAT_MODEL -> safe default
    env_model = os.getenv("DEFAULT_MODEL") or os.getenv("GROQ_CHAT_MODEL")
    chosen = env_model or "llama-3.3-70b-versatile"
    return _MODEL_FALLBACKS.get(chosen, chosen)

MODEL_NAME = _resolve_model()
# -----------------------------------------------------------------------------


def _build_prompt(question: str, contexts: List[str]) -> str:
    """
    Build a compact, context-constrained prompt.
    The generator must answer ONLY from provided contexts.
    """
    ctx = "\n\n".join(f"- {c}" for c in contexts if isinstance(c, str))
    return (
        "You are a precise assistant. Answer ONLY using the context below.\n"
        'If the answer is not in the context, reply: "I don\'t know based on the provided context."\n\n'
        f"Context:\n{ctx}\n\n"
        f"Question: {question}\n"
        "Give a concise answer (≤ 3 sentences)."
    )


def generate_answer(question: str, contexts: List[str]) -> Tuple[str, Dict]:
    """
    Generate an answer from Groq Chat Completions given a question + retrieved contexts.

    Returns:
        (answer_text, usage_dict)
        usage_dict includes: prompt_tokens, completion_tokens, total_tokens, model, provider
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Please add it to your .env or environment."
        )

    # Initialize Groq client
    client = Groq(api_key=api_key)

    # Construct prompt from contexts
    prompt = _build_prompt(question, contexts)

    # Call Groq
    resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "Answer strictly from the provided context."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
    )

    # Extract text & usage
    text = (resp.choices[0].message.content or "").strip()
    usage = {
        "prompt_tokens": getattr(resp.usage, "prompt_tokens", None),
        "completion_tokens": getattr(resp.usage, "completion_tokens", None),
        "total_tokens": getattr(resp.usage, "total_tokens", None),
        "model": MODEL_NAME,
        "provider": "groq",
    }

    # Safety net: if the model returned nothing, keep contract stable
    if not text:
        text = "I don't know based on the provided context."

    return text, usage
