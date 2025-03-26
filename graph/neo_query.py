import os
import logging
from typing import List, Optional
from datetime import datetime

import strawberry
import neo4j
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from dotenv import load_dotenv

# Import native schema types
from schema.schema import (
    HeroMetaSnapshot, 
    PositionMetrics, 
    HeroItemBuild, 
    ItemSynergy, 
    SkillPriority
)

class STRATZ_Neo4j_Importer:
    """
    Neo4j Importer using native schema types
    
    Design Principles:
    - Leverage existing schema definitions
    - Maintain data integrity
    - Provide flexible import mechanisms
    """
    
    def __init__(self, 
                 stratz_api_key: str, 
                 neo4j_uri: str, 
                 neo4j_user: str, 
                 neo4j_password: str):
        """
        Initialize STRATZ API and Neo4j connections
        
        Args:
            stratz_api_key (str): STRATZ GraphQL API key
            neo4j_uri (str): Neo4j database connection URI
            neo4j_user (str): Neo4j username
            neo4j_password (str): Neo4j password
        """
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # GraphQL Client Setup
        transport = RequestsHTTPTransport(
            url='https://api.stratz.com/graphql',
            headers={
                'Authorization': f'Bearer {stratz_api_key}',
                'Content-Type': 'application/json'
            }
        )
        self.stratz_client = Client(transport=transport, fetch_schema_from_transport=True)
        
        # Neo4j Driver Setup
        self.neo4j_driver = neo4j.GraphDatabase.driver(
            neo4j_uri, 
            auth=(neo4j_user, neo4j_password)
        )

    def fetch_hero_meta_timeline(
        self, 
        hero_id: int, 
        resolution: str = 'PATCH'
    ) -> List[HeroMetaSnapshot]:
        """
        Fetch hero meta timeline using native schema types
        
        Args:
            hero_id (int): Hero identifier
            resolution (str): Time resolution (DAILY, WEEKLY, PATCH)
        
        Returns:
            List of HeroMetaSnapshot instances
        """
        query = gql('''
        query HeroMetaTimeline($heroId: ID!, $resolution: TimeResolution) {
            heroMetaTimeline(heroId: $heroId, resolution: $resolution) {
                timestamp
                patchVersion
                overallWinRate
                positions {
                    position
                    pickRate
                    winRate
                    goldPerMin
                    expPerMin
                }
                itemBuilds {
                    itemId
                    winRate
                    purchaseTiming
                    matches
                    synergyItems {
                        itemId
                        synergyScore
                    }
                }
                skillPriorities {
                    abilityId
                    priorityScore
                }
            }
        }
        ''')
        
        params = {
            'heroId': hero_id,
            'resolution': resolution
        }
        
        try:
            result = self.stratz_client.execute(query, variable_values=params)
            
            # Transform API result to native schema types
            meta_snapshots = []
            for snapshot_data in result['heroMetaTimeline']:
                # Transform positions
                positions = [
                    PositionMetrics(
                        position=pos['position'],
                        pick_rate=pos['pickRate'],
                        win_rate=pos['winRate'],
                        gold_per_min=pos['goldPerMin'],
                        exp_per_min=pos['expPerMin']
                    ) for pos in snapshot_data['positions']
                ]
                
                # Transform item builds
                item_builds = [
                    HeroItemBuild(
                        item_id=build['itemId'],
                        win_rate=build['winRate'],
                        purchase_timing=build['purchaseTiming'],
                        matches=build['matches'],
                        synergy_items=[
                            ItemSynergy(
                                item_id=synergy['itemId'],
                                synergy_score=synergy['synergyScore']
                            ) for synergy in build['synergyItems']
                        ]
                    ) for build in snapshot_data['itemBuilds']
                ]
                
                # Transform skill priorities
                skill_priorities = [
                    SkillPriority(
                        ability_id=skill['abilityId'],
                        priority_score=skill['priorityScore']
                    ) for skill in snapshot_data['skillPriorities']
                ]
                
                # Create HeroMetaSnapshot
                meta_snapshot = HeroMetaSnapshot(
                    timestamp=datetime.fromisoformat(snapshot_data['timestamp']),
                    patch_version=snapshot_data['patchVersion'],
                    overall_win_rate=snapshot_data['overallWinRate'],
                    positions=positions,
                    item_builds=item_builds,
                    skill_priorities=skill_priorities
                )
                
                meta_snapshots.append(meta_snapshot)
            
            return meta_snapshots
        
        except Exception as e:
            self.logger.error(f"Error fetching hero meta timeline: {e}")
            raise

    def import_hero_meta_to_neo4j(self, hero_id: int):
        """
        Import hero meta timeline to Neo4j
        
        Args:
            hero_id (int): Hero identifier to import
        """
        try:
            meta_snapshots = self.fetch_hero_meta_timeline(hero_id)
            
            with self.neo4j_driver.session() as session:
                # Create or update Hero node
                session.run(
                    "MERGE (h:Hero {id: $hero_id})", 
                    hero_id=hero_id
                )
                
                # Import each meta snapshot
                for snapshot in meta_snapshots:
                    # Create or link Patch node
                    session.run(
                        """
                        MERGE (p:Patch {version: $patch_version})
                        MERGE (h:Hero {id: $hero_id})-[:META_IN_PATCH]->(p)
                        CREATE (ms:MetaSnapshot {
                            timestamp: $timestamp,
                            overall_win_rate: $win_rate
                        })
                        MERGE (h)-[:HAS_META_SNAPSHOT]->(ms)
                        MERGE (ms)-[:BELONGS_TO_PATCH]->(p)
                        """,
                        hero_id=hero_id,
                        patch_version=snapshot.patch_version,
                        timestamp=snapshot.timestamp.isoformat(),
                        win_rate=snapshot.overall_win_rate
                    )
                    
                    # Import Position Metrics
                    for position in snapshot.positions:
                        session.run(
                            """
                            MATCH (ms:MetaSnapshot {timestamp: $timestamp})
                            CREATE (pm:PositionMetrics {
                                position: $position,
                                pick_rate: $pick_rate,
                                win_rate: $win_rate,
                                gold_per_min: $gpm,
                                exp_per_min: $xpm
                            })
                            MERGE (ms)-[:HAS_POSITION_METRICS]->(pm)
                            """,
                            timestamp=snapshot.timestamp.isoformat(),
                            position=position.position,
                            pick_rate=position.pick_rate,
                            win_rate=position.win_rate,
                            gpm=position.gold_per_min,
                            xpm=position.exp_per_min
                        )
                    
                    # Import Item Builds
                    for item_build in snapshot.item_builds:
                        session.run(
                            """
                            MATCH (ms:MetaSnapshot {timestamp: $timestamp})
                            CREATE (ib:ItemBuild {
                                item_id: $item_id,
                                win_rate: $win_rate,
                                purchase_timing: $purchase_timing,
                                matches: $matches
                            })
                            MERGE (ms)-[:HAS_ITEM_BUILD]->(ib)
                            """,
                            timestamp=snapshot.timestamp.isoformat(),
                            item_id=item_build.item_id,
                            win_rate=item_build.win_rate,
                            purchase_timing=item_build.purchase_timing,
                            matches=item_build.matches
                        )
                        
                        # Import Item Synergies
                        for synergy in item_build.synergy_items:
                            session.run(
                                """
                                MATCH (ib:ItemBuild {item_id: $source_item_id})
                                CREATE (is:ItemSynergy {
                                    item_id: $synergy_item_id,
                                    synergy_score: $synergy_score
                                })
                                MERGE (ib)-[:HAS_SYNERGY]->(is)
                                """,
                                source_item_id=item_build.item_id,
                                synergy_item_id=synergy.item_id,
                                synergy_score=synergy.synergy_score
                            )
                    
                    # Import Skill Priorities
                    for skill in snapshot.skill_priorities:
                        session.run(
                            """
                            MATCH (ms:MetaSnapshot {timestamp: $timestamp})
                            CREATE (sp:SkillPriority {
                                ability_id: $ability_id,
                                priority_score: $priority_score
                            })
                            MERGE (ms)-[:HAS_SKILL_PRIORITY]->(sp)
                            """,
                            timestamp=snapshot.timestamp.isoformat(),
                            ability_id=skill.ability_id,
                            priority_score=skill.priority_score
                        )
            
            self.logger.info(f"Successfully imported meta for hero {hero_id}")
        
        except Exception as e:
            self.logger.error(f"Failed to import hero meta for hero {hero_id}: {e}")
            raise

    def close(self):
        """Close database connections"""
        self.neo4j_driver.close()

def main():
    """
    Main execution entry point
    """
    # Load environment variables
    load_dotenv()
    
    # Retrieve configuration from environment
    STRATZ_API_KEY = os.getenv('STRATZ_API_KEY')
    NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
    NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')

    # Validate required configuration
    if not all([STRATZ_API_KEY, NEO4J_PASSWORD]):
        raise ValueError("Missing required configuration. Check environment variables.")

    # Create importer instance
    importer = STRATZ_Neo4j_Importer(
        STRATZ_API_KEY, 
        NEO4J_URI, 
        NEO4J_USER, 
        NEO4J_PASSWORD
    )

    try:
        # Example: Import meta for hero with ID 1 (Anti-Mage)
        importer.import_hero_meta_to_neo4j(1)
        print("Successfully imported hero meta to Neo4j!")
    except Exception as e:
        logging.error(f"Import failed: {e}")
    finally:
        importer.close()

if __name__ == '__main__':
    main()
