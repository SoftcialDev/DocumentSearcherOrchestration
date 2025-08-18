from modules.databases import SQLServerConnection, PostgreSQLConnection
from pathlib import Path
import modules.authenticators as auth
import modules.conversions as conv
import modules.manifest as manifest
import modules.sources as sources
import hashlib
import logging
import os


def start_local_sequence():
    """
    Entry point for local process, reads docs and pdf files from the files folders, going through
    the following steps:

    Reading -> Splitting -> Vectorizing -> Uploading
    
    This entrypoint has the following characteristics:
    - Checks for differences: False
    - Tags content: False
    - Removes the data: False
    """
    logging.info("Reading local files...")
    files = read_local_files()
    logging.info(f"Found {len(files)} files")

    vectorize_and_upload_files(files)

def start_database_sequence():
    """
    Entry point for database consumptions, queries the content of the SQL Server configured
    tables, fetches their content and parse the result in the following steps:

    Reading -> Splitting -> Hashing -> Vectorizing -> Uploading
    
    This entrypoint has the following characteristics:
    - Checks for differences: True
    - Tags content: True
    - Removes the data: False
    """
    SYNCTABLES = os.getenv("SYNCTABLES").split(",")
    
    sqlserver = SQLServerConnection()
    postgresql = PostgreSQLConnection()

    logging.info(f"Tables to be fetched: {SYNCTABLES}")

    results = {}
    for table in SYNCTABLES:
        logging.info(f"Fetching source database for {table}")
        query = f"SELECT * FROM {table}"
        result = sqlserver.fetch_all(query)
        logging.info(f"Obtained {len(result["rows"])} records from source {table}")
        results[table] = result

    originals = {}
    for table in SYNCTABLES:
        logging.info(f"Fetching destination database for {table}")
        query = f"SELECT id, content_hash FROM {table}"
        result = postgresql.fetch_all(query)
        logging.info(f"Obtained {len(result["rows"])} records from destination {table}")
        originals[table] = result

    logging.info("Converting data -> human read -> chunks...")
    chunks_sets = {}
    chunk_count = 0
    for table, result in results.items():
        pk_struct = sqlserver.get_primary_key(table)
        for row in result["rows"]:
            id_value = "_".join(str(row[key]) for key in pk_struct)
            text = conv.data_to_human(table, row)
            chunks = conv.string_to_chunks(text)
            chunks_sets[f"{table}+{id_value}"] = chunks
            chunk_count = chunk_count + len(chunks)
    logging.info(f"Created {chunk_count} chunks")

    final_records = compare_records(chunks_sets, originals, sqlserver)

    if chunks_sets:
        new_embeddings = []
        updated_embeddings = []
        removed_embeddings = {}

        for key, chunks in chunks_sets.items():
            key_values = key.split("+")
            table = key_values[0]
            id_value = key_values[1]

            # process new records
            if id_value in final_records[table]["new"]:

                embedding = conv.chunks_to_embeddings(chunks)
                new_embeddings.append({
                    "table": table,
                    "itemId": id_value,
                    "embedding": embedding
                })

            # process updated new records
            if id_value in final_records[table]["updated"]:

                embedding = conv.chunks_to_embeddings(chunks)
                updated_embeddings.append({
                    "table": table,
                    "itemId": id_value,
                    "embedding": embedding
                })

        # Process deleted records
        removed_embeddings = []
        for table, changes in final_records.items():
            deleted_ids = changes.get("deleted", [])
            for id_value in deleted_ids:
                removed_embeddings.append({
                    "table": table,
                    "itemId": id_value,
                    "embedding": None
                })

        logging.info(f"Uploading {len(new_embeddings)} new vectors")
        upload_embeddings(new_embeddings)
        logging.info("Embeddings uploaded")

        logging.info(f"Updating {len(updated_embeddings)} existing vectors")
        refresh_embeddings(updated_embeddings)
        logging.info("Embeddings updated")

        logging.info(f"Deleting {len(removed_embeddings)} removed vectors")
        delete_embeddings(removed_embeddings)
        logging.info("Embeddings deleted")

def start_sharepoint_sequence(composite: str, topic:str):
    """
    Entry point for sharepoint consumptions, reads the content of a subscribed sharepoint
    folder, fetches their content and parse the result in the following steps:

    Reading -> Splitting  -> Vectorizing -> Uploading
    
    This entrypoint has the following characteristics:
    - Checks for differences: False
    - Tags content: True
    - Removes the data: True
    """
    SOURCE = "SHAREPOINT"
    sharepoint_token = auth.get_sharepoint_token()

    site, list, folder = composite.split(",", 2)

    logging.info("Reading manifest...")
    man = manifest.collect_manifest(SOURCE)
    logging.info("Manifest loaded")

    logging.info("Reading remote content metadata...")
    list_items = sources.get_sharepoint_content(sharepoint_token, site, list, folder)
    logging.info("Remote metadata loaded")

    logging.info("Downloading differences")
    downloaded_files = sources.download_sharepoint_file(sharepoint_token, man, list_items)
    logging.info(f"Downloaded {len(downloaded_files)} files")

    vectorize_and_upload_files(downloaded_files, topic)

    logging.info("Registering changes to manifest...")
    manifest.upload_to_manifest(list_items, SOURCE)
    logging.info("Manifest updated")

    logging.info("Cleaning local information...")
    clean_files(downloaded_files)
    logging.info("Local server cleaned")

def start_onedrive_sequence():
    """
    Entry point for sharepoint consumptions, reads the content of a subscribed sharepoint
    folder, fetches their content and parse the result in the following steps:

    Reading -> Splitting  -> Vectorizing -> Uploading
    
    This entrypoint has the following characteristics:
    - Checks for differences: False
    - Tags content: True
    - Removes the data: True
    """
    SOURCE = "ONEDRIVE"
    onedrive_token = auth.get_onedrive_token()

    logging.info("Getting users IDS")
    allowed_ids = sources.get_onedrive_users(onedrive_token)
    logging.info(f"Obtained {len(allowed_ids)} ids")

    logging.info("Getting users drives content")
    manifest = []
    for id in allowed_ids:
        logging.info(f"Reading files of {id}")
        manifest = sources.get_onedrive_content(onedrive_token, id, manifest)
    logging.info(f"Fetched {len(manifest)} items metadata")

    logging.info("Downloading items...")
    downloaded_files = sources.download_onedrive_files(onedrive_token, manifest)
    logging.info(f"Downloaded {len(downloaded_files)} files")

    vectorize_and_upload_files(downloaded_files, "onedrive")

    logging.info("Cleaning local information...")
    clean_files(downloaded_files)
    logging.info("Local server cleaned")

# Helper methods
def read_local_files():
    files_dir = Path(__file__).parent / "files"
    all_files = [
        {
            "path": str(f),        
            "itemId": "LocalFile"
        }
        for f in files_dir.iterdir() if f.is_file()
    ]
    return all_files

def clean_files(file_paths: list):
    for file in file_paths:
        try:
            if os.path.exists(file['path']):
                os.remove(file['path'])
                logging.info(f"Deleted: {file['path']}")
            else:
                logging.warning(f"File not found: {file['path']}")
        except Exception as e:
            logging.exception(f"Failed to delete {file['path']}: {e}")

def compare_records(chunks_sets, originals):
    summary = {}
    
    for key, chunks in chunks_sets.items():
        table, id_value = key.split("+", 1)

        # Generate hash of the current content (joined chunks)
        content = "\n".join(chunks)
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        # Build destination dict once per table
        if table not in summary:
            dst_rows = originals.get(table, {}).get("rows", [])
            dst_dict = {row["id"]: row["content_hash"] for row in dst_rows}
            summary[table] = {
                "new": [],
                "updated": [],
                "deleted": [],
                "dst_dict": dst_dict
            }
        else:
            dst_dict = summary[table]["dst_dict"]

        # Check existence and differences
        if id_value not in dst_dict:
            summary[table]["new"].append(id_value)
        elif dst_dict[id_value] != content_hash:
            summary[table]["updated"].append(id_value)
        # else → record unchanged, do nothing

    # Now detect deleted records
    for table, data in summary.items():
        current_ids = set(
            id_key.split("+", 1)[1] for id_key in chunks_sets if id_key.startswith(table + "+")
        )
        dst_ids = set(data["dst_dict"].keys())
        deleted_ids = dst_ids - current_ids
        summary[table]["deleted"].extend(deleted_ids)

        # Remove dst_dict from final summary (optional)
        del summary[table]["dst_dict"]

    return summary

def upload_embeddings(embeddings: list):
    postgresql =  PostgreSQLConnection()
    # Group inserts by table
    records_to_insert = {}
    tables = {item["table"] for item in embeddings}
    for table in tables:
        records_to_insert[table] = {
            "query" : f"""
                INSERT INTO public.{table} (id, chunk_id, content, content_hash, vector)
                VALUES (%s, %s, %s, %s, %s)
            """,
            "records" : []
        }

    for embedding in embeddings:
        for chunk_id, (content, emb) in enumerate(embedding["embedding"]):
            if "\x00" in content:
                logging.warning(f"Skipping chunk {chunk_id} (NUL byte detected)")
                continue

            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            records_to_insert[embedding["table"]]["records"].append((
                embedding["itemId"],
                chunk_id,
                content,
                content_hash,
                emb.tolist()
            ))

    for table, group in records_to_insert.items():
        postgresql.execute_many(group["query"], group["records"])
        logging.info(f"Uploaded {len(group['records'])} records into {table}.")

def refresh_embeddings(embeddings: list):
    postgresql =  PostgreSQLConnection()

    # Group updates by table
    records_to_update = {}
    tables = {item["table"] for item in embeddings}
    for table in tables:
        records_to_update[table] = {
            "query" : f"""
                UPDATE {table}
                SET vector = %s, content = %s, content_hash = %s
                WHERE id = %s AND chunk_id = %s
            """,
            "records" : []
        }

    for embedding in embeddings:
        for chunk_id, (content, emb) in enumerate(embedding["embedding"]):
            if "\x00" in content:
                logging.warning(f"Skipping chunk {chunk_id} (NUL byte detected)")
                continue

            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            records_to_update[embedding["table"]]["records"].append((
                emb.tolist(),          
                content,               
                content_hash,          
                embedding["itemId"],
                chunk_id 
            ))

    for table, group in records_to_update.items():
        postgresql.execute_many(group["query"], group["records"])
        logging.info(f"Updated {len(group['records'])} records from {table}.")


def delete_embeddings(embeddings: list):
    postgresql =  PostgreSQLConnection()

    records_to_delete = {}
    tables = {item["table"] for item in embeddings}
    for table in tables:
        records_to_delete[table] = {
            "query" : f"DELETE FROM {table} WHERE id = %s",
            "records" : []
        }

    for embedding in embeddings:
        records_to_delete[embedding["table"]]["records"].append((embedding["itemId"],))
            
    for table, group in records_to_delete.items():
        postgresql.execute_many(group["query"], group["records"])
        logging.info(f"Deleted {len(group['records'])} records from {table}.")
        
def vectorize_and_upload_files(files, table):
    if not files:
        logging.info("No files detected, aborting...")
        return

    logging.info("Vectorizing new files...")
    embeddings = []
    if files:
        for file in files:
            logging.info(f"Vectorizing file: {file['path']}")
            chunks = None
            if file["path"].endswith(".docx"):
                chunks = conv.docx_to_chunks(file["path"])
            elif file["path"].endswith(".pdf"):
                chunks = conv.pdf_to_chunks(file["path"])

            if chunks is not None:
                embedding = conv.chunks_to_embeddings(chunks)
                embeddings.append({
                    "table" : table,
                    "itemId" : file["itemId"],
                    "embedding" : embedding
                })
    logging.info("All files vectorized")

    logging.info("Uploading new vectors")
    upload_embeddings(embeddings)
    logging.info("Embeddings uploaded")