from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    ForeignKey, Enum as SAEnum, UniqueConstraint
)
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class Stage(str, enum.Enum):
    GROUP = "GROUP"
    R32 = "R32"          # Oitavas-de-final (Round of 32)
    R16 = "R16"          # Oitavas-de-final (Round of 16)
    QF = "QF"            # Quartas-de-final
    SF = "SF"            # Semifinal
    THIRD = "THIRD"      # Disputa 3º lugar
    FINAL = "FINAL"      # Final


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    bets = relationship("Bet", back_populates="user")
    special_bet = relationship("SpecialBet", back_populates="user", uselist=False)


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    flag = Column(String(10), nullable=False)  # emoji de bandeira
    confederation = Column(String(20), nullable=False)  # UEFA, CONMEBOL, etc.

    group_teams = relationship("GroupTeam", back_populates="team")


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(5), nullable=False)  # A, B, C ... L

    group_teams = relationship("GroupTeam", back_populates="group")
    matches = relationship("Match", back_populates="group")


class GroupTeam(Base):
    __tablename__ = "group_teams"
    __table_args__ = (UniqueConstraint("group_id", "team_id", name="uq_group_team"),)

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    position = Column(Integer, default=0)  # Posição final no grupo

    group = relationship("Group", back_populates="group_teams")
    team = relationship("Team", back_populates="group_teams")


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    match_number = Column(Integer, nullable=False, unique=True)
    stage = Column(SAEnum(Stage), nullable=False, default=Stage.GROUP)
    home_team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    away_team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    match_date = Column(DateTime, nullable=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    is_finished = Column(Boolean, default=False)
    label = Column(String(100), nullable=True)  # ex: "1A vs 2B" para mata-mata

    home_team = relationship("Team", foreign_keys=[home_team_id])
    away_team = relationship("Team", foreign_keys=[away_team_id])
    group = relationship("Group", back_populates="matches")
    bets = relationship("Bet", back_populates="match")


class Bet(Base):
    __tablename__ = "bets"
    __table_args__ = (UniqueConstraint("user_id", "match_id", name="uq_bet_user_match"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    home_score = Column(Integer, nullable=False)
    away_score = Column(Integer, nullable=False)
    points = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="bets")
    match = relationship("Match", back_populates="bets")


class SpecialBet(Base):
    __tablename__ = "special_bets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    champion_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    runner_up_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    third_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    fourth_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    points = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="special_bet")
    champion = relationship("Team", foreign_keys=[champion_id])
    runner_up = relationship("Team", foreign_keys=[runner_up_id])
    third = relationship("Team", foreign_keys=[third_id])
    fourth = relationship("Team", foreign_keys=[fourth_id])
