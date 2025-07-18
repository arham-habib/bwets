import os, uuid, datetime as dt
from sqlalchemy import Column, String, Integer, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.dialects.sqlite import BLOB as UUID  # ok for SQLite
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(DATABASE_URL, future=True, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)

Base = declarative_base()



class Player(Base):
    __tablename__ = "players"
    id = Column(String, primary_key=True,
                default=lambda: str(uuid.uuid4()))
    player_name = Column(String, nullable=False)
    heat = Column(Integer, nullable=False)
    division = Column(String, nullable=False)
    dropped_out = Column(Boolean, default=False)
    active = Column(Boolean, default=True)

class PropUniverse(Base):
    __tablename__ = "prop_universe"
    id        = Column(String, primary_key=True,
                       default=lambda: str(uuid.uuid4())) 
    prop_name = Column(String, unique=True, nullable=False)
    active    = Column(Boolean, default=True)


class AdvanceBet(Base):
    __tablename__ = "advance_bets"
    bet_id        = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    player_id     = Column(String, ForeignKey("players.id"), nullable=False)
    bettor_email  = Column(String, nullable=False)          
    amount        = Column(Float,  nullable=False)
    placed_at     = Column(DateTime, default=datetime.utcnow)

class WinBet(Base):
    __tablename__ = "win_bets"
    bet_id        = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    player_id     = Column(String, ForeignKey("players.id"), nullable=False)
    bettor_email  = Column(String, nullable=False)      
    amount        = Column(Float,  nullable=False)
    placed_at     = Column(DateTime, default=datetime.utcnow)

class PropBet(Base):
    __tablename__ = "prop_bets"
    bet_id        = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    prop_id       = Column(String, ForeignKey("prop_universe.id"), nullable=False)
    side_yes      = Column(Boolean, nullable=False)
    bettor_email  = Column(String, nullable=False)         
    amount        = Column(Float,  nullable=False)
    placed_at     = Column(DateTime, default=datetime.utcnow)

