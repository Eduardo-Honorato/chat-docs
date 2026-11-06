from functools import lru_cache

import anthropic
import chromadb
from sentence_transformers import SentenceTransformer

from config import CLAUDE_MODEL, COLLECTION, DB_PATH, EMBED_MODEL

SYSTEM_PROMPT = """Você é um assistente especializado na biblioteca padrão do Python.
Responda usando APENAS os trechos da documentação oficial fornecidos em <trechos>.

Regras:
- Responda no mesmo idioma da pergunta.
- Cite as fontes no texto com o número do trecho, por exemplo [1] ou [2].
- Inclua exemplos de código quando ajudarem, baseados nos trechos.
- Se os trechos não trouxerem a resposta, diga isso com clareza em vez de inventar.
- Seja direto e objetivo."""


@lru_cache(maxsize=1)
def _embedder() -> SentenceTransformer:
    return SentenceTransformer(EMBED_MODEL)


@lru_cache(maxsize=1)
def _collection():
    return chromadb.PersistentClient(path=DB_PATH).get_collection(COLLECTION)


@lru_cache(maxsize=1)
def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic()  # lê ANTHROPIC_API_KEY do ambiente


def retrieve(query: str, k: int = 6) -> list[dict]:
    embedding = _embedder().encode(["query: " + query], normalize_embeddings=True).tolist()
    result = _collection().query(query_embeddings=embedding, n_results=k)
    return [
        {"text": doc, **meta}
        for doc, meta in zip(result["documents"][0], result["metadatas"][0])
    ]


def retrieve_for(history: list[dict], k: int = 6) -> list[dict]:
    """Busca usando as duas últimas perguntas, para perguntas de acompanhamento funcionarem."""
    user_msgs = [m["content"] for m in history if m["role"] == "user"]
    return retrieve("\n".join(user_msgs[-2:]), k)


def stream_answer(history: list[dict], sources: list[dict]):
    context = "\n\n".join(
        f"[{i}] {s['title']} ({s['url']})\n{s['text']}" for i, s in enumerate(sources, 1)
    )
    system = f"{SYSTEM_PROMPT}\n\n<trechos>\n{context}\n</trechos>"
    messages = [{"role": m["role"], "content": m["content"]} for m in history]

    with _client().messages.stream(
        model=CLAUDE_MODEL, max_tokens=1500, system=system, messages=messages
    ) as stream:
        yield from stream.text_stream
