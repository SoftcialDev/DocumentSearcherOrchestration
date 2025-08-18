import json
import os
from pathlib import Path
from typing import Any

SHAREPOINT_MANIFEST_FILE = "sharepoint_manifest.json"
ONEDRIVE_MANIFEST_FILE = "onedrive_manifest.json"

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

def get_manifest_path(source: str) -> str:
    """
    Loads the manifest of the latest uploaded files

    Args:
        source (str): The origin of the manifest, either SHAREPOINT or ONEDRIVE

    Return:
        The path of the local manifest of the source provided
    """
    if source == "SHAREPOINT":
        return SHAREPOINT_MANIFEST_FILE
    elif source == "ONEDRIVE":
        return ONEDRIVE_MANIFEST_FILE
    else:
        print("Could not load manifest file")
        return None

def update_manifest(manifest: dict[str, Any], source: str) -> None:
    path = get_manifest_path(source)
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)

def load_manifest(source: str) -> dict[str, Any]:
    path = get_manifest_path(source)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}