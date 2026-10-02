from __future__ import annotations

from pathlib import Path

from .config import get_settings
from .db import Store


def main() -> None:
    settings = get_settings()
    if not settings.bot_token or ":" not in settings.bot_token:
        raise SystemExit("BOT_TOKEN is missing or malformed")
    Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)
    Store(settings.database_path)
    if settings.generation_provider == "openai" and not settings.openai_api_key:
        raise SystemExit("OPENAI_API_KEY is required when GENERATION_PROVIDER=openai")
    print("ok")


if __name__ == "__main__":
    main()
