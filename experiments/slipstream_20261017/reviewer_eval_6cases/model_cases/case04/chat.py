import sqlite3
from contextlib import closing
from typing import Protocol

class Model(Protocol):
    async def generate(self, prompt: str) -> str: ...

class ChatJournal:
    def __init__(self, database: str, model: Model):
        self.database = database
        self.model = model
        with closing(sqlite3.connect(database)) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS turns (session TEXT, role TEXT, body TEXT)")
            conn.commit()

    async def chat(self, session: str, prompt: str) -> str:
        with closing(sqlite3.connect(self.database, timeout=0.05)) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                conn.execute("INSERT INTO turns VALUES (?, ?, ?)", (session, "user", prompt))
                answer = await self.model.generate(prompt)
                conn.execute("INSERT INTO turns VALUES (?, ?, ?)", (session, "assistant", answer))
                conn.commit()
                return answer
            except BaseException:
                conn.rollback()
                raise
