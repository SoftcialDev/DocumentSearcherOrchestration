from modules import databases
from modules.authenticators import get_secret
import os

PGSCHEME = get_secret("PGSCHEME")

def list_topics() -> list:
    """
    
    """
    pgsql = databases.PostgreSQLConnection()
    query = f"SELECT name FROM {PGSCHEME}.topics"
    result = pgsql.fetch_all(query)
    return result["rows"]

def create_topic(name: str) -> bool:
    """

    """
    # Create the origin table
    pgsql = databases.PostgreSQLConnection()
    query = f"""CREATE TABLE {PGSCHEME}.{name} (
        item_id text,
        drive_id text,
        chunk_id integer,
        title text,
        content text,
        content_hash text,
        vector vector(768),
        tsv tsvector GENERATED ALWAYS AS (to_tsvector('spanish'::regconfig, content)) STORED
    )"""
    result = pgsql.execute_one(query)

    if result:
        # Create a record in the topics table
        query = f"""INSERT INTO {PGSCHEME}.topics VALUES('{name}')"""
        return pgsql.execute_one(query)

def rename_topic(old_name: str, new_name: str) -> bool:
    """
    
    """
    pgsql = databases.PostgreSQLConnection()
    # Rename the origin table
    query = f"""ALTER TABLE {PGSCHEME}.{old_name} RENAME TO {new_name}"""
    result = pgsql.execute_one(query)

    if result:
        # Update record from topics table
        query = f"""UPDATE {PGSCHEME}.topics SET name = {new_name} WHERE name = '{old_name}'"""
        return pgsql.execute_one(query)

def delete_topic(name: str) -> bool:
    """
    
    """
    pgsql = databases.PostgreSQLConnection()
    # Collect the drive_id references
    drive_ids_query = f"""SELECT DISTINCT drive_id FROM {PGSCHEME}.{name}"""
    drive_ids = pgsql.fetch_all(drive_ids_query)

    # Remove the origin table
    drop_query = f"""DROP TABLE {PGSCHEME}.{name}"""
    drop_result = pgsql.execute_one(drop_query)

    if drop_result:
        # Remove record from manifests table
        sources_query = f"""DELETE FROM {PGSCHEME}.manifests WHERE topic = '{name}'"""
        sources_result = pgsql.execute_one(sources_query)
    
        # Remove record from sources table
        manifests_query = f"""DELETE FROM {PGSCHEME}.sources WHERE topic = '{name}'"""
        manifests_result = pgsql.execute_one(manifests_query)

        # Remove record from topics table
        topics_query = f"""DELETE FROM {PGSCHEME}.topics WHERE name = '{name}'"""
        topics_result = pgsql.execute_one(topics_query)

        return topics_result and manifests_result and sources_result
    else:
        return False
