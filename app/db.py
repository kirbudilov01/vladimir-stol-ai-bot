from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class Store:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self.connect() as db:
            db.executescript(
                """
                create table if not exists users (
                    telegram_id integer primary key,
                    username text,
                    referrer_id integer,
                    free_used integer not null default 0,
                    credits integer not null default 0,
                    created_at text not null default current_timestamp
                );
                create table if not exists generations (
                    id integer primary key autoincrement,
                    telegram_id integer not null,
                    style text not null,
                    prompt text not null,
                    input_path text not null,
                    output_path text not null,
                    created_at text not null default current_timestamp
                );
                """
            )

    def ensure_user(self, telegram_id: int, username: str | None, referrer_id: int | None = None) -> None:
        with self.connect() as db:
            db.execute(
                """
                insert into users (telegram_id, username, referrer_id)
                values (?, ?, ?)
                on conflict(telegram_id) do update set username=excluded.username
                """,
                (telegram_id, username, referrer_id if referrer_id != telegram_id else None),
            )

    def user(self, telegram_id: int) -> sqlite3.Row:
        with self.connect() as db:
            row = db.execute("select * from users where telegram_id=?", (telegram_id,)).fetchone()
        if row is None:
            raise KeyError(telegram_id)
        return row

    def can_generate(self, telegram_id: int, free_generations: int) -> bool:
        user = self.user(telegram_id)
        return user["credits"] > 0 or user["free_used"] < free_generations

    def charge_generation(self, telegram_id: int, free_generations: int) -> str:
        with self.connect() as db:
            user = db.execute("select * from users where telegram_id=?", (telegram_id,)).fetchone()
            if user["credits"] > 0:
                db.execute("update users set credits=credits-1 where telegram_id=?", (telegram_id,))
                return "credit"
            if user["free_used"] < free_generations:
                db.execute("update users set free_used=free_used+1 where telegram_id=?", (telegram_id,))
                return "free"
        raise RuntimeError("No generations available")

    def grant(self, telegram_id: int, credits: int) -> None:
        with self.connect() as db:
            db.execute(
                "insert into users (telegram_id, credits) values (?, ?) "
                "on conflict(telegram_id) do update set credits=credits+excluded.credits",
                (telegram_id, credits),
            )

    def save_generation(self, data: dict[str, Any]) -> None:
        with self.connect() as db:
            db.execute(
                "insert into generations (telegram_id, style, prompt, input_path, output_path) values (?, ?, ?, ?, ?)",
                (data["telegram_id"], data["style"], data["prompt"], data["input_path"], data["output_path"]),
            )

