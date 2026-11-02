"""Small DB-API adapter with cross-process, per-budget PostgreSQL locks."""
import hashlib
import sqlite3

GLOBAL_LOCK = 2710312601


class LedgerConnection:
    def __init__(self, target, mandate_id=None):
        self.postgres = target.startswith(("postgresql://", "postgres://"))
        self.mandate_id = mandate_id
        if self.postgres:
            import psycopg
            try:
                self.connection = psycopg.connect(target, autocommit=True, connect_timeout=10)
            except psycopg.Error:
                raise RuntimeError("PostgreSQL connection failed. Check the private DATABASE_URL and server availability.") from None
        else:
            self.connection = sqlite3.connect(target, timeout=60)
            self.connection.execute("PRAGMA busy_timeout=60000")
        try:
            self.begin()
        except Exception:
            self.connection.close()
            raise

    def begin(self):
        if not self.postgres:
            self.connection.execute("BEGIN IMMEDIATE")
            return
        self.connection.execute("BEGIN")
        self.connection.execute("SET LOCAL lock_timeout = '10s'")
        if self.mandate_id is None:
            self.connection.execute("SELECT pg_advisory_xact_lock(%s)", (GLOBAL_LOCK,))
        else:
            self.connection.execute("SELECT pg_advisory_xact_lock_shared(%s)", (GLOBAL_LOCK,))
            key = int.from_bytes(hashlib.sha256(self.mandate_id.encode()).digest()[:8], "big", signed=True)
            self.connection.execute("SELECT pg_advisory_xact_lock(%s)", (key,))

    def execute(self, sql, params=()):
        if sql == "BEGIN IMMEDIATE":
            self.begin()
            return None
        return self.connection.execute(sql.replace("?", "%s") if self.postgres else sql, params)

    def executescript(self, sql):
        if self.postgres:
            sql = sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY")
        for statement in sql.split(";"):
            if statement.strip():
                self.execute(statement)

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def close(self):
        self.connection.close()
