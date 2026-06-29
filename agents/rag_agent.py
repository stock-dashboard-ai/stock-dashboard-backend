import os
from pinecone import Pinecone
from utils.watsonx import get_embedder


def run_rag(ticker: str, query: str) -> tuple[str, int]:
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    index = pc.Index("stock-dashboard")
    embedder = get_embedder()

    vector = embedder.embed_query(query)
    results = index.query(
        vector=vector,
        top_k=5,
        namespace=ticker,
        include_metadata=True,
    )

    matches = getattr(results, "matches", None)
    if not matches:
        return "", 0

    chunks = []
    for m in matches:
        meta = m.get("metadata", {})
        text = meta.get("text", "")
        doc_type = meta.get("document_type", "")
        title = meta.get("title", "")
        chunks.append(f"[{doc_type}: {title}]\n{text}")

    return "\n\n".join(chunks), len(chunks)
