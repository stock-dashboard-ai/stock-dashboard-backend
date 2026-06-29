import json
from pathlib import Path

CACHE_DIR = Path(__file__).parent.parent / "cache"


def get_cache(key: str) -> dict | None:
    path = CACHE_DIR / f"{key}.json"
    if path.exists():
        return json.loads(path.read_text())
    return None


def set_cache(key: str, data: dict) -> None:
    CACHE_DIR.mkdir(exist_ok=True)
    path = CACHE_DIR / f"{key}.json"
    path.write_text(json.dumps(data, default=str))
