from modules import databases
from modules.logs import write_line
from modules.authenticators import get_secret
import os

PGSCHEME = get_secret("PGSCHEME")

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
    parent_id = source_id.rsplit(",", 1)[-1].strip()
        
    # Start deleting
    query_sources = f"""
        DELETE FROM {PGSCHEME}.sources WHERE topic = '{topic_name}' AND id = '{source_id}'
    """
    result_sources = pgsql.execute_one(query_sources)
    write_line(query_sources)

    query_vectors = f"""
        DELETE FROM {PGSCHEME}.{topic_name} WHERE drive_id = '{parent_id}'
    """
    result_vectors = pgsql.execute_one(query_vectors)
    write_line(query_vectors)

    query_manifests = f"""
        DELETE FROM {PGSCHEME}.manifests WHERE drive_id = '{parent_id}' AND topic = '{topic_name}'
    """
    result_manifests = pgsql.execute_one(query_manifests)
    write_line(query_manifests)

    return result_sources and result_vectors and result_manifests

def update_source(topic: str, id: str, schedule: str):
    pgsql = databases.PostgreSQLConnection()
    query = f"UPDATE {PGSCHEME}.sources SET schedule = {schedule} WHERE topic = '{topic}' AND id = '{id}'"
    return pgsql.execute_one(query)