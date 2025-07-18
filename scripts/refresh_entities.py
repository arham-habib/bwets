#!/usr/bin/env python3
"""
Refresh players & props from the current CSV files WITHOUT touching bets.

▪ Adds new rows
▪ Sets .active = False for rows that disappeared from the CSV
▪ Leaves existing bets and odds untouched
"""

import os, csv, uuid, logging
from dotenv import load_dotenv
from sqlalchemy import select
from app.models import SessionLocal, Player, PropUniverse

DATA_DIR   = "data"
PLAYERS_CSV = os.path.join(DATA_DIR, "players.csv")
PROPS_CSV   = os.path.join(DATA_DIR, "props.csv")

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

def read_players():
    with open(PLAYERS_CSV, newline="") as f:
        for row in csv.DictReader(f):
            yield row["player_name"], int(row["heat"]), row["division"]

def read_props():
    with open(PROPS_CSV, newline="") as f:
        for name, in csv.reader(f):
            yield name.strip()

def main():
    new_players = list(read_players())
    new_props   = list(read_props())

    with SessionLocal() as db:
        # --- Players --------------------------------------------
        db_players = db.execute(select(Player)).scalars().all()
        db_keyed = {(p.player_name, p.heat, p.division): p for p in db_players}

        # add or reactivate
        for name, heat, div in new_players:
            key = (name, heat, div)
            if key in db_keyed:
                db_keyed[key].active = True
            else:
                db.add(Player(
                    id=str(uuid.uuid4()),
                    player_name=name, heat=heat, division=div,
                    active=True, dropped_out=False
                ))

        # mark missing players inactive
        new_set = set(new_players)
        for key, player in db_keyed.items():
            if key not in new_set:
                player.active = False

        # --- Props ----------------------------------------------
        db_props = {p.prop_name: p for p in db.execute(select(PropUniverse)).scalars()}
        for prop in new_props:
            if prop in db_props:
                db_props[prop].active = True
            else:
                db.add(PropUniverse(id=str(uuid.uuid4()), prop_name=prop, active=True))

        # mark removed props inactive
        for name, p in db_props.items():
            if name not in new_props:
                p.active = False

        db.commit()

    logging.info("🔄  Players & props refreshed without touching bets")

if __name__ == "__main__":
    main()
