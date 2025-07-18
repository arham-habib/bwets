"""
Populate players & props with toy values so you can click around immediately.
Run:  `python -m scripts.populate_dummy`
Safe to run twice (UPSERT).
"""

import os, asyncio, csv, uuid, random
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DB = os.environ["DATABASE_URL"]

PLAYERS_CSV = "data/players.csv"          # optional – auto‑created if absent
PROPS_CSV   = "data/props.csv"

engine = create_async_engine(DB, echo=False, future=True)

async def run():
    async with engine.begin() as conn:
        # --- Players ---
        if not os.path.exists(PLAYERS_CSV):
            os.makedirs("data", exist_ok=True)
            with open(PLAYERS_CSV, "w", newline="") as f:
                w = csv.writer(f)
                for div in ("Open", "Women", "Silver"):
                    for heat in range(1,4):
                        for i in range(1,6):
                            w.writerow([f"Runner_{div}_{heat}_{i}", heat, div])
        with open(PLAYERS_CSV) as f:
            rows = [r for r in csv.reader(f)]
        await conn.execute(
            text("""
            insert into players (id, player_name, heat, division)
            select uuid_generate_v4(), :name, :heat, :division
            where not exists (
              select 1 from players where player_name = :name and heat = :heat and division = :division
            )
            """),
            [{"name": n, "heat": int(h), "division": d} for n,h,d in rows]
        )

        # --- Props ---
        default_props = ["Finishes under 18 min", "Photo finish (<0.5 s gap)",
                         "Someone drops baton", "Record broken"]
        if not os.path.exists(PROPS_CSV):
            os.makedirs("data", exist_ok=True)
            with open(PROPS_CSV, "w", newline="") as f:
                csv.writer(f).writerows([[p] for p in default_props])

        with open(PROPS_CSV) as f:
            props = [r[0] for r in csv.reader(f)]
        await conn.execute(
            text("""
            insert into prop_universe (id, prop_name)
            select uuid_generate_v4(), :prop
            where not exists (select 1 from prop_universe where prop_name = :prop)
            """),
            [{"prop": p} for p in props]
        )

    print("✅  Dummy data loaded.")

if __name__ == "__main__":
    asyncio.run(run())
