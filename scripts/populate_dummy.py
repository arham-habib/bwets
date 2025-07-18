#!/usr/bin/env python3
"""
Seed ./data/bwets.db from players.csv and props.csv.

If the CSV files don’t exist we generate toy data so you can click around
immediately.  The script:

1. Reads DATABASE_URL from .env (SQLite by default)
2. Executes schema.sql (re‑creates all tables)
3. Inserts player + prop rows
"""

import os
import uuid
import logging
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
from string import ascii_uppercase


# ─────────────────────────  setup  ──────────────────────────
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

DB_URL = os.getenv("DATABASE_URL", "sqlite:///data/bwets.db")
DATA_DIR = "data"
PLAYERS_CSV = os.path.join(DATA_DIR, "players.csv")
PROPS_CSV = os.path.join(DATA_DIR, "props.csv")
SCHEMA_SQL = "schema.sql"

os.makedirs(DATA_DIR, exist_ok=True)
engine = create_engine(DB_URL, future=True, echo=False)

# ─────────────── default CSVs (if user hasn’t provided) ───────────────
if not os.path.exists(PLAYERS_CSV):
    divisions = ["Open", "Women", "Masters"]          # 3 divisions
    heats_per_div = 5                                 # 5 heats each
    players_per_heat = 6                              # 6 runners per heat

    # generator for player names: A, B, … Z, AA, AB, …
    def name_gen():
        i = 0
        while True:
            q, r = divmod(i, 26)
            yield (ascii_uppercase[r] if q == 0
                   else ascii_uppercase[q-1] + ascii_uppercase[r])
            i += 1

    names = name_gen()
    rows = []
    for div in divisions:
        for heat in range(1, heats_per_div + 1):
            for _ in range(players_per_heat):
                rows.append([next(names), heat, div])

    pd.DataFrame(rows, columns=["player_name", "heat", "division"]).to_csv(
        PLAYERS_CSV, index=False
    )
    logging.info("Created default %s wish %d players", PLAYERS_CSV, len(rows))

if not os.path.exists(PROPS_CSV):
    pd.Series(
        ["Record broken", "Photo finish (<0.5 s)", "Equities winner"]
    ).to_csv(PROPS_CSV, index=False, header=False)
    logging.info("Created default %s", PROPS_CSV)


# ───────────────── load CSVs → DataFrames ──────────────────────────────
players = pd.read_csv(PLAYERS_CSV)
players["id"] = [str(uuid.uuid4()) for _ in range(len(players))]
players["dropped_out"] = False
players["active"] = True

props = pd.read_csv(PROPS_CSV, header=None, names=["prop_name"])
props["id"] = [str(uuid.uuid4()) for _ in range(len(props))]
props["active"] = True

# ───────── If SQLite, wipe the file so schema always recreates ────────
if engine.dialect.name == "sqlite":
    db_path = engine.url.database            # e.g. data/bwets.db
    if os.path.exists(db_path):
        os.remove(db_path)
        logging.info("Removed existing %s", db_path)

# ───────────────── exec schema & insert rows ───────────────────────────
with engine.begin() as conn:
    # executescript lets us run multiple statements in SQLite
    raw_conn = conn.connection
    raw_conn.executescript(open(SCHEMA_SQL).read())

    players.to_sql("players", conn, if_exists="append", index=False)
    props.to_sql("prop_universe", conn, if_exists="append", index=False)

logging.info("✅  Seeded DB with %d players, %d props", len(players), len(props))
