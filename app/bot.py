from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    BufferedInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from .config import Settings
from .db import Store
from .generator import ImageGenerator, STYLE_LABELS


PLANS = (
    "Тарифы\n\n"
    "1 генерация - 99 рублей\n"
    "3 генерации - 279 рублей\n"
    "5 генераций - 449 рублей\n"
    "10 генераций - 499 рублей\n"
    "Безлимит на месяц - 1490 рублей\n"
    "Безлимит навсегда - 9999 рублей\n\n"
    "Сейчас платежи не включены в код специально: после выбора провайдера подключается Telegram Payments/YooKassa/CloudPayments. "
    "До этого админ может выдавать кредиты командой /grant."
)

HELP = (
    "Как пользоваться\n\n"
    "1. Нажми Стили и выбери сценарий.\n"
    "2. Отправь свое фото или референс.\n"
    "3. Получи готовую картинку для сторис.\n\n"
    "Команды: /balance, /plans, /ref, /styles, /help."
)

STYLE_ALIASES = {
    "букет": "flowers",
    "flowers": "flowers",
    "flower": "flowers",
    "пара": "couple",
    "couple": "couple",
    "дубай": "dubai",
    "dubai": "dubai",
    "авто": "car",
    "машина": "car",
    "car": "car",
}

PLAN_CATALOG = {
    "one": {"title": "1 генерация", "credits": 1, "amount": 9900},
    "three": {"title": "3 генерации", "credits": 3, "amount": 27900},
    "five": {"title": "5 генераций", "credits": 5, "amount": 44900},
    "ten": {"title": "10 генераций", "credits": 10, "amount": 49900},
}


def main_keyboard(settings: Settings) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="Стили"), KeyboardButton(text="Баланс")],
        [KeyboardButton(text="Тарифы"), KeyboardButton(text="Рефералка")],
    ]
    if settings.public_webapp_url:
        rows.insert(0, [KeyboardButton(text="Открыть mini app", web_app=WebAppInfo(url=settings.public_webapp_url))])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, input_field_placeholder="Отправь фото для генерации")


def style_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Букет", callback_data="style:flowers"),
                InlineKeyboardButton(text="Пара", callback_data="style:couple"),
            ],
            [
                InlineKeyboardButton(text="Дубай", callback_data="style:dubai"),
                InlineKeyboardButton(text="Авто", callback_data="style:car"),
            ],
        ]
    )


def resolve_style(text: str | None, telegram_id: int) -> str:
    if text:
        first = text.strip().split()[0].lower()
        if first in STYLE_ALIASES:
            return STYLE_ALIASES[first]
    return "flowers"


def plan_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Купить 1", callback_data="buy:one"), InlineKeyboardButton(text="Купить 3", callback_data="buy:three")],
            [InlineKeyboardButton(text="Купить 5", callback_data="buy:five"), InlineKeyboardButton(text="Купить 10", callback_data="buy:ten")],
        ]
    )


async def register_handlers(dp: Dispatcher, bot: Bot, store: Store, generator: ImageGenerator, settings: Settings) -> None:
    storage_dir = Path("storage")
    storage_dir.mkdir(exist_ok=True)

    @dp.message(Command("start"))
    async def start(message: Message, command: CommandObject) -> None:
        referrer = int(command.args) if command.args and command.args.isdigit() else None
        store.ensure_user(message.from_user.id, message.from_user.username, referrer)
        await message.answer(
            "STOL AI\n\n"
            "Сделай реалистичное инфоповодное фото для сторис. Первая генерация бесплатная.\n\n"
            "Начни с кнопки Стили или просто отправь фото.",
            reply_markup=main_keyboard(settings),
        )

    @dp.message(Command("help"))
    @dp.message(F.text.casefold() == "помощь")
    async def help_message(message: Message) -> None:
        await message.answer(HELP, reply_markup=main_keyboard(settings))

    @dp.message(Command("styles"))
    @dp.message(F.text.casefold() == "стили")
    async def styles(message: Message) -> None:
        await message.answer("Выбери сценарий для следующей генерации.", reply_markup=style_keyboard())

    @dp.callback_query(F.data.startswith("style:"))
    async def style_callback(callback) -> None:
        style = callback.data.split(":", 1)[1]
        store.ensure_user(callback.from_user.id, callback.from_user.username)
        store.set_style(callback.from_user.id, style)
        await callback.answer(f"Выбран стиль: {STYLE_LABELS.get(style, style)}")
        await callback.message.answer(
            f"Стиль сохранен: {STYLE_LABELS.get(style, style)}. Теперь отправь фото.",
            reply_markup=main_keyboard(settings),
        )

    @dp.message(F.web_app_data)
    async def web_app_style(message: Message) -> None:
        try:
            payload = json.loads(message.web_app_data.data)
        except json.JSONDecodeError:
            await message.answer("Mini app прислал непонятные данные. Выбери стиль кнопкой Стили.")
            return
        style = payload.get("style")
        if style not in STYLE_LABELS:
            await message.answer("Такого стиля пока нет. Выбери один из готовых сценариев.")
            return
        store.ensure_user(message.from_user.id, message.from_user.username)
        store.set_style(message.from_user.id, style)
        await message.answer(f"Стиль из mini app сохранен: {STYLE_LABELS[style]}. Отправь фото.")

    @dp.message(Command("plans"))
    @dp.message(F.text.casefold() == "тарифы")
    async def plans(message: Message) -> None:
        store.ensure_user(message.from_user.id, message.from_user.username)
        await message.answer(PLANS, reply_markup=plan_keyboard())

    @dp.callback_query(F.data.startswith("buy:"))
    async def buy_callback(callback) -> None:
        store.ensure_user(callback.from_user.id, callback.from_user.username)
        plan_key = callback.data.split(":", 1)[1]
        plan = PLAN_CATALOG.get(plan_key)
        if plan is None:
            await callback.answer("Такого тарифа нет.", show_alert=True)
            return
        if not settings.payment_provider_token:
            await callback.answer("Платежи пока не подключены.", show_alert=True)
            await callback.message.answer("Платежный provider token не задан. Админ может выдать кредиты вручную командой /grant.")
            return
        payload = f"plan:{plan_key}:{callback.from_user.id}"
        await callback.message.answer_invoice(
            title=f"STOL AI: {plan['title']}",
            description=f"{plan['credits']} кредит(ов) для генерации фото",
            payload=payload,
            provider_token=settings.payment_provider_token,
            currency=settings.payment_currency,
            prices=[LabeledPrice(label=plan["title"], amount=plan["amount"])],
        )
        await callback.answer()

    @dp.pre_checkout_query()
    async def pre_checkout(pre_checkout_query: PreCheckoutQuery) -> None:
        payload = pre_checkout_query.invoice_payload
        parts = payload.split(":")
        ok = len(parts) == 3 and parts[0] == "plan" and parts[1] in PLAN_CATALOG
        await pre_checkout_query.answer(ok=ok, error_message=None if ok else "Неизвестный тариф.")

    @dp.message(F.successful_payment)
    async def successful_payment(message: Message) -> None:
        store.ensure_user(message.from_user.id, message.from_user.username)
        payment = message.successful_payment
        plan_key = payment.invoice_payload.split(":")[1]
        plan = PLAN_CATALOG[plan_key]
        store.save_payment(
            telegram_id=message.from_user.id,
            provider_charge_id=payment.provider_payment_charge_id,
            payload=payment.invoice_payload,
            amount=payment.total_amount,
            currency=payment.currency,
            credits=plan["credits"],
        )
        await message.answer(f"Оплата прошла. Начислено кредитов: {plan['credits']}.")

    @dp.message(Command("balance"))
    @dp.message(F.text.casefold() == "баланс")
    async def balance(message: Message) -> None:
        store.ensure_user(message.from_user.id, message.from_user.username)
        user = store.user(message.from_user.id)
        free_left = max(0, settings.free_generations - user["free_used"])
        style = STYLE_LABELS.get(store.selected_style(message.from_user.id), "Букет")
        await message.answer(f"Баланс: {user['credits']} кредитов.\nБесплатных генераций осталось: {free_left}.\nТекущий стиль: {style}.")

    @dp.message(Command("ref"))
    @dp.message(F.text.casefold() == "рефералка")
    async def ref(message: Message) -> None:
        me = await bot.get_me()
        await message.answer(
            "Реферальная ссылка для блогеров и трафферов:\n"
            f"https://t.me/{me.username}?start={message.from_user.id}\n\n"
            "Коммерческое правило: 50% от привлеченных оплат. Выплаты фиксируются после подключения платежей/CRM."
        )

    @dp.message(Command("admin"))
    async def admin(message: Message) -> None:
        if message.from_user.id not in settings.admins:
            await message.answer("Команда только для администратора.")
            return
        stats = store.stats()
        await message.answer(
            "Админ-панель\n\n"
            f"Пользователей: {stats['users']}\n"
            f"Генераций: {stats['generations']}\n"
            f"Реферальных входов: {stats['referrals']}\n\n"
            f"Оплат: {stats['payments']}\n\n"
            "Выдать кредиты: /grant <telegram_id> <credits>"
        )

    @dp.message(Command("grant"))
    async def grant(message: Message, command: CommandObject) -> None:
        if message.from_user.id not in settings.admins:
            await message.answer("Команда только для администратора.")
            return
        parts = (command.args or "").split()
        if len(parts) != 2 or not all(p.lstrip("-").isdigit() for p in parts):
            await message.answer("Формат: /grant <telegram_id> <credits>")
            return
        store.grant(int(parts[0]), int(parts[1]))
        await message.answer("Кредиты выданы.")

    @dp.message(F.photo)
    async def photo(message: Message) -> None:
        store.ensure_user(message.from_user.id, message.from_user.username)
        if not store.can_generate(message.from_user.id, settings.free_generations):
            await message.answer("Бесплатная генерация уже использована. Нажми Тарифы или напиши /plans.", reply_markup=main_keyboard(settings))
            return
        style = resolve_style(message.caption, message.from_user.id)
        if style == "flowers" and not (message.caption and message.caption.strip().split()[0].lower() in STYLE_ALIASES):
            style = store.selected_style(message.from_user.id)
        file_size = message.photo[-1].file_size or 0
        if file_size > settings.max_photo_mb * 1024 * 1024:
            await message.answer(f"Фото слишком тяжелое. Лимит: {settings.max_photo_mb} MB.")
            return
        await message.answer(f"Фото принято. Стиль: {STYLE_LABELS.get(style, style)}. Генерирую результат.")
        token = uuid4().hex
        input_path = storage_dir / f"{message.from_user.id}_{token}_input.jpg"
        output_path = storage_dir / f"{message.from_user.id}_{token}_output.jpg"
        await bot.download(message.photo[-1], destination=input_path)
        try:
            prompt = await generator.generate(input_path, output_path, style)
        except Exception as exc:
            await message.answer(
                "Генерация не прошла. Проверь ключи/провайдера в .env или попробуй другое фото.\n"
                f"Техническая причина: {type(exc).__name__}"
            )
            return
        store.charge_generation(message.from_user.id, settings.free_generations)
        store.save_generation(
            {
                "telegram_id": message.from_user.id,
                "style": style,
                "prompt": prompt,
                "input_path": str(input_path),
                "output_path": str(output_path),
            }
        )
        result = BufferedInputFile(output_path.read_bytes(), filename="stol-ai-result.jpg")
        await message.answer_photo(
            photo=result,
            caption="Готово. Можно отправить еще фото или выбрать другой стиль.",
            reply_markup=main_keyboard(settings),
        )

    @dp.message()
    async def fallback(message: Message) -> None:
        await message.answer("Я жду фото. Перед отправкой можно выбрать стиль кнопкой Стили.", reply_markup=main_keyboard(settings))
