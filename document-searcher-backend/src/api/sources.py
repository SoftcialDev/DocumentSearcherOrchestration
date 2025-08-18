from modules import databases
import os

PGSCHEME = os.getenv("PGSCHEME")

def list_sources(topic: str):
    """
    
    """
    pgsql = databases.PostgreSQLConnection()
    query = f"SELECT * FROM {PGSCHEME}.sources WHERE topic = '{topic}'"
    return pgsql.fetch_all(query)['rows']

def add_sources(values: list):
    pgsql = databases.PostgreSQLConnection()
    query = f"""
        INSERT INTO {PGSCHEME}.sources (topic, name, id, schedule, site)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (topic, id) DO NOTHING;
    """
    return pgsql.execute_many(query, values)

def remove_source(topic_name: str, source_id: str):
    pgsql = databases.PostgreSQLConnection()
    query = f"""
        DELETE FROM {PGSCHEME}.sources WHERE topic = '{topic_name}' AND id = '{source_id}'
    """
    return pgsql.execute_one(query)

def update_source(topic: str, id: str, schedule: str):
    pgsql = databases.PostgreSQLConnection()
    query = f"UPDATE {PGSCHEME}.sources SET schedule = {schedule} WHERE topic = '{topic}' AND id = '{id}'"
    return pgsql.execute_one(query)