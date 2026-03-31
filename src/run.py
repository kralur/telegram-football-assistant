import asyncio
import os
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import uvicorn

from src.config.settings import WEBAPP_HOST, WEBAPP_PORT


def resolve_runtime():
    app_runtime = os.getenv("APP_RUNTIME", "").strip().lower()
    if app_runtime in {"web", "bot", "all"}:
        return app_runtime
    if os.getenv("PORT") or WEBAPP_PORT:
        return "web"
    return "bot"


def main():
    runtime = resolve_runtime()

    if runtime == "web":
        uvicorn.run("src.web.app:app", host=WEBAPP_HOST, port=WEBAPP_PORT, reload=False)
        return

    if runtime == "all":
        uvicorn.run("src.web.app:app", host=WEBAPP_HOST, port=WEBAPP_PORT, reload=False)
        return

    from src.app import main as bot_main

    asyncio.run(bot_main())


if __name__ == "__main__":
    main()
