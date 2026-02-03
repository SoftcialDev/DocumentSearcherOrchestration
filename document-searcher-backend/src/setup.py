from modules.databases import PostgreSQLConnection
from modules.authenticators import get_secret
from modules.logs import write_line
import psutil
import logging
import os

################################################
# Set up for the minimal working configuration #
################################################
def database_setup() -> bool:
    PGSCHEME = get_secret("PGSCHEME")
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
            topic VARCHAR(255) NOT NULL,
            file_id VARCHAR(255) NOT NULL,
            drive_id VARCHAR(255) NOT NULL,
            name VARCHAR(255) NOT NULL, 
            web_url TEXT NOT NULL,
            last_modified TIMESTAMPTZ NOT NULL,
            source VARCHAR(255) NOT NULL,
            PRIMARY KEY (topic, file_id, drive_id)
        );
    """
    if not pgsql.execute_one(manifest_query):
        return False
    
    connected_accounts_query = """
        CREATE TABLE IF NOT EXISTS public.connected_accounts (
            user_id VARCHAR(255) NOT NULL,
            source VARCHAR(255) NOT NULL,
            access_token VARCHAR(255) NOT NULL,
            refresh_token VARCHAR(255) NOT NULL,
            expires_at BIGINT NOT NULL,
            PRIMARY KEY (user_id, source)
        );
    """
    if not pgsql.execute_one(connected_accounts_query):
        return False
    
    source_accounts_query = """
        CREATE TABLE IF NOT EXISTS public.sources_accounts (
            -- FK to public.sources PK (topic, id)
            topic           TEXT        NOT NULL,
            id              TEXT        NOT NULL,

            -- FK to public.connected_accounts PK (user_id, source)
            user_id         VARCHAR(255) NOT NULL,
            account_source  VARCHAR(255) NOT NULL,   -- e.g., 'GoogleDrive', 'OneDrive', etc.

            -- Composite PK across both parents
            PRIMARY KEY (topic, id, user_id, account_source),

            FOREIGN KEY (topic, id)
                REFERENCES public.sources (topic, id)
                ON DELETE CASCADE,

            FOREIGN KEY (user_id, account_source)
                REFERENCES public.connected_accounts (user_id, source)
                ON DELETE CASCADE
        );
    """
    if not pgsql.execute_one(source_accounts_query):
        return False

    return True


def env_checkup() -> tuple[bool, bool]:
    error = False
    warning = 0

    # Strictly necessary variables for vector database
    PGHOST = get_secret("PGHOST")
    PGUSER = get_secret("PGUSER")
    PGPORT = get_secret("PGPORT", 5432)
    PGDATABASE = get_secret("PGDATABASE")
    PGSCHEME = get_secret("PGSCHEME")
    PGPASSWORD = get_secret("PGPASSWORD")
    if not PGHOST or not PGUSER or not PGPORT or not PGDATABASE or not PGSCHEME or not PGPASSWORD:
        write_line("Vector database variables are not set, system will not be able to communicate with vectors")
        error = True

    # Strictly necessary variables for Sharepoint / Onedrive / Graph
    SESV = get_secret("SHAREPOINTENTRASECRET")
    SECI = get_secret("SHAREPOINTENTRACLIENTID")
    OESV = get_secret("ONEDRIVEENTRASECRET")
    OETI = get_secret("ONEDRIVEENTRATENANT")
    OECI = get_secret("ONEDRIVEENTRACLIENTID")
    if not SESV or not SECI or not OESV or not OETI or not OECI or not GET:
        write_line("Microsoft services variables are not set, system will not be able to download files from sources")
        error = True

    # Necessary for some functions, can be omitted by using default values
    EXTENSIONS = os.getenv("EXTENSIONS", None)
    if not EXTENSIONS:
        write_line(f"Extensions variable are not set, using default formats .PDF .DOCX")
        warning += 1

    return error, warning

def ram_checkup(required_gb: int, logs: list):
    total_gb = psutil.virtual_memory().total / (1024 ** 3)
    write_line(f"Detected RAM: {total_gb:.2f} GB")
    if total_gb < required_gb:
        write_line("Not enough RAM detected to run this program")
        return False
    return True