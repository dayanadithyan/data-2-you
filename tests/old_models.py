from datetime import datetime
import json
from sqlalchemy import Column, Integer, Boolean, String, Text, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, Session

Base = declarative_base()

class DotaMatch(Base):
    """
    Represents a Dota 2 match with its properties and relationships.
    """
    __tablename__ = 'dota_matches'
    
    # Primary key and basic match data
    id = Column(Integer, primary_key=True)
    did_radiant_win = Column(Boolean, nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    start_date_time = Column(Integer, nullable=False)  # Unix timestamp
    end_date_time = Column(Integer, nullable=False)    # Unix timestamp
    
    # Structure statuses
    tower_status_radiant = Column(Integer, nullable=False)
    tower_status_dire = Column(Integer, nullable=False)
    barracks_status_radiant = Column(Integer, nullable=False)
    barracks_status_dire = Column(Integer, nullable=False)
    
    # Game events and settings
    first_blood_time = Column(Integer, nullable=True)
    lobby_type = Column(String(50), nullable=False)
    game_mode = Column(String(50), nullable=False)
    game_version_id = Column(Integer, nullable=False)
    
    # Time series data (stored as JSON strings)
    radiant_networth_leads = Column(Text, nullable=True)
    radiant_experience_leads = Column(Text, nullable=True)
    
    # Outcome and tournament data
    analysis_outcome = Column(String(100), nullable=True)
    
    # Foreign keys for relationships
    league_id = Column(Integer, ForeignKey('leagues.id'), nullable=True)
    series_id = Column(Integer, ForeignKey('series.id'), nullable=True)
    radiant_team_id = Column(Integer, ForeignKey('teams.id'), nullable=True)
    dire_team_id = Column(Integer, ForeignKey('teams.id'), nullable=True)
    
    # Relationships
    league = relationship("League", back_populates="matches")
    series = relationship("Series", back_populates="matches")
    radiant_team = relationship("Team", foreign_keys=[radiant_team_id], back_populates="radiant_matches")
    dire_team = relationship("Team", foreign_keys=[dire_team_id], back_populates="dire_matches")
    
    def __repr__(self):
        return f"<DotaMatch(id={self.id}, radiant_win={self.did_radiant_win})>"
    
    # Time helper properties
    @property
    def start_datetime(self):
        """Convert Unix timestamp to datetime"""
        return datetime.fromtimestamp(self.start_date_time)
    
    @property
    def end_datetime(self):
        """Convert Unix timestamp to datetime"""
        return datetime.fromtimestamp(self.end_date_time)
    
    @property
    def duration_minutes(self):
        """Return duration in minutes"""
        return self.duration_seconds / 60.0
    
    # Structure status decoder methods
    def decode_tower_status(self, is_radiant=True):
        """Decode tower status into individual tower states"""
        status_value = self.tower_status_radiant if is_radiant else self.tower_status_dire
        
        towers = {
            'tier1_bot': bool(status_value & 1),
            'tier2_bot': bool(status_value & (1 << 1)),
            'tier3_bot': bool(status_value & (1 << 2)),
            'tier1_mid': bool(status_value & (1 << 3)),
            'tier2_mid': bool(status_value & (1 << 4)),
            'tier3_mid': bool(status_value & (1 << 5)),
            'tier1_top': bool(status_value & (1 << 6)),
            'tier2_top': bool(status_value & (1 << 7)),
            'tier3_top': bool(status_value & (1 << 8)),
            'tier4_1': bool(status_value & (1 << 9)),
            'tier4_2': bool(status_value & (1 << 10))
        }
        return towers
    
    def decode_barracks_status(self, is_radiant=True):
        """Decode barracks status into individual barracks states"""
        status_value = self.barracks_status_radiant if is_radiant else self.barracks_status_dire
        
        barracks = {
            'bot_ranged': bool(status_value & 1),
            'bot_melee': bool(status_value & (1 << 1)),
            'mid_ranged': bool(status_value & (1 << 2)),
            'mid_melee': bool(status_value & (1 << 3)),
            'top_ranged': bool(status_value & (1 << 4)),
            'top_melee': bool(status_value & (1 << 5))
        }
        return barracks
    
    # Time series data methods
    def get_networth_leads(self):
        """Return networth leads as a list of (time_point, value) tuples"""
        if not self.radiant_networth_leads:
            return []
        
        try:
            leads = json.loads(self.radiant_networth_leads)
            # Estimate time points (roughly every 60 seconds)
            return [(i * 60, value) for i, value in enumerate(leads) if i * 60 <= self.duration_seconds]
        except Exception as e:
            return []
    
    def get_experience_leads(self):
        """Return experience leads as a list of (time_point, value) tuples"""
        if not self.radiant_experience_leads:
            return []
        
        try:
            leads = json.loads(self.radiant_experience_leads)
            # Estimate time points (roughly every 60 seconds)
            return [(i * 60, value) for i, value in enumerate(leads) if i * 60 <= self.duration_seconds]
        except Exception as e:
            return []


class Team(Base):
    """
    Represents a Dota 2 team.
    """
    __tablename__ = 'teams'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=True)
    
    # Relationships
    radiant_matches = relationship("DotaMatch", foreign_keys=[DotaMatch.radiant_team_id], back_populates="radiant_team")
    dire_matches = relationship("DotaMatch", foreign_keys=[DotaMatch.dire_team_id], back_populates="dire_team")
    
    def __repr__(self):
        return f"<Team(id={self.id}, name={self.name or 'Unknown'})>"
    
    def get_matches(self, session):
        """Get all matches for this team"""
        return session.query(DotaMatch).filter(
            (DotaMatch.radiant_team_id == self.id) | (DotaMatch.dire_team_id == self.id)
        ).all()
    
    def win_rate(self, session):
        """Calculate team's win rate"""
        radiant_matches = session.query(DotaMatch).filter(DotaMatch.radiant_team_id == self.id).all()
        dire_matches = session.query(DotaMatch).filter(DotaMatch.dire_team_id == self.id).all()
        
        total_matches = len(radiant_matches) + len(dire_matches)
        if total_matches == 0:
            return 0
        
        wins = 0
        for match in radiant_matches:
            if match.did_radiant_win:
                wins += 1
        
        for match in dire_matches:
            if not match.did_radiant_win:
                wins += 1
        
        return wins / total_matches


class League(Base):
    """
    Represents a Dota 2 league or tournament.
    """
    __tablename__ = 'leagues'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=True)
    
    # Relationships
    matches = relationship("DotaMatch", back_populates="league")
    series = relationship("Series", back_populates="league")
    
    def __repr__(self):
        return f"<League(id={self.id}, name={self.name or 'Unknown'})>"
    
    def get_matches(self, session):
        """Get all matches in this league"""
        return session.query(DotaMatch).filter(DotaMatch.league_id == self.id).all()


class Series(Base):
    """
    Represents a series of matches within a league.
    """
    __tablename__ = 'series'
    
    id = Column(Integer, primary_key=True)
    league_id = Column(Integer, ForeignKey('leagues.id'), nullable=True)
    
    # Relationships
    league = relationship("League", back_populates="series")
    matches = relationship("DotaMatch", back_populates="series")
    
    def __repr__(self):
        return f"<Series(id={self.id}, league_id={self.league_id})>"
    
    def get_matches(self, session):
        """Get all matches in this series"""
        return session.query(DotaMatch).filter(DotaMatch.series_id == self.id).all()