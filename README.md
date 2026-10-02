# STOL AI Telegram Bot

Telegram bot + mini app shell for viral "event photo" generations. The product flow is simple: user chooses a scenario, sends a photo, receives a finished image, and can share a referral link.

## Current Product State

This repo is ready to run as a working MVP after you add real secrets to `.env`.

Implemented:

- Telegram onboarding and persistent keyboard.
- Style selection in Telegram and in the mini app.
- Photo upload flow with clear status/error messages.
- One free generation per user.
- Credit balance and admin credit grants.
- Referral links for bloggers and media buyers.
- SQLite users/generations/referral tracking.
- Admin stats via `/admin`.
- Docker and docker-compose deployment.
- Provider switch:
  - `mock` for local/demo mode without paid APIs.
  - `openai` for real image generation when `OPENAI_API_KEY` is configured.

Not included yet by design:

- Real Telegram bot token.
- Production hosting URL.
- Real payment provider integration.
- Final commercial prompts after live image tests.

## External Services Needed

Required:

- Telegram BotFather bot token: `BOT_TOKEN`.
- A server/VPS or any Docker host.

Required for real AI output:

- OpenAI API key: `OPENAI_API_KEY`.
- Set `GENERATION_PROVIDER=openai`.

Optional for mini app:

- Public HTTPS hosting for `webapp/index.html`.
- Add that URL to `PUBLIC_WEBAPP_URL`.
- Configure the domain in BotFather if Telegram asks for it.

Optional for payments:

- Telegram Payments provider token, YooKassa, CloudPayments, Stripe, or another provider.
- The repo currently supports manual credit grants with `/grant`; payment callbacks should be added after the provider is chosen.

## Quick Start

```bash
cp .env.example .env
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

Production:

```bash
docker compose up -d --build
```

## Environment

```bash
BOT_TOKEN=123456:telegram-bot-token
ADMIN_IDS=123456789
DATABASE_PATH=./data/stol_ai.sqlite3
PUBLIC_WEBAPP_URL=
GENERATION_PROVIDER=mock
OPENAI_API_KEY=
OPENAI_IMAGE_MODEL=gpt-image-1
FREE_GENERATIONS=1
```

## User Flow

1. User opens `/start`.
2. User taps `Стили` or opens mini app.
3. User selects `Букет`, `Пара`, `Дубай`, or `Авто`.
4. User sends a photo.
5. Bot sends the generated result.
6. User can check `Баланс`, open `Тарифы`, or copy `Рефералка`.

## Admin Flow

- `/admin` shows users, generations, referral starts.
- `/grant <telegram_id> <credits>` adds paid credits manually.
- `.env` `ADMIN_IDS` controls who can use admin commands.

## Quality Notes

The bot is production-shaped, but final image quality depends on:

- prompt tuning on real photos;
- selected image model/provider;
- payment provider requirements;
- real traffic and abuse limits;
- hosting stability and backups.

For launch, start with `GENERATION_PROVIDER=mock` only for bot QA, then switch to `openai` and test 20-30 real generations before buying traffic.
