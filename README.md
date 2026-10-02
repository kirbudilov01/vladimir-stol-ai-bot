# STOL AI Telegram Bot

Telegram bot + mini app shell for viral "event photo" generations: choose a style, upload a selfie/reference photo, receive a generated image, and share a referral link.

## What is included

- Telegram bot with `/start`, `/plans`, `/balance`, `/ref`, `/help`.
- One free generation per user.
- SQLite user/generation/referral tracking.
- Admin `/grant <telegram_id> <credits>` command.
- Dark neon mini app page served from `webapp/index.html`.
- Pluggable generation provider:
  - `mock` works locally without paid APIs.
  - `openai` uses the OpenAI Images API when `OPENAI_API_KEY` is set.
- Docker and docker-compose setup.

## Quick start

```bash
cp .env.example .env
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

For production:

```bash
docker compose up -d --build
```

## Environment

Create `.env` from `.env.example`.

- `BOT_TOKEN` is required.
- `ADMIN_IDS` is a comma-separated list of Telegram user ids.
- `GENERATION_PROVIDER=mock` for local demo.
- `GENERATION_PROVIDER=openai` and `OPENAI_API_KEY=...` for real image generation.
- `PUBLIC_WEBAPP_URL` should point to the hosted `/webapp/index.html` URL if you want the Telegram mini app button.

## Notes for launch

The bot intentionally does not store tokens in code. Add a real bot token, deploy to a VPS, set `PUBLIC_WEBAPP_URL`, and run `docker compose up -d --build`.

