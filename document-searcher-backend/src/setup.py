from modules.databases import PostgreSQLConnection
import psutil
import logging
import os

################################################
# Set up for the minimal working configuration #
################################################
def database_setup() -> bool:
    PGSCHEME = os.getenv("PGSCHEME")
    pgsql = PostgreSQLConnection()

    topics_query = f"""
        CREATE TABLE IF NOT EXISTS {PGSCHEME}.topics (
            name TEXT PRIMARY KEY
        );
    """
    if not pgsql.execute_one(topics_query):
        return False

    subs_query = f"""
        CREATE TABLE IF NOT EXISTS {PGSCHEME}.sources (
            topic TEXT NOT NULL,
            name TEXT,
            id TEXT NOT NULL,
            schedule text NOT NULL,
            site TEXT,
            PRIMARY KEY (topic, id),
            FOREIGN KEY (topic) REFERENCES {PGSCHEME}.topics(name) ON DELETE CASCADE
        );
    """
    if not pgsql.execute_one(subs_query):
        return False

    manifest_query = f"""
        CREATE TABLE IF NOT EXISTS {PGSCHEME}.manifests (
            file_id VARCHAR(255) NOT NULL,
            drive_id VARCHAR(255) NOT NULL,
            name VARCHAR(255) NOT NULL, 
            web_url TEXT NOT NULL,
            last_modified TIMESTAMPTZ NOT NULL,
            PRIMARY KEY (file_id, drive_id)
        );
    """
    if not pgsql.execute_one(manifest_query):
        return False

    return True


def env_checkup() -> tuple[bool, bool]:
    error = False
    warning = 0

    # Strictly necessary variables for vector database
    PGHOST = os.getenv("PGHOST")
    PGUSER = os.getenv("PGUSER")
    PGPORT = os.getenv("PGPORT", 5432)
    PGDATABASE = os.getenv("PGDATABASE")
    PGSCHEME = os.getenv("PGSCHEME")
    PGPASSWORD = os.getenv("PGPASSWORD")
    if not PGHOST or not PGUSER or not PGPORT or not PGDATABASE or not PGSCHEME or not PGPASSWORD:
        logging.error("Vector database variables are not set, system will not be able to communicate with vectors")
        error = True

    # Strictly necessary variables for Sharepoint / Onedrive / Graph
    SESV = os.getenv("SHAREPOINT_ENTRA_SECRET_VALUE")
    SECI = os.getenv("SHAREPOINT_ENTRA_CLIENT_ID")
    OESV = os.getenv("ONEDRIVE_ENTRA_SECRET_VALUE")
    OETI = os.getenv("ONEDRIVE_ENTRA_TENANT_ID")
    OECI = os.getenv("ONEDRIVE_ENTRA_CLIENT_ID")
    GET = os.getenv("GRAPH_TOKEN_ENDPOINT")
    if not SESV or not SECI or not OESV or not OETI or not OECI or not GET:
        logging.error("Microsoft services variables are not set, system will not be able to download files from sources")
        error = True

    # Necessary for some functions, can be omitted by using default values
    EXTENSIONS = os.getenv("EXTENSIONS", None)
    if not EXTENSIONS:
        logging.warning(f"Extensions variable are not set, using default formats .PDF .DOCX")
        warning += 1

    return error, warning

def ram_checkup(required_gb: int):
    total_gb = psutil.virtual_memory().total / (1024 ** 3)
    logging.info(f"Detected RAM: {total_gb:.2f} GB")
    if total_gb < required_gb:
        logging.error("Not enough RAM detected to run this program")
        return False
    return True