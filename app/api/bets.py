from fastapi import APIRouter, Depends, Request
from sqlalchemy import select, func
from sqlalchemy.exc import NoResultFound
from ..core import get_db, require_user
from ..models import Player, AdvanceBet
import uuid, decimal, os

router = APIRouter(prefix="/bets", tags=["bets"])
HOUSE_TAKE = decimal.Decimal(os.getenv("HOUSE_TAKE", "0.03"))

@router.post("/advance/{player_id}")
async def make_advance_bet(player_id: uuid.UUID, amount: decimal.Decimal,
                           req: Request, db=Depends(get_db)):
    user = require_user(req)
    bet = AdvanceBet(bettor_email=user, player_id=player_id, amount=amount)
    db.add(bet)
    await db.commit()
    return {"bet_id": bet.bet_id}

@router.get("/advance/pool/{heat}")
async def advance_pool(heat: int, db=Depends(get_db)):
    q = select(func.sum(AdvanceBet.amount)).join(Player).where(Player.heat==heat)
    pool, = (await db.execute(q)).one()
    pool = pool or decimal.Decimal("0")
    return {"net_pool": pool * (1 - HOUSE_TAKE)}
