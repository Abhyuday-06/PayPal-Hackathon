"""Preserve a SQLite ledger when moving to an empty PostgreSQL database.

The source is opened read-only. Destination schemas must have no project data;
the automatically seeded empty mandate is the only overwrite permitted.
"""
import argparse
import json
import os
from pathlib import Path
import sqlite3
import time
from urllib.parse import quote
from dotenv import load_dotenv
from .gateway import Gateway
from .payments import SimulatedPayments

TABLES = ["mandates", "proposals", "events", "webhook_events", "jobs"]


def migrate(source_path, target_url):
    if not target_url.startswith(("postgresql://", "postgres://")):
        raise ValueError("The destination must be PostgreSQL.")
    source = Path(source_path).resolve()
    if not source.is_file():
        raise ValueError("The source ledger does not exist.")
    source_db = sqlite3.connect("file:" + quote(source.as_posix(), safe="/:") + "?mode=ro", uri=True)
    try:
        data = {table: source_db.execute("SELECT * FROM " + table).fetchall() for table in TABLES}
    finally:
        source_db.close()
    if any(json.loads(row[1])["state"] in ("queued", "running") for row in data["jobs"]):
        raise ValueError("Complete background jobs and stop the API before migrating.")
    if any(json.loads(row[2]).get("lease_until", 0) > time.time() for row in data["proposals"]):
        raise ValueError("A payment operation is still active. Do not migrate during external execution.")
    target = Gateway(target_url, SimulatedPayments())
    with target.tx() as db:
        for table in ["proposals", "webhook_events", "jobs"]:
            if db.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]:
                raise ValueError("Destination has project data; use an empty database.")
        mandates = db.execute("SELECT id FROM mandates").fetchall()
        if len(mandates) != 1 or mandates[0][0] != "mandate-studio":
            raise ValueError("Destination contains custom budgets; use an empty database.")
        events = db.execute("SELECT data FROM events").fetchall()
        if len(events) > 1 or any(json.loads(row[0])["kind"] != "mandate_created" for row in events):
            raise ValueError("Destination has audit history; use an empty database.")
        for table in TABLES:
            db.execute("DELETE FROM " + table)
            for row in data[table]:
                if table == "events":
                    db.execute("INSERT INTO events(data) VALUES (?)", (row[1],))
                else:
                    db.execute("INSERT INTO " + table + " VALUES (" + ",".join("?" for _ in row) + ")", row)
    return {table: len(rows) for table, rows in data.items()}


if __name__ == "__main__":
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    parser = argparse.ArgumentParser()
    parser.add_argument("--sqlite", required=True)
    args = parser.parse_args()
    print(migrate(args.sqlite, os.environ["DATABASE_URL"]))
