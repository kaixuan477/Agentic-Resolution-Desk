"""CLI: seed the pgvector policy corpus.

Usage:
    python -m scripts.seed_policies

Requires a reachable ``DATABASE_URL`` and a valid ``GOOGLE_API_KEY`` (for
embeddings). Safe to re-run — rows are upserted.
"""

from __future__ import annotations

import sys

from src.config import get_settings
from src.rag.ingest import ingest_policies


def main() -> int:
    settings = get_settings()
    print(f"Seeding policy corpus into: {settings.database_url}")
    try:
        count = ingest_policies(settings.database_url)
    except Exception as exc:  # noqa: BLE001 - CLI boundary: surface a clean message
        print(f"Seeding failed: {exc}", file=sys.stderr)
        return 1
    print(f"Ingested {count} policy documents.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
