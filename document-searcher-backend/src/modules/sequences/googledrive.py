import pathlib, requests, os

def download_google_file(access_token: str, folder_id: str, dest_dir: str = "./downloads"):
    DRIVE_LIST  = "https://www.googleapis.com/drive/v3/files"
    DRIVE_GET   = "https://www.googleapis.com/drive/v3/files/{id}"
    DRIVE_EXPORT= "https://www.googleapis.com/drive/v3/files/{id}/export"

    # Export Google-native files to these formats
    EXPORT_MAP = {
        "application/vnd.google-apps.document": ("application/pdf", ".pdf"),       # Docs → PDF
        "application/vnd.google-apps.spreadsheet": ("text/csv", ".csv"),          # Sheets → CSV
        "application/vnd.google-apps.presentation": ("application/pdf", ".pdf"),  # Slides → PDF
    }

    os.makedirs(dest_dir, exist_ok=True)
    headers = {"Authorization": f"Bearer {access_token}"}

    # List items in the folder (top level only)
    params = {
        "q": f"'{folder_id}' in parents and trashed=false",
        "fields": "nextPageToken, files(id,name,mimeType)",
        "includeItemsFromAllDrives": "true",
        "supportsAllDrives": "true",
        "pageSize": 1000,
    }

    total = 0
    page_token = None
    while True:
        if page_token:
            params["pageToken"] = page_token
        r = requests.get(DRIVE_LIST, headers=headers, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()

        for f in data.get("files", []):
            fid, name, mt = f["id"], f["name"], f.get("mimeType", "")
            # Skip subfolders; this function is non-recursive
            if mt == "application/vnd.google-apps.folder":
                continue

            # Google-native files → export
            if mt in EXPORT_MAP:
                export_mime, suffix = EXPORT_MAP[mt]
                out = pathlib.Path(dest_dir) / (name if name.lower().endswith(suffix) else name + suffix)
                with requests.get(
                    DRIVE_EXPORT.format(id=fid),
                    headers=headers,
                    params={"mimeType": export_mime},
                    stream=True,
                    timeout=60,
                ) as resp:
                    resp.raise_for_status()
                    with open(out, "wb") as fh:
                        for chunk in resp.iter_content(8192):
                            if chunk: fh.write(chunk)
                total += 1
                continue

            # Regular binary files → download
            out = pathlib.Path(dest_dir) / name
            with requests.get(
                DRIVE_GET.format(id=fid),
                headers=headers,
                params={"alt": "media", "supportsAllDrives": "true"},
                stream=True,
                timeout=60,
            ) as resp:
                resp.raise_for_status()
                with open(out, "wb") as fh:
                    for chunk in resp.iter_content(8192):
                        if chunk: fh.write(chunk)
            total += 1

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    return total

def start_googledrive_sequence():
    SOURCE = "SHAREPOINT"
    logs = []
    
    # googledrive_token = auth.get_sharepoint_token(logs)
    
    return
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