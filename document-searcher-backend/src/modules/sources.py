from typing import Any
from datetime import datetime, timedelta, timezone
import requests
import os

ONEDRIVE_EMAILS = os.getenv("ONEDRIVE_EMAILS")
EXTENSIONS = os.getenv("EXTENSIONS", "").split(",")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

############
# Onedrive #
############
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


def get_onedrive_content(token, user_id, list_items=None, item_id="root", path=""):
    """
    Traverses onedrive content by their user_id, collecting the ids of the items to download them
    if the id is of a folder, it will recursively traverse all folders and obtain their content

    Args:
        token (str): Authentication token to connect with Onedrive
        user_id (str): The owner's id of the folders to traverse
        list_items (list): The returning content, used to recursively add items. Default value None to get a clean list of records
        item_id (str): The starting point to traverse. Default value root to traverse the totality of the files
        path (str): Saving path. Default value empty to save on project root.

    Returns
        A list of ids representing the files contained within the onedrive folder
    """
    # Initalize return content
    if not list_items:
        list_items = []
    headers = {"Authorization": f"Bearer {token}"}

    url = f"https://graph.microsoft.com/v1.0/users/{user_id}/drive/items/{item_id}/children"
    resp = requests.get(url, headers=headers)

    if not resp.ok:
        print(f"Failed to list {item_id} for {user_id}: {resp.status_code}")
        return

    items = resp.json().get("value", [])
    for item in items:
        name = item["name"]
        current_path = f"{path}/{name}".strip("/")

        if "folder" in item:
            # It's a folder, recurse into it
            print(f"[Folder] {current_path} ({item['id']})")
            get_onedrive_content(token, user_id, list_items, item["id"], current_path)
        else:
            # Ignore items without valid extensions
            if not any(name.endswith(ext) for ext in EXTENSIONS):
                continue
            list_items.append({
                "user_id": user_id,
                "item_id": item["id"],
                "name": name,
                "path": current_path,
                "size": item.get("size", 0),
                "lastModifiedDateTime": item.get("lastModifiedDateTime")
            })
    return list_items


def download_onedrive_files(token: str, manifest: dict[str, Any], save_path=".") -> list:
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

            print(f"Downloaded: {filename}")
            files.append({
                "path" : full_path,
                "itemId" : item_id
            })
        else:
            print(f"Failed to download {filename}: {response.status_code} - {response.text}")

    return files
##############
# Sharepoint #
##############
def subscribe_to_sharepoint(token: str, sharepoint_site: str, sharepoint_list: str) -> bool:

    expiration_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()

    url = "https://graph.microsoft.com/v1.0/subscriptions"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "changeType": "updated",
        "notificationUrl": WEBHOOK_URL,
        "resource": f"/sites/{sharepoint_site}/lists/{sharepoint_list}",
        "expirationDateTime": expiration_time,
        "clientState": "SecretClientState"
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        data = response.json()
        print("Subscription created successfully.")
        print("ID:", data.get("id"))
        print("Expires:", data.get("expirationDateTime"))
        return True
    else:
        print("Failed to create subscription.")
        print("Status:", response.status_code)
        print("Response:", response.text)
        return False

def get_sharepoint_content(token: str, sharepoint_site: str, sharepoint_list: str, sharepoint_folder: str):
    base = "https://graph.microsoft.com/v1.0"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    # 1) resolve drive for this list (works for any doc library)
    r = requests.get(f"{base}/sites/{sharepoint_site}/lists/{sharepoint_list}/drive",
                     headers=headers, timeout=30)
    r.raise_for_status()
    drive_id = r.json().get("id")

    # 2) list ONLY the folder's children
    url = f"{base}/drives/{drive_id}/items/{sharepoint_folder}/children?$expand=listItem"
    resp = requests.get(url, headers=headers, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    items = []
    for child in data.get("value", []):
        name = child.get("name", "")
        if EXTENSIONS and not any(name.lower().endswith(ext) for ext in EXTENSIONS):
            continue
        items.append({
            "name": name,
            "webUrl": child.get("webUrl", ""),
            "id": child.get("id", ""),
            "size": child.get("size"),
            "lastModifiedDateTime": child.get("lastModifiedDateTime"),
            "driveId": child.get("parentReference", {}).get("driveId"),
            "listItemId": (child.get("listItem") or {}).get("id"),
        })

    return items
        
def download_sharepoint_file(token, manifest, items):
    files = []

    # Build a set of (drive_id, file_id) from manifest (snake_case)
    manifest_keys = {
        (str(m["drive_id"]), str(m["file_id"]))
        for m in manifest
        if m.get("drive_id") and m.get("file_id")
    }

    for item in items:
        drive_id = item.get("driveId")
        item_id  = item.get("driveItemId") or item.get("id")
        file_name = item.get("fileName") or item.get("name")
        download_dir = ""  # keep your current behavior

        if not drive_id or not item_id or not file_name:
            continue  # missing essentials; skip

        # Only .docx / .pdf
        fn_lower = file_name.lower()
        if not (fn_lower.endswith(".docx") or fn_lower.endswith(".pdf")):
            continue

        # Skip items already on manifest
        if (str(drive_id), str(item_id)) in manifest_keys:
            continue

        url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/content"
        headers = { "Authorization": f"Bearer {token}" }

        response = requests.get(url, headers=headers, stream=True)
        if response.status_code == 200:
            file_path = os.path.join(download_dir, file_name)
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            files.append({"path": file_path, "itemId": item_id})
        else:
            pass

    return files