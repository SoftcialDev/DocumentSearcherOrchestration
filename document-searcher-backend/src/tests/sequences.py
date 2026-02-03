from modules.databases import SQLServerConnection, PostgreSQLConnection
from modules.logs import write_line, write_block
from pathlib import Path
import modules.authenticators as auth
import modules.conversions as conv
import modules.manifest as manifest
import modules.sources as sources
import hashlib, logging, os


def start_local_sequence(file_path, file_name, file_id, topic):
    """
    Entry point for local process, reads docs and pdf files from the files folders, going through
    the following steps:

    Reading -> Splitting -> Vectorizing -> Uploading
    
    This entrypoint has the following characteristics:
    - Checks for differences: False
    - Tags content: False
    - Removes the data: False
    """
    logs = []
    logs.append("Reading uploaded files...")
    files = [
        {
            "path": str(file_path),        
            "itemId": file_id,
            "itemName": file_name,
            "folderId": file_id # For local files, folder_id uses file_id
        }
    ]
    vectorize_and_upload_files(files, topic, logs)
    write_block(logs, "Local file upload")

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
    logs = []
    sqlserver = SQLServerConnection()
    postgresql = PostgreSQLConnection()

    logs.append(f"Tables to be fetched: {SYNCTABLES}")

    results = {}
    for table in SYNCTABLES:
        logs.append(f"Fetching source database for {table}")
        query = f"SELECT * FROM {table}"
        result = sqlserver.fetch_all(query)
        logs.append(f"Obtained {len(result['rows'])} records from source {table}")
        results[table] = result

    originals = {}
    for table in SYNCTABLES:
        logs.append(f"Fetching destination database for {table}")
        query = f"SELECT id, content_hash FROM {table}"
        result = postgresql.fetch_all(query)
        logs.append(f"Obtained {len(result['rows'])} records from destination {table}")
        originals[table] = result

    logs.append("Converting data -> human read -> chunks...")
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
    logs.append(f"Created {chunk_count} chunks")

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

        logs.append(f"Uploading {len(new_embeddings)} new vectors")
        upload_embeddings(new_embeddings, logs)
        logs.append("Embeddings uploaded")

        logs.append(f"Updating {len(updated_embeddings)} existing vectors")
        refresh_embeddings(updated_embeddings, logs)
        logs.append("Embeddings updated")

        logs.append(f"Deleting {len(removed_embeddings)} removed vectors")
        delete_embeddings(removed_embeddings, logs)
        logs.append("Embeddings deleted")

        write_block(logs, "DB Sequence")

def start_sharepoint_sequence(key: str, topic:str):
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
    logs = []
    sharepoint_token = auth.get_sharepoint_token(logs)

    try:
        site, list_id, folder = (p.strip() for p in key.split(",", 2))
    except ValueError:
        # unsplittable (not 3 parts) → end the process here
        return

    logs.append("Reading manifest...")
    man = manifest.collect_manifest(SOURCE, topic)
    logs.append("Manifest loaded")

    logs.append("Reading remote content metadata...")
    list_items = sources.get_sharepoint_content(sharepoint_token, topic, site, list_id, folder)
    logs.append("Remote metadata loaded")

    logs.append("Downloading differences")
    downloaded_files = sources.download_sharepoint_file(sharepoint_token, man, list_items)
    logs.append(f"Downloaded {len(downloaded_files)} files")

    vectorize_and_upload_files(downloaded_files, topic, logs)

    logs.append("Registering changes to manifest...")
    manifest.upload_to_manifest(list_items, SOURCE)
    logs.append("Manifest updated")

    logs.append("Cleaning local information...")
    clean_files(downloaded_files, logs)
    logs.append("Local server cleaned")

    write_block(logs, "SH Sequence")

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
    logs = []
    onedrive_token = auth.get_onedrive_token(logs)

    logs.append("Getting users IDS")
    allowed_ids = sources.get_onedrive_users(onedrive_token)
    logs.append(f"Obtained {len(allowed_ids)} ids")

    logs.append("Getting users drives content")
    manifest = []
    for id in allowed_ids:
        logs.append(f"Reading files of {id}")
        manifest = sources.get_onedrive_content(onedrive_token, id, manifest, logs)
    logs.append(f"Fetched {len(manifest)} items metadata")

    logs.append("Downloading items...")
    downloaded_files = sources.download_onedrive_files(onedrive_token, manifest, logs)
    logs.append(f"Downloaded {len(downloaded_files)} files")

    vectorize_and_upload_files(downloaded_files, "onedrive", logs)

    logs.append("Cleaning local information...")
    clean_files(downloaded_files, logs)
    logs.append("Local server cleaned")

    write_block(logs, "OD Sequence")

# Helper methods
# DEPRECATED
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

def clean_files(file_paths: list, logs: list):
    for file in file_paths:
        try:
            if os.path.exists(file['path']):
                os.remove(file['path'])
                logs.append(f"Deleted: {file['path']}")
            else:
                logs.append("---ERROR---")
                logs.append(f"File not found: {file['path']}")
                logs.append("---ERROR---")
        except Exception as e:
            logs.append("---ERROR---")
            logs.append(f"Failed to delete {file['path']}: {e}")
            logs.append("---ERROR---")

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

def upload_embeddings(embeddings: list, logs: list):
    postgresql =  PostgreSQLConnection()
    # Group inserts by table
    records_to_insert = {}
    tables = {item["table"] for item in embeddings}
    for table in tables:
        records_to_insert[table] = {
            "query" : f"""
                INSERT INTO public.{table} (item_id, drive_id, chunk_id, title, content, content_hash, vector)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            "records" : []
        }

    for embedding in embeddings:
        for chunk_id, (content, emb) in enumerate(embedding["embedding"]):
            if "\x00" in content:
                logs.append(f"Skipping chunk {chunk_id} (NUL byte detected)")
                continue

            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            records_to_insert[embedding["table"]]["records"].append((
                embedding["itemId"],
                embedding["folderId"],
                chunk_id,
                embedding["itemName"],
                content,
                content_hash,
                emb.tolist()
            ))

    for table, group in records_to_insert.items():
        postgresql.execute_many(group["query"], group["records"])
        logs.append(f"Uploaded {len(group['records'])} records into {table}.")

def refresh_embeddings(embeddings: list, logs: list):
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
                logs.append(f"Skipping chunk {chunk_id} (NUL byte detected)")
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
        logs.append(f"Updated {len(group['records'])} records from {table}.")

def delete_embeddings(embeddings: list, logs: list):
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
        logs.append(f"Deleted {len(group['records'])} records from {table}.")
        
def vectorize_and_upload_files(files: list, table: str, logs:list):
    if not files:
        logs.append("No files detected, aborting...")
        return

    logs.append("Vectorizing new files...")
    embeddings = []
    if files:
        for file in files:
            logs.append(f"Vectorizing file: {file['path']}")
            chunks = None
            if file["path"].endswith(".docx"):
                chunks = conv.docx_to_chunks(file["path"], logs)
            elif file["path"].endswith(".pdf"):
                chunks = conv.pdf_to_chunks(file["path"], logs)

            if chunks is not None:
                embedding = conv.chunks_to_embeddings(chunks)
                embeddings.append({
                    "table" : table,
                    "itemId" : file["itemId"],
                    "itemName" : file["itemName"],
                    "folderId" : file["folderId"],
                    "embedding" : embedding
                })
    logs.append("All files vectorized")

    logs.append("Uploading new vectors")
    upload_embeddings(embeddings, logs)
    logs.append("Embeddings uploaded")