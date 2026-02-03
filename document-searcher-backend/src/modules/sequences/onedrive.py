from modules.sequences.helpers import vectorize_and_upload_files, clean_files
import modules.authenticators as auth
from modules.logs import write_block
from typing import Any
import requests, os

ONEDRIVE_EMAILS = os.getenv("ONEDRIVE_EMAILS")
EXTENSIONS = os.getenv("EXTENSIONS", "").split(",")

def get_onedrive_users(token: str) -> list:
    """
    Get the IDs of the folder sources to download the files for RAG conversion. To obtain the IDs 
    of those folder the email of each user to obtain the files from. The emails of those users
    must be in the same tenant of the provided token.

    Args:
        token (str): A Graph token authentication

    Returns:
        list: A list of strings of each folder IDs
    """
    allowed_users = ONEDRIVE_EMAILS.split(",")
    allowed_ids = []

    url = "https://graph.microsoft.com/v1.0/users"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    users = response.json().get("value", [])
    for user in users:
        if user["userPrincipalName"] in allowed_users:
            allowed_ids.append(user["id"])
    
    return allowed_ids


def get_onedrive_content(onedrive_token: str, user_id: str, manifest: list, logs: list, item_id="root", path=""):
    """
    Traverses onedrive content by their user_id, collecting the ids of the items to download them
    if the id is of a folder, it will recursively traverse all folders and obtain their content

    Args:
        token (str): Authentication token to connect with Onedrive
        user_id (str): The owner's id of the folders to traverse
        manifest (list): The returning content, used to recursively add items. Default value None to get a clean list of records
        item_id (str): The starting point to traverse. Default value root to traverse the totality of the files
        path (str): Saving path. Default value empty to save on project root.

    Returns
        A list of ids representing the files contained within the onedrive folder
    """
    # Initalize return content
    if not manifest:
        manifest = []
    headers = {"Authorization": f"Bearer {onedrive_token}"}

    url = f"https://graph.microsoft.com/v1.0/users/{user_id}/drive/items/{item_id}/children"
    resp = requests.get(url, headers=headers)

    if not resp.ok:
        logs.append("---ERROR---")
        logs.append(f"Failed to list {item_id} for {user_id}: {resp.status_code}")
        logs.append("---ERROR---")
        return

    items = resp.json().get("value", [])
    for item in items:
        name = item["name"]
        current_path = f"{path}/{name}".strip("/")

        if "folder" in item:
            # It's a folder, recurse into it
            logs.append(f"[Folder] {current_path} ({item['id']})")
            get_onedrive_content(onedrive_token, user_id, manifest, item["id"], current_path)
        else:
            # Ignore items without valid extensions
            if not any(name.endswith(ext) for ext in EXTENSIONS):
                continue
            manifest.append({
                "user_id": user_id,
                "item_id": item["id"],
                "name": name,
                "path": current_path,
                "size": item.get("size", 0),
                "lastModifiedDateTime": item.get("lastModifiedDateTime")
            })
    return manifest


def download_onedrive_files(token: str, manifest: dict[str, Any], logs: list, save_path=".") -> list:
    """
    Download a series of files from onedrive and temporaly store in local storage

    Args:
        token (str):
        manifest (dict): 
        save_path (str): 
    """
    files = []
    for file in manifest:
        user_id = file["user_id"]
        item_id = file["item_id"]
        filename = file["name"]

        headers = {"Authorization": f"Bearer {token}"}

        url = f"https://graph.microsoft.com/v1.0/users/{user_id}/drive/items/{item_id}/content"
        response = requests.get(url, headers=headers, stream=True)

        if response.status_code == 200:
            os.makedirs(save_path, exist_ok=True)
            full_path = os.path.join(save_path, filename)

            with open(full_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            logs.append(f"Downloaded: {filename}")
            files.append({
                "path" : full_path,
                "itemId" : item_id
            })
        else:
            logs.append(f"Failed to download {filename}: {response.status_code} - {response.text}")

    return files

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
    allowed_ids = get_onedrive_users(onedrive_token)
    logs.append(f"Obtained {len(allowed_ids)} ids")

    logs.append("Getting users drives content")
    manifest = []
    for id in allowed_ids:
        logs.append(f"Reading files of {id}")
        manifest = get_onedrive_content(onedrive_token, id, manifest, logs)
    logs.append(f"Fetched {len(manifest)} items metadata")

    logs.append("Downloading items...")
    downloaded_files = download_onedrive_files(onedrive_token, manifest, logs)
    logs.append(f"Downloaded {len(downloaded_files)} files")

    vectorize_and_upload_files(downloaded_files, "onedrive", logs)

    logs.append("Cleaning local information...")
    clean_files(downloaded_files, logs)
    logs.append("Local server cleaned")

    write_block(logs, "OD Sequence")