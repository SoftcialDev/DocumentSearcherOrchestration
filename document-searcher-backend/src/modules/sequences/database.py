from modules.sequences.helpers import compare_records, upload_embeddings, refresh_embeddings, delete_embeddings
from modules.databases import PostgreSQLConnection, SQLServerConnection
from modules.logs import write_block
import modules.conversions as conv
import os

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