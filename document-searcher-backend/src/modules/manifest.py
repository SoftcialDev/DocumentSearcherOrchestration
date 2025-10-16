from modules.databases import PostgreSQLConnection
from modules.authenticators import get_secret


def collect_manifest(source: str, topic: str) -> list:
    """
        Returns a manifest of the specified source
    """
    PGSCHEME = get_secret("PGSCHEME")
    postgresql =  PostgreSQLConnection()
    query = f"SELECT * FROM {PGSCHEME}.manifests WHERE source = '{source}' AND topic = '{topic}'"

    result = postgresql.fetch_all(query)
    return result.get("rows", [])

def upload_to_manifest(values: list[dict], source: str) -> bool:
    """
    Converts a list of JSONs into a list of tuples to be inserted into the manifest
    """
    postgresql =  PostgreSQLConnection()
    inserts = []
    PGSCHEME = get_secret("PGSCHEME")

    query = f"""
        INSERT INTO {PGSCHEME}.manifests
            (topic, file_id, drive_id, name, web_url, last_modified, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (topic, file_id, drive_id) DO UPDATE
        SET name = EXCLUDED.name,
            web_url = EXCLUDED.web_url,
            last_modified = EXCLUDED.last_modified;
    """

    for element in values:
        inserts.append((
            element.get("topic"),
            element.get("id"),
            element.get("parentId"),
            element.get("name","")[:255], # Truncates long files names
            element.get("webUrl"),
            element.get("lastModifiedDateTime"),
            source
        ))

    return postgresql.execute_many(query, inserts)

def remove_from_manifest(values: list[str]) -> bool:
    """
    Deletes elements from the manifest, the strings have the format of 'file_id,driveId'
    which is the key to be deleted
    """
    postgresql =  PostgreSQLConnection()
    deletes = []
    PGSCHEME = get_secret("PGSCHEME")

    query = f"""
        DELETE FROM {PGSCHEME}.manifests
        WHERE file_id = %s AND drive_id = %s
    """

    for element in values:
        keys = element.split(",")
        deletes.append((
            keys[0],
            keys[1]
        ))

    return postgresql.execute_many(query, deletes)
