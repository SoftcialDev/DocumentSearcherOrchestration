from modules import databases
import os

def list_topics() -> list:
    """
    
    """
    pgscheme = os.getenv("PGSCHEME")
    pgsql = databases.PostgreSQLConnection()
    query = f"SELECT name FROM {pgscheme}.topics"
    result = pgsql.fetch_all(query)
    return result["rows"]

def create_topic(name: str) -> bool:
    """

    """
    # Create the origin table
    pgscheme = os.getenv("PGSCHEME")
    pgsql = databases.PostgreSQLConnection()
    query = f"""CREATE TABLE {pgscheme}.{name} (
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
        query = f"""INSERT INTO {pgscheme}.topics VALUES('{name}')"""
        return pgsql.execute_one(query)

def rename_topic(old_name: str, new_name: str) -> bool:
    """
    
    """
    pgsql = databases.PostgreSQLConnection()
    pgscheme = os.getenv("PGSCHEME")
    # Rename the origin table
    query = f"""ALTER TABLE {pgscheme}.{old_name} RENAME TO {new_name}"""
    result = pgsql.execute_one(query)

    if result:
        # Update record from topics table
        query = f"""UPDATE {pgscheme}.topics SET name = {new_name} WHERE name = '{old_name}'"""
        return pgsql.execute_one(query)

def delete_topic(name: str) -> bool:
    """
    
    """
    pgsql = databases.PostgreSQLConnection()
    pgscheme = os.getenv("PGSCHEME")
    # Collect the drive_id references
    drive_ids_query = f"""SELECT DISTINCT drive_id FROM {pgscheme}.{name}"""
    drive_ids = pgsql.fetch_all(drive_ids_query)

    # Remove the origin table
    drop_query = f"""DROP TABLE {pgscheme}.{name}"""
    drop_result = pgsql.execute_one(drop_query)

    if drop_result:
        # Remove record from manifests table
        sources_query = f"""DELETE FROM {pgscheme}.manifests WHERE topic = '{name}'"""
        sources_result = pgsql.execute_one(sources_query)
    
        # Remove record from sources table
        manifests_query = f"""DELETE FROM {pgscheme}.sources WHERE topic = '{name}'"""
        manifests_result = pgsql.execute_one(manifests_query)

        # Remove record from topics table
        topics_query = f"""DELETE FROM {pgscheme}.topics WHERE name = '{name}'"""
        topics_result = pgsql.execute_one(topics_query)

        return topics_result and manifests_result and sources_result
    else:
        return False
