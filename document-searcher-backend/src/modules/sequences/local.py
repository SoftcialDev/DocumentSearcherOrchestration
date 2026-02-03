from modules.sequences.helpers import vectorize_and_upload_files
from modules.logs import write_block

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