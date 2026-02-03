from modules.databases import PostgreSQLConnection
from pathlib import Path
import modules.conversions as conv
import os, hashlib

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