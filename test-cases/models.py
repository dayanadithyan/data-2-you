from typing import List, Optional
import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class GorpMigrations(Base):
    __tablename__ = 'gorp_migrations'

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    applied_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    def __repr__(self):
        return f"<GorpMigrations(id={self.id!r}, applied_at={self.applied_at!r})>"


class Heroes(Base):
    __tablename__ = 'heroes'

    display_name: Mapped[str] = mapped_column(Text)
    short_name: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True)

    match_pick_bans: Mapped[List['MatchPickBans']] = relationship('MatchPickBans', back_populates='hero')
    match_players: Mapped[List['MatchPlayers']] = relationship('MatchPlayers', back_populates='hero')

    def __repr__(self):
        return f"<Heroes(id={self.id}, display_name={self.display_name!r}, short_name={self.short_name!r})>"


class Items(Base):
    __tablename__ = 'items'

    display_name: Mapped[str] = mapped_column(Text)
    short_name: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True)

    match_players: Mapped[List['MatchPlayers']] = relationship(
        'MatchPlayers',
        foreign_keys='[MatchPlayers.backpack_0_id]',
        back_populates='backpack_0'
    )
    match_players_: Mapped[List['MatchPlayers']] = relationship(
        'MatchPlayers',
        foreign_keys='[MatchPlayers.backpack_1_id]',
        back_populates='backpack_1'
    )
    # Fix here: back_populates now refers to the attribute on MatchPlayers named 'backpack_2'
    match_players1: Mapped[List['MatchPlayers']] = relationship(
        'MatchPlayers',
        foreign_keys='[MatchPlayers.backpack_2_id]',
        back_populates='backpack_2'
    )
    match_players2: Mapped[List['MatchPlayers']] = relationship(
        'MatchPlayers',
        foreign_keys='[MatchPlayers.item_0_id]',
        back_populates='item_0'
    )
    match_players3: Mapped[List['MatchPlayers']] = relationship(
        'MatchPlayers',
        foreign_keys='[MatchPlayers.item_1_id]',
        back_populates='item_1'
    )
    match_players4: Mapped[List['MatchPlayers']] = relationship(
        'MatchPlayers',
        foreign_keys='[MatchPlayers.item_2_id]',
        back_populates='item_2'
    )
    match_players5: Mapped[List['MatchPlayers']] = relationship(
        'MatchPlayers',
        foreign_keys='[MatchPlayers.item_3_id]',
        back_populates='item_3'
    )
    match_players6: Mapped[List['MatchPlayers']] = relationship(
        'MatchPlayers',
        foreign_keys='[MatchPlayers.item_4_id]',
        back_populates='item_4'
    )
    match_players7: Mapped[List['MatchPlayers']] = relationship(
        'MatchPlayers',
        foreign_keys='[MatchPlayers.item_5_id]',
        back_populates='item_5'
    )
    match_players8: Mapped[List['MatchPlayers']] = relationship(
        'MatchPlayers',
        foreign_keys='[MatchPlayers.neutral_0_id]',
        back_populates='neutral_0'
    )

    def __repr__(self):
        return f"<Items(id={self.id}, display_name={self.display_name!r}, short_name={self.short_name!r})>"


class Leagues(Base):
    __tablename__ = 'leagues'

    name: Mapped[str] = mapped_column(Text)
    id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True)

    matches: Mapped[List['Matches']] = relationship('Matches', back_populates='league')

    def __repr__(self):
        return f"<Leagues(id={self.id}, name={self.name!r})>"


class TeamPlayers(Base):
    __tablename__ = 'team_players'

    name: Mapped[str] = mapped_column(Text)
    steam_account_id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True)

    match_players: Mapped[List['MatchPlayers']] = relationship('MatchPlayers', back_populates='steam_account')

    def __repr__(self):
        return f"<TeamPlayers(steam_account_id={self.steam_account_id}, name={self.name!r})>"


class Teams(Base):
    __tablename__ = 'teams'

    name: Mapped[str] = mapped_column(Text)
    tag: Mapped[str] = mapped_column(Text)
    id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True)

    series: Mapped[List['Series']] = relationship(
        'Series',
        foreign_keys='[Series.team_one_id]',
        back_populates='team_one'
    )
    series_: Mapped[List['Series']] = relationship(
        'Series',
        foreign_keys='[Series.team_two_id]',
        back_populates='team_two'
    )
    series1: Mapped[List['Series']] = relationship(
        'Series',
        foreign_keys='[Series.winning_team_id]',
        back_populates='winning_team'
    )
    matches: Mapped[List['Matches']] = relationship(
        'Matches',
        foreign_keys='[Matches.dire_team_id]',
        back_populates='dire_team'
    )
    matches_: Mapped[List['Matches']] = relationship(
        'Matches',
        foreign_keys='[Matches.radiant_team_id]',
        back_populates='radiant_team'
    )

    def __repr__(self):
        return f"<Teams(id={self.id}, name={self.name!r}, tag={self.tag!r})>"


class Series(Base):
    __tablename__ = 'series'

    type: Mapped[str] = mapped_column(Text)
    team_one_win_count: Mapped[int] = mapped_column(Integer)
    team_two_win_count: Mapped[int] = mapped_column(Integer)
    team_one_id: Mapped[int] = mapped_column(ForeignKey('teams.id'))
    team_two_id: Mapped[int] = mapped_column(ForeignKey('teams.id'))
    id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True)
    winning_team_id: Mapped[Optional[int]] = mapped_column(ForeignKey('teams.id'))

    team_one: Mapped['Teams'] = relationship('Teams', foreign_keys=[team_one_id], back_populates='series')
    team_two: Mapped['Teams'] = relationship('Teams', foreign_keys=[team_two_id], back_populates='series_')
    winning_team: Mapped[Optional['Teams']] = relationship('Teams', foreign_keys=[winning_team_id], back_populates='series1')
    matches: Mapped[List['Matches']] = relationship('Matches', back_populates='series')

    def __repr__(self):
        return (f"<Series(id={self.id}, type={self.type!r}, "
                f"team_one_win_count={self.team_one_win_count}, team_two_win_count={self.team_two_win_count}, "
                f"winning_team_id={self.winning_team_id})>")


class Matches(Base):
    __tablename__ = 'matches'

    did_radiant_win: Mapped[int] = mapped_column(Integer)
    duration_seconds: Mapped[int] = mapped_column(Integer)
    start_date_time: Mapped[int] = mapped_column(Integer)
    end_date_time: Mapped[int] = mapped_column(Integer)
    tower_status_radiant: Mapped[int] = mapped_column(Integer)
    tower_status_dire: Mapped[int] = mapped_column(Integer)
    barracks_status_radiant: Mapped[int] = mapped_column(Integer)
    barracks_status_dire: Mapped[int] = mapped_column(Integer)
    first_blood_time: Mapped[int] = mapped_column(Integer)
    lobby_type: Mapped[str] = mapped_column(Text)
    game_mode: Mapped[str] = mapped_column(Text)
    game_version_id: Mapped[int] = mapped_column(Integer)
    radiant_networth_leads: Mapped[str] = mapped_column(Text)
    radiant_experience_leads: Mapped[str] = mapped_column(Text)
    analysis_outcome: Mapped[str] = mapped_column(Text)
    league_id: Mapped[int] = mapped_column(ForeignKey('leagues.id'))
    series_id: Mapped[int] = mapped_column(ForeignKey('series.id'))
    radiant_team_id: Mapped[int] = mapped_column(ForeignKey('teams.id'))
    dire_team_id: Mapped[int] = mapped_column(ForeignKey('teams.id'))
    id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True)

    dire_team: Mapped['Teams'] = relationship('Teams', foreign_keys=[dire_team_id], back_populates='matches')
    league: Mapped['Leagues'] = relationship('Leagues', back_populates='matches')
    radiant_team: Mapped['Teams'] = relationship('Teams', foreign_keys=[radiant_team_id], back_populates='matches_')
    series: Mapped['Series'] = relationship('Series', back_populates='matches')
    match_pick_bans: Mapped[List['MatchPickBans']] = relationship('MatchPickBans', back_populates='match')
    match_players: Mapped[List['MatchPlayers']] = relationship('MatchPlayers', back_populates='match')

    def __repr__(self):
        return (f"<Matches(id={self.id}, did_radiant_win={self.did_radiant_win}, "
                f"duration_seconds={self.duration_seconds}, start_date_time={self.start_date_time})>")


class MatchPickBans(Base):
    __tablename__ = 'match_pick_bans'

    is_pick: Mapped[int] = mapped_column(Integer)
    pick_order: Mapped[int] = mapped_column(Integer)
    is_radiant: Mapped[int] = mapped_column(Integer)
    match_id: Mapped[int] = mapped_column(ForeignKey('matches.id'), primary_key=True)
    hero_id: Mapped[int] = mapped_column(ForeignKey('heroes.id'), primary_key=True)

    hero: Mapped['Heroes'] = relationship('Heroes', back_populates='match_pick_bans')
    match: Mapped['Matches'] = relationship('Matches', back_populates='match_pick_bans')

    def __repr__(self):
        return (f"<MatchPickBans(match_id={self.match_id}, hero_id={self.hero_id}, "
                f"is_pick={self.is_pick}, pick_order={self.pick_order}, is_radiant={self.is_radiant})>")


class MatchPlayers(Base):
    __tablename__ = 'match_players'

    is_radiant: Mapped[int] = mapped_column(Integer)
    is_victory: Mapped[int] = mapped_column(Integer)
    kills: Mapped[int] = mapped_column(Integer)
    deaths: Mapped[int] = mapped_column(Integer)
    assists: Mapped[int] = mapped_column(Integer)
    num_last_hits: Mapped[int] = mapped_column(Integer)
    num_denies: Mapped[int] = mapped_column(Integer)
    gold_per_min: Mapped[int] = mapped_column(Integer)
    networth: Mapped[int] = mapped_column(Integer)
    exp_per_min: Mapped[int] = mapped_column(Integer)
    level: Mapped[int] = mapped_column(Integer)
    gold_spent: Mapped[int] = mapped_column(Integer)
    hero_damage: Mapped[int] = mapped_column(Integer)
    tower_damage: Mapped[int] = mapped_column(Integer)
    hero_healing: Mapped[int] = mapped_column(Integer)
    is_random: Mapped[int] = mapped_column(Integer)
    lane: Mapped[str] = mapped_column(Text)
    position: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(Text)
    invisible_seconds: Mapped[int] = mapped_column(Integer)
    match_id: Mapped[int] = mapped_column(ForeignKey('matches.id'), primary_key=True)
    steam_account_id: Mapped[str] = mapped_column(ForeignKey('team_players.steam_account_id'), primary_key=True)
    hero_id: Mapped[int] = mapped_column(ForeignKey('heroes.id'))
    dota_plus_hero_level: Mapped[Optional[int]] = mapped_column(Integer)
    item_0_id: Mapped[Optional[int]] = mapped_column(ForeignKey('items.id'))
    item_1_id: Mapped[Optional[int]] = mapped_column(ForeignKey('items.id'))
    item_2_id: Mapped[Optional[int]] = mapped_column(ForeignKey('items.id'))
    item_3_id: Mapped[Optional[int]] = mapped_column(ForeignKey('items.id'))
    item_4_id: Mapped[Optional[int]] = mapped_column(ForeignKey('items.id'))
    item_5_id: Mapped[Optional[int]] = mapped_column(ForeignKey('items.id'))
    backpack_0_id: Mapped[Optional[int]] = mapped_column(ForeignKey('items.id'))
    backpack_1_id: Mapped[Optional[int]] = mapped_column(ForeignKey('items.id'))
    backpack_2_id: Mapped[Optional[int]] = mapped_column(ForeignKey('items.id'))
    neutral_0_id: Mapped[Optional[int]] = mapped_column(ForeignKey('items.id'))

    backpack_0: Mapped[Optional['Items']] = relationship(
        'Items', foreign_keys=[backpack_0_id], back_populates='match_players'
    )
    backpack_1: Mapped[Optional['Items']] = relationship(
        'Items', foreign_keys=[backpack_1_id], back_populates='match_players_'
    )
    backpack_2: Mapped[Optional['Items']] = relationship(
        'Items', foreign_keys=[backpack_2_id], back_populates='match_players1'
    )
    hero: Mapped['Heroes'] = relationship('Heroes', back_populates='match_players')
    item_0: Mapped[Optional['Items']] = relationship(
        'Items', foreign_keys=[item_0_id], back_populates='match_players2'
    )
    item_1: Mapped[Optional['Items']] = relationship(
        'Items', foreign_keys=[item_1_id], back_populates='match_players3'
    )
    item_2: Mapped[Optional['Items']] = relationship(
        'Items', foreign_keys=[item_2_id], back_populates='match_players4'
    )
    item_3: Mapped[Optional['Items']] = relationship(
        'Items', foreign_keys=[item_3_id], back_populates='match_players5'
    )
    item_4: Mapped[Optional['Items']] = relationship(
        'Items', foreign_keys=[item_4_id], back_populates='match_players6'
    )
    item_5: Mapped[Optional['Items']] = relationship(
        'Items', foreign_keys=[item_5_id], back_populates='match_players7'
    )
    match: Mapped['Matches'] = relationship('Matches', back_populates='match_players')
    neutral_0: Mapped[Optional['Items']] = relationship(
        'Items', foreign_keys=[neutral_0_id], back_populates='match_players8'
    )
    steam_account: Mapped['TeamPlayers'] = relationship('TeamPlayers', back_populates='match_players')

    def __repr__(self):
        return (f"<MatchPlayers(match_id={self.match_id}, steam_account_id={self.steam_account_id!r}, "
                f"kills={self.kills}, deaths={self.deaths}, assists={self.assists}, "
                f"gold_per_min={self.gold_per_min}, level={self.level})>")
