from modules import databases
import os

PGSCHEME = os.getenv("PGSCHEME")

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
        id text,
        chunk_id integer,
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

    # Remove the origin table
    query = f"""DROP TABLE {PGSCHEME}.{name}"""
    result = pgsql.execute_one(query)

    if result:
        # Remove record from topics table
        query = f"""DELETE FROM {PGSCHEME}.topics WHERE name = '{name}'"""
        return pgsql.execute_one(query)


def link_topic_vector(topic_name: str, vector_id: int) -> bool:
    pass