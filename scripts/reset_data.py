"""Truncate all Postgres tables and clear the Pinecone index.

Wipes mda, financials, embedded, chat_history in Postgres and every
namespace in the Pinecone index. Next uvicorn start will re-embed
everything from scratch. Requires DATABASE_URL and PINECONE_API_KEY.
"""
import os
import sys

from dotenv import load_dotenv
from pinecone import Pinecone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from utils.db import reset_all
from data.embeddings import INDEX_NAME


def reset_postgres() -> None:
    reset_all()
    print("[reset] truncated Postgres tables: mda, financials, embedded, chat_history")


def reset_pinecone() -> None:
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    if INDEX_NAME not in [i.name for i in pc.list_indexes()]:
        print(f"[reset] Pinecone index '{INDEX_NAME}' does not exist, skipping")
        return

    index = pc.Index(INDEX_NAME)
    stats = index.describe_index_stats()
    namespaces = list(stats.namespaces.keys())
    if not namespaces:
        print("[reset] Pinecone index has no namespaces, nothing to clear")
        return

    for ns in namespaces:
        index.delete(delete_all=True, namespace=ns)
    print(f"[reset] cleared Pinecone namespaces: {', '.join(namespaces)}")


if __name__ == "__main__":
    confirm = input(
        "This will TRUNCATE all Postgres tables (mda, financials, embedded, "
        "chat_history) and clear the entire Pinecone index. Type 'yes' to continue: "
    )
    if confirm.strip().lower() != "yes":
        print("Aborted.")
        sys.exit(0)

    reset_postgres()
    reset_pinecone()
    print("[reset] done")
