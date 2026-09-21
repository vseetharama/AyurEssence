from __future__ import annotations

from sqlalchemy import text

from app.database.session import engine


def init_db() -> None:
    with engine.begin() as conn:
        conn.execute(text("SELECT 1"))
