from sqlalchemy import select, func
from .models import PropBet
import os

# keep everything in float arithmetic
HOUSE = float(os.getenv("HOUSE_TAKE", "0.03"))   # 3 % rake ⇒ 0.03

def pool_odds(session, BetModel, group_field):
    """
    Return a dict {target_id: implied_probability} for a parimutuel pool
    after applying the HOUSE rake.
    """
    total = session.scalar(select(func.sum(BetModel.amount))) or 0.0
    total *= (1.0 - HOUSE)

    odds = {}
    if total <= 0:
        return odds

    for id_, stake in session.execute(
        select(group_field, func.sum(BetModel.amount)).group_by(group_field)
    ):
        prob = (stake * (1.0 - HOUSE)) / total
        odds[str(id_)] = {
            "prob": round(float(prob), 4),
            "stake": round(float(stake), 2),
        }

    return odds

def prop_odds(session):
    """
    Returns nested dict {prop_id: {'yes': {prob, stake},
                                   'no':  {...}}}
    """
    total_yes = session.scalar(
        select(func.sum(PropBet.amount)).where(PropBet.side_yes.is_(True))
    ) or 0.0

    total_no = session.scalar(
        select(func.sum(PropBet.amount)).where(PropBet.side_yes.is_(False))
    ) or 0.0
    odds = {}
    for prop_id, side_yes, stake in session.execute(
        select(PropBet.prop_id,
               PropBet.side_yes,
               func.sum(PropBet.amount))
        .group_by(PropBet.prop_id, PropBet.side_yes)
    ):
        side = "yes" if side_yes else "no"
        odds.setdefault(str(prop_id), {}).setdefault(side, {})
        total = (total_yes if side_yes else total_no) * (1 - HOUSE)
        prob = ((stake * (1 - HOUSE)) / total) if total else 0
        odds[str(prop_id)][side] = {"stake": float(stake), "prob": round(prob,4)}
    return odds