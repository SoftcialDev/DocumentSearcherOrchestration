from modules.sequences.helpers import vectorize_and_upload_files, clean_files
from modules.logs import write_block
import modules.sources as sources
import modules.manifest as manifest
import modules.authenticators as auth
import requests, os

EXTENSIONS = os.getenv("EXTENSIONS", "").split(",")

def get_sharepoint_content(token: str, topic: str, sharepoint_site: str, sharepoint_list: str, sharepoint_folder: str):
    base = "https://graph.microsoft.com/v1.0"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    # Drive for this list (document library)
    r = requests.get(f"{base}/sites/{sharepoint_site}/lists/{sharepoint_list}/drive",
                     headers=headers, timeout=30)
    r.raise_for_status()
    drive_id = r.json().get("id")  # looks like "b!ryfNTdR..."

    # Children of the folder: include parentReference + listItem.id
    url = (
        f"{base}/drives/{drive_id}/items/{sharepoint_folder}/children"
        "?$select=id,name,webUrl,size,lastModifiedDateTime,parentReference"
        "&$expand=listItem($select=id)"
    )
    resp = requests.get(url, headers=headers, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    items = []
    for child in data.get("value", []):
        name = child.get("name", "")
        if EXTENSIONS and not any(name.lower().endswith(ext) for ext in EXTENSIONS):
            continue

        parent_ref = child.get("parentReference") or {}
        items.append({
            "topic" : topic,
            "id": child.get("id", ""),                         # e.g. "01IRFFWM..."
            "driveId": parent_ref.get("driveId", ""),          # e.g. "b!ryfNTdR..."
            "listItemId": (child.get("listItem") or {}).get("id"),
            "parentId": parent_ref.get("id", ""),              # e.g. folder DriveItem ID
            "name": name,
            "webUrl": child.get("webUrl", ""),
            "size": child.get("size"),
            "lastModifiedDateTime": child.get("lastModifiedDateTime"),
        })
    
    return items

        
def download_sharepoint_file(token, manifest, items):
    files = []

    manifest_keys = {
        (str(m["drive_id"]), str(m["file_id"]))
        for m in manifest
        if m.get("drive_id") and m.get("file_id")
    }

    for item in items:
        parent_id = item.get("parentId")
        drive_id = item.get("driveId")
        item_id  = item.get("driveItemId") or item.get("id")
        file_name = item.get("fileName") or item.get("name")
        download_dir = ""

        if not drive_id or not item_id or not file_name or not parent_id:
            continue  # missing essentials; skip

        # Only .docx / .pdf
        fn_lower = file_name.lower()
        if not (fn_lower.endswith(".docx") or fn_lower.endswith(".pdf")):
            continue

        # Skip items already on manifest
        if (str(parent_id), str(item_id)) in manifest_keys:
            continue

        url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/content"
        headers = { "Authorization": f"Bearer {token}" }

        response = requests.get(url, headers=headers, stream=True)
        if response.status_code == 200:
            file_path = os.path.join(download_dir, file_name)
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            files.append({
                "path": file_path, 
                "itemName": file_name, 
                "folderId": parent_id,
                "itemId": item_id
            })
        else:
            pass

    return files

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
    list_items = get_sharepoint_content(sharepoint_token, topic, site, list_id, folder)
    logs.append("Remote metadata loaded")

    logs.append("Downloading differences")
    downloaded_files = download_sharepoint_file(sharepoint_token, man, list_items)
    logs.append(f"Downloaded {len(downloaded_files)} files")

    vectorize_and_upload_files(downloaded_files, topic, logs)

    logs.append("Registering changes to manifest...")
    manifest.upload_to_manifest(list_items, SOURCE)
    logs.append("Manifest updated")

    logs.append("Cleaning local information...")
    clean_files(downloaded_files, logs)
    logs.append("Local server cleaned")

    write_block(logs, "SH Sequence")