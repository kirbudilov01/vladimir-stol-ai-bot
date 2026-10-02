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
- Telegram Payments integration point: invoice, pre-checkout, successful payment, credit accrual.
- Referral links for bloggers and media buyers.
- SQLite users/generations/referral tracking.
- Admin stats via `/admin`.
- Persistent user style selection in SQLite.
- File-size guardrail.
- Docker healthcheck.
- GitHub Actions CI.
- Docker and docker-compose deployment.
- Provider switch:
  - `mock` for local/demo mode without paid APIs.
  - `openai` for real image generation when `OPENAI_API_KEY` is configured.

External/live items not stored in the repo:

- Real Telegram bot token.
- Production hosting URL.
- Real payment provider token.
- Final prompt tuning after live image tests.

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

- Telegram Payments provider token: `PAYMENT_PROVIDER_TOKEN`.
- YooKassa, CloudPayments, Stripe, or another Telegram-supported provider.
- If `PAYMENT_PROVIDER_TOKEN` is empty, the bot keeps working and admins can issue credits manually with `/grant`.

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
PAYMENT_PROVIDER_TOKEN=
PAYMENT_CURRENCY=RUB
MAX_PHOTO_MB=15
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

## Payment Flow

1. User opens `Тарифы`.
2. User presses a buy button.
3. Bot sends a Telegram invoice.
4. Telegram sends pre-checkout.
5. After successful payment, bot stores the payment and adds credits.

If the provider token is missing, the user sees a clear message and no broken invoice is sent.

## Verification

Local syntax check:

```bash
python -m compileall app tests
```

Unit tests:

```bash
pytest -q
```

Docker healthcheck:

```bash
python -m app.healthcheck
```

CI runs compile and tests on every push through GitHub Actions.

## 100/100 Launch Checklist

The code is complete for handoff. To call the live product 100/100, complete these external steps:

1. Create a BotFather bot and set `BOT_TOKEN`.
2. Put your Telegram id into `ADMIN_IDS`.
3. Run in `mock` mode and check `/start`, `Стили`, `Баланс`, `Тарифы`, `/admin`.
4. Add `OPENAI_API_KEY`, set `GENERATION_PROVIDER=openai`, and test 20-30 real photos.
5. Tune prompts/styles if real results are weak.
6. Host `webapp/index.html` on HTTPS and set `PUBLIC_WEBAPP_URL`.
7. Connect payment provider and set `PAYMENT_PROVIDER_TOKEN`.
8. Make one test payment and confirm credits are added.
9. Run traffic only after image quality and payments are verified.

## Quality Notes

The bot is production-shaped, but final image quality depends on:

- prompt tuning on real photos;
- selected image model/provider;
- payment provider requirements;
- real traffic and abuse limits;
- hosting stability and backups.

For launch, start with `GENERATION_PROVIDER=mock` only for bot QA, then switch to `openai` and test 20-30 real generations before buying traffic.
