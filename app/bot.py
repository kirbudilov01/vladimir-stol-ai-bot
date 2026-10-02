from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject
from aiogram.types import BufferedInputFile, KeyboardButton, Message, ReplyKeyboardMarkup, WebAppInfo

from .config import Settings
from .db import Store
from .generator import ImageGenerator


PLANS = (
    "Тарифы:\n"
    "1 генерация - 99 рублей\n"
    "3 генерации - 279 рублей\n"
    "5 генераций - 449 рублей\n"
    "10 генераций - 499 рублей\n"
    "Безлимит на месяц - 1490 рублей\n"
    "Безлимит навсегда - 9999 рублей\n\n"
    "Первая генерация бесплатная. Оплату можно подключить через Telegram Payments или выдавать кредиты командой /grant."
)


def keyboard(settings: Settings) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text="Сгенерировать фото")], [KeyboardButton(text="Тарифы"), KeyboardButton(text="Рефералка")]]
    if settings.public_webapp_url:
        rows.insert(0, [KeyboardButton(text="Открыть mini app", web_app=WebAppInfo(url=settings.public_webapp_url))])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


async def register_handlers(dp: Dispatcher, bot: Bot, store: Store, generator: ImageGenerator, settings: Settings) -> None:
    storage_dir = Path("storage")
    storage_dir.mkdir(exist_ok=True)

    @dp.message(Command("start"))
    async def start(message: Message, command: CommandObject) -> None:
        referrer = int(command.args) if command.args and command.args.isdigit() else None
        store.ensure_user(message.from_user.id, message.from_user.username, referrer)
        await message.answer(
            "STOL AI: сделай реалистичное инфоповодное фото для сторис.\n\n"
            "Отправь фото и в подписи укажи стиль: flowers, couple, dubai или car.",
            reply_markup=keyboard(settings),
        )

    @dp.message(Command("plans"))
    @dp.message(F.text.casefold() == "тарифы")
    async def plans(message: Message) -> None:
        store.ensure_user(message.from_user.id, message.from_user.username)
        await message.answer(PLANS)

    @dp.message(Command("balance"))
    async def balance(message: Message) -> None:
        store.ensure_user(message.from_user.id, message.from_user.username)
        user = store.user(message.from_user.id)
        free_left = max(0, settings.free_generations - user["free_used"])
        await message.answer(f"Баланс: {user['credits']} кредитов. Бесплатных генераций осталось: {free_left}.")

    @dp.message(Command("ref"))
    @dp.message(F.text.casefold() == "рефералка")
    async def ref(message: Message) -> None:
        me = await bot.get_me()
        await message.answer(
            "Реферальная ссылка для блогеров и трафферов:\n"
            f"https://t.me/{me.username}?start={message.from_user.id}\n\n"
            "Коммерческое правило: 50% от привлечённых оплат ведём в CRM/таблице при подключении платежей."
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
            await message.answer("Бесплатная генерация уже использована. Напиши /plans, чтобы пополнить баланс.")
            return
        style = (message.caption or "flowers").strip().split()[0].lower()
        await message.answer("Принял фото. Генерирую, обычно это занимает до минуты.")
        token = uuid4().hex
        input_path = storage_dir / f"{message.from_user.id}_{token}_input.jpg"
        output_path = storage_dir / f"{message.from_user.id}_{token}_output.jpg"
        await bot.download(message.photo[-1], destination=input_path)
        prompt = await generator.generate(input_path, output_path, style)
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
        await message.answer_photo(photo=result, caption="Готово. Можно сделать ещё стиль: flowers, couple, dubai, car.")

    @dp.message()
    async def fallback(message: Message) -> None:
        await message.answer("Отправь фото с подписью-стилем: flowers, couple, dubai или car.", reply_markup=keyboard(settings))
