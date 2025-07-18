from sqlalchemy import Column, String, Integer, Boolean, Numeric, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .core import Base

class Player(Base):
    __tablename__ = "players"
    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_name = Column(String, nullable=False)
    heat        = Column(Integer, nullable=False)
    division    = Column(String)
    dropped_out = Column(Boolean, default=False)
    active      = Column(Boolean, default=True)

class AdvanceBet(Base):
    __tablename__ = "advance_bets"
    bet_id       = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bettor_email = Column(String, nullable=False)
    player_id    = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False)
    amount       = Column(Numeric(12,2), nullable=False)
    placed_at    = Column(TIMESTAMP(timezone=True))

# define WinBet, PropUniverse, PropBet analogously
