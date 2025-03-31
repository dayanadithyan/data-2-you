from sqlalchemy import Column, Integer, String, Boolean, Text, Float, ForeignKey, create_engine, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func  # Added missing import for func
import json
from datetime import datetime

Base = declarative_base()

class DotaMatch(Base):
    """
    Maps to the existing table in the SQLite database.
    This class represents the core entity in our data model.
    """
    __tablename__ = 'dota_matches'  # Assuming the table is named dota_matches
    
    # Primary key and basic match data
    id = Column(Integer, primary_key=True)
    did_radiant_win = Column(Boolean, nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    start_date_time = Column(Integer, nullable=False)  # Unix timestamp
    end_date_time = Column(Integer, nullable=False)    # Unix timestamp
    
    # Structure statuses (encoded values)
    tower_status_radiant = Column(Integer, nullable=False)
    tower_status_dire = Column(Integer, nullable=False)
    barracks_status_radiant = Column(Integer, nullable=False)
    barracks_status_dire = Column(Integer, nullable=False)
    
    # Game events and settings
    first_blood_time = Column(Integer, nullable=True)
    lobby_type = Column(String, nullable=False)
    game_mode = Column(String, nullable=False)
    game_version_id = Column(Integer, nullable=False)
    
    # Time series data (stored as JSON strings)
    radiant_networth_leads = Column(Text, nullable=True)
    radiant_experience_leads = Column(Text, nullable=True)
    
    # Outcome and tournament data
    analysis_outcome = Column(String, nullable=True)
    league_id = Column(Integer, nullable=True)
    series_id = Column(Integer, nullable=True)
    
    # Team identifiers
    radiant_team_id = Column(Integer, nullable=True)
    dire_team_id = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<DotaMatch(id={self.id}, radiant_win={self.did_radiant_win})>"
    
    # Properties to access the related entities
    @property
    def radiant_team(self):
        """Virtual property for the radiant team"""
        from sqlalchemy.orm import Session
        session = Session.object_session(self)
        if session and self.radiant_team_id:
            return Team.get_or_create(session, self.radiant_team_id)
        return None
    
    @property
    def dire_team(self):
        """Virtual property for the dire team"""
        from sqlalchemy.orm import Session
        session = Session.object_session(self)
        if session and self.dire_team_id:
            return Team.get_or_create(session, self.dire_team_id)
        return None
    
    @property
    def league(self):
        """Virtual property for the league"""
        from sqlalchemy.orm import Session
        session = Session.object_session(self)
        if session and self.league_id:
            return League.get_or_create(session, self.league_id)
        return None
    
    @property
    def series(self):
        """Virtual property for the series"""
        from sqlalchemy.orm import Session
        session = Session.object_session(self)
        if session and self.series_id:
            return Series.get_or_create(session, self.series_id, self.league_id)
        return None
    
    # Time helper methods
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
            leads = eval(self.radiant_networth_leads)
            # Estimate time points (roughly every 60 seconds)
            return [(i * 60, value) for i, value in enumerate(leads) if i * 60 <= self.duration_seconds]
        except:
            return []
    
    def get_experience_leads(self):
        """Return experience leads as a list of (time_point, value) tuples"""
        if not self.radiant_experience_leads:
            return []
        
        try:
            leads = eval(self.radiant_experience_leads)
            # Estimate time points (roughly every 60 seconds)
            return [(i * 60, value) for i, value in enumerate(leads) if i * 60 <= self.duration_seconds]
        except:
            return []
    
    # Graph transformation methods
    def to_graph_nodes(self):
        """Convert this match to a dictionary of graph nodes"""
        nodes = {}
        
        # Match node
        nodes[f"match_{self.id}"] = {
            "type": "match",
            "id": self.id,
            "duration": self.duration_seconds,
            "start_time": self.start_datetime.isoformat(),
            "end_time": self.end_datetime.isoformat(),
            "analysis_outcome": self.analysis_outcome,
            "first_blood_time": self.first_blood_time,
            "lobby_type": self.lobby_type,
            "game_mode": self.game_mode,
            "game_version_id": self.game_version_id
        }
        
        # Add team nodes if they exist
        if self.radiant_team_id:
            nodes[f"team_{self.radiant_team_id}"] = {
                "type": "team",
                "id": self.radiant_team_id
            }
        
        if self.dire_team_id:
            nodes[f"team_{self.dire_team_id}"] = {
                "type": "team",
                "id": self.dire_team_id
            }
        
        # Add league node if it exists
        if self.league_id:
            nodes[f"league_{self.league_id}"] = {
                "type": "league",
                "id": self.league_id
            }
        
        # Add series node if it exists
        if self.series_id:
            nodes[f"series_{self.series_id}"] = {
                "type": "series",
                "id": self.series_id
            }
        
        return nodes
    
    def to_graph_edges(self):
        """Convert this match to a dictionary of graph edges"""
        edges = []
        
        # Team participation edges
        if self.radiant_team_id:
            # Extract tower and barracks status for edge attributes
            radiant_towers = self.decode_tower_status(is_radiant=True)
            radiant_barracks = self.decode_barracks_status(is_radiant=True)
            
            edges.append({
                "source": f"team_{self.radiant_team_id}",
                "target": f"match_{self.id}",
                "relationship": "PARTICIPATED_IN",
                "side": "radiant",
                "result": "won" if self.did_radiant_win else "lost",
                "tower_status": radiant_towers,
                "barracks_status": radiant_barracks
            })
        
        if self.dire_team_id:
            # Extract tower and barracks status for edge attributes
            dire_towers = self.decode_tower_status(is_radiant=False)
            dire_barracks = self.decode_barracks_status(is_radiant=False)
            
            edges.append({
                "source": f"team_{self.dire_team_id}",
                "target": f"match_{self.id}",
                "relationship": "PARTICIPATED_IN",
                "side": "dire",
                "result": "lost" if self.did_radiant_win else "won",
                "tower_status": dire_towers,
                "barracks_status": dire_barracks
            })
        
        # Match to series edge
        if self.series_id:
            edges.append({
                "source": f"match_{self.id}",
                "target": f"series_{self.series_id}",
                "relationship": "PART_OF"
            })
        
        # Series to league edge
        if self.series_id and self.league_id:
            edges.append({
                "source": f"series_{self.series_id}",
                "target": f"league_{self.league_id}",
                "relationship": "PART_OF"
            })
        
        return edges


# These classes don't map to tables but provide a consistent API to access related entities
class Team:
    """
    Virtual entity for teams.
    In a graph structure, this would be a primary node type.
    """
    def __init__(self, id, name=None):
        self.id = id
        self.name = name
    
    def __repr__(self):
        return f"<Team(id={self.id}, name={self.name or 'Unknown'})>"
    
    @classmethod
    def get_or_create(cls, session, team_id):
        """Get a team instance (doesn't persist to DB)"""
        if not team_id:
            return None
        return cls(id=team_id)
    
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


class League:
    """
    Virtual entity for leagues.
    In a graph structure, this would be a primary node type.
    """
    def __init__(self, id, name=None):
        self.id = id
        self.name = name
    
    def __repr__(self):
        return f"<League(id={self.id}, name={self.name or 'Unknown'})>"
    
    @classmethod
    def get_or_create(cls, session, league_id):
        """Get a league instance (doesn't persist to DB)"""
        if not league_id:
            return None
        return cls(id=league_id)
    
    def get_series(self, session):
        """Get all series in this league"""
        matches = session.query(DotaMatch).filter(DotaMatch.league_id == self.id).all()
        series_ids = set(match.series_id for match in matches if match.series_id)
        
        return [Series(series_id, self.id) for series_id in series_ids]
    
    def get_matches(self, session):
        """Get all matches in this league"""
        return session.query(DotaMatch).filter(DotaMatch.league_id == self.id).all()


class Series:
    """
    Virtual entity for series.
    In a graph structure, this would be a node connecting League and Match nodes.
    """
    def __init__(self, id, league_id=None):
        self.id = id
        self.league_id = league_id
    
    def __repr__(self):
        return f"<Series(id={self.id}, league_id={self.league_id})>"
    
    @classmethod
    def get_or_create(cls, session, series_id, league_id=None):
        """Get a series instance (doesn't persist to DB)"""
        if not series_id:
            return None
        return cls(id=series_id, league_id=league_id)
    
    def get_matches(self, session):
        """Get all matches in this series"""
        return session.query(DotaMatch).filter(DotaMatch.series_id == self.id).all()
    
    @property
    def league(self):
        """Get the league for this series"""
        if not self.league_id:
            return None
        return League(self.league_id)


# Database connection and utility functions
def connect_to_db(db_path):
    """Connect to the existing SQLite database"""
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    return Session()

def export_to_graph(session, graph_format='networkx'):
    """
    Export the database to a graph structure
    Supports formats: 'networkx', 'igraph', 'graphml', 'dict'
    """
    if graph_format == 'dict':
        # Simple dictionary representation
        nodes = {}
        edges = []
        
        # Collect all matches
        matches = session.query(DotaMatch).all()
        
        # Process each match
        for match in matches:
            # Add nodes from this match
            nodes.update(match.to_graph_nodes())
            
            # Add edges from this match
            edges.extend(match.to_graph_edges())
        
        return {
            'nodes': nodes,
            'edges': edges
        }
    
    elif graph_format == 'networkx':
        import networkx as nx
        G = nx.DiGraph()
        
        # Get dictionary representation
        graph_dict = export_to_graph(session, 'dict')
        
        # Add nodes
        for node_id, attrs in graph_dict['nodes'].items():
            G.add_node(node_id, **attrs)
        
        # Add edges
        for edge in graph_dict['edges']:
            source = edge.pop('source')
            target = edge.pop('target')
            G.add_edge(source, target, **edge)
        
        return G
    
    elif graph_format == 'igraph':
        import igraph as ig
        
        # Get dictionary representation
        graph_dict = export_to_graph(session, 'dict')
        
        g = ig.Graph(directed=True)
        
        # Add vertices
        for node_id, attrs in graph_dict['nodes'].items():
            g.add_vertex(name=node_id, **attrs)
        
        # Add edges
        for edge in graph_dict['edges']:
            g.add_edge(edge['source'], edge['target'], **{k: v for k, v in edge.items() if k not in ('source', 'target')})
        
        return g
    
    elif graph_format == 'graphml':
        import networkx as nx
        G = export_to_graph(session, 'networkx')
        return nx.write_graphml(G, "dota_matches.graphml")
    
    else:
        raise ValueError(f"Unsupported graph format: {graph_format}")

def analyze_match_outcomes(session):
    """Analyze match outcomes by team, league, etc."""
    results = {
        'total_matches': session.query(DotaMatch).count(),
        'radiant_wins': session.query(DotaMatch).filter(DotaMatch.did_radiant_win == True).count(),
        'dire_wins': session.query(DotaMatch).filter(DotaMatch.did_radiant_win == False).count(),
        'analysis_outcomes': {},
        'avg_duration': session.query(DotaMatch).with_entities(
            func.avg(DotaMatch.duration_seconds).label('avg_duration')
        ).scalar() / 60.0,  # in minutes
        'teams': {},
        'leagues': {}
    }
    
    # Count analysis outcomes
    for outcome in session.query(DotaMatch.analysis_outcome).distinct():
        if outcome[0]:
            count = session.query(DotaMatch).filter(DotaMatch.analysis_outcome == outcome[0]).count()
            results['analysis_outcomes'][outcome[0]] = count
    
    # Get unique team IDs
    team_ids = set()
    for radiant_id, dire_id in session.query(DotaMatch.radiant_team_id, DotaMatch.dire_team_id).all():
        if radiant_id:
            team_ids.add(radiant_id)
        if dire_id:
            team_ids.add(dire_id)
    
    # Analyze teams
    for team_id in team_ids:
        team = Team(team_id)
        results['teams'][team_id] = {
            'win_rate': team.win_rate(session),
            'matches': len(team.get_matches(session))
        }
    
    # Get unique league IDs
    league_ids = set([l_id[0] for l_id in session.query(DotaMatch.league_id).distinct() if l_id[0]])
    
    # Analyze leagues
    for league_id in league_ids:
        league = League(league_id)
        league_matches = league.get_matches(session)
        results['leagues'][league_id] = {
            'matches': len(league_matches),
            'series': len(set([m.series_id for m in league_matches if m.series_id]))
        }
    
    return results