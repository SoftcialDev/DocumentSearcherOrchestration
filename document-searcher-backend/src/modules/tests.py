import hashlib


def group_by_table(records):
    """Groups embeddings by table name for easier processing."""
    grouped = {}
    for record in records:
        grouped.setdefault(record["table"], []).append(record)
    return grouped

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