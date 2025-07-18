from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid, logging
from .models import SessionLocal, Player, AdvanceBet, WinBet, PropBet, PropUniverse
from .odds import pool_odds

api = FastAPI()
log = logging.getLogger("uvicorn.error")


class BetIn(BaseModel):
    target_id: uuid.UUID
    amount: float
    market: str  # "advance" | "win" | "prop"
    side_yes: bool | None = None  # for prop


@api.post("/bet")
def place_bet(bet: BetIn):
    with SessionLocal() as db:
        if bet.market == "advance":
            db.add(AdvanceBet(player_id=bet.target_id, amount=bet.amount))
        elif bet.market == "win":
            db.add(WinBet(player_id=bet.target_id, amount=bet.amount))
        elif bet.market == "prop":
            db.add(PropBet(prop_id=bet.target_id, amount=bet.amount, side_yes=bet.side_yes))
        else:
            raise HTTPException(400, "unknown market")
        db.commit()
    log.info("BET %s %s %s", bet.market, bet.target_id, bet.amount)
    return {"status": "ok"}


@api.get("/odds/{market}")
def odds(market: str):
    with SessionLocal() as db:
        if market == "advance":
            return pool_odds(db, AdvanceBet, AdvanceBet.player_id)
        if market == "win":
            return pool_odds(db, WinBet, WinBet.player_id)
        if market == "prop":
            return pool_odds(db, PropBet, PropBet.prop_id)
    raise HTTPException(404)
