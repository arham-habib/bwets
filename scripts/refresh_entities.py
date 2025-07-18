#!/usr/bin/env python3
"""
Refresh players & props from the CSVs WITHOUT touching bets.

▪ Creates the schema + DB file on first boot (so Fly volumes work)
▪ Adds new rows
▪ Sets .active = False for rows removed from the CSVs
"""

import os, csv, uuid, logging
from pathlib import Path
from dotenv import load_dotenv

from sqlalchemy import select, inspect, text, Connection
from app.models import SessionLocal, Player, PropUniverse, engine   # ← engine!

# ───── paths ──────────────────────────────────────────────────────
DATA_DIR      = "data"
PLAYERS_CSV   = os.path.join(DATA_DIR, "players.csv")
PROPS_CSV     = os.path.join(DATA_DIR, "props.csv")
SCHEMA_SQL    = "schema.sql"        # executed on first boot
DB_FILE       = Path(os.getenv("DATABASE_URL", "sqlite:///bwets.db")
                     .replace("sqlite:///", ""))   # e.g. /data/bwets.db

SCHEMA_SQL_TXT = Path(SCHEMA_SQL).read_text()
# ───── logging / env ──────────────────────────────────────────────
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

# ───── helpers to load the CSVs ───────────────────────────────────
def run_ddl(conn: Connection) -> None:
    """
    Execute schema.sql on the current connection.

    * SQLite → use raw driver .executescript() so we can run multiple
      statements in one go.
    * Postgres (or any other) → split on semicolons and run one‑by‑one.
    """
    if conn.dialect.name == "sqlite":
        # connection.driver_connection is the raw pysqlite connection
        conn.connection.executescript(SCHEMA_SQL_TXT)
    else:
        for stmt in filter(None, (s.strip() for s in SCHEMA_SQL_TXT.split(";"))):
            conn.exec_driver_sql(stmt)

def read_players():
    if not Path(PLAYERS_CSV).exists():
        return []
    with open(PLAYERS_CSV, newline="") as f:
        for row in csv.DictReader(f):
            yield row["player_name"], int(row["heat"]), row["division"]

def read_props():
    if not Path(PROPS_CSV).exists():
        return []
    with open(PROPS_CSV, newline="") as f:
        for (name,) in csv.reader(f):
            yield name.strip()

# ───── bootstrap DB if required ──────────────────────────────────
def ensure_schema():
    must_init = not DB_FILE.exists()
    if not must_init:
        # file exists – still check for tables (volume might be empty)
        with engine.begin() as conn:
            has_players = "players" in inspect(conn).get_table_names()
            must_init   = not has_players

    if must_init:
        logging.info("🏗️  Initialising empty DB at %s", DB_FILE)
        # make sure parent dir exists (important the very first time)
        DB_FILE.parent.mkdir(parents=True, exist_ok=True)
        with engine.begin() as conn:
            run_ddl(conn)

# ───── main refresh routine ───────────────────────────────────────
def main() -> None:
    ensure_schema()

    new_players = list(read_players())
    new_props   = list(read_props())

    with SessionLocal() as db:
        # ─── PLAYERS ───────────────────────────────────────────────
        db_players = db.execute(select(Player)).scalars().all()
        db_keyed = {(p.player_name, p.heat, p.division): p for p in db_players}

        for name, heat, div in new_players:
            key = (name, heat, div)
            if key in db_keyed:
                db_keyed[key].active = True
            else:
                db.add(Player(
                    player_name=name, heat=heat, division=div,
                    active=True, dropped_out=False
                ))

        new_set = set(new_players)
        for key, player in db_keyed.items():
            if key not in new_set:
                player.active = False

        # ─── PROPS ────────────────────────────────────────────────
        db_props = {p.prop_name: p for p in db.execute(select(PropUniverse)).scalars()}
        for prop in new_props:
            if prop in db_props:
                db_props[prop].active = True
            else:
                db.add(PropUniverse(prop_name=prop, active=True))

        for name, p in db_props.items():
            if name not in new_props:
                p.active = False

        db.commit()

    logging.info("🔄  Players & props refreshed ‑ bets untouched")

if __name__ == "__main__":
    main()
