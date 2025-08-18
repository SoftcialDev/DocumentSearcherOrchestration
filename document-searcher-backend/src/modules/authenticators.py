import msal
import requests
import os
import logging

# Sharepoint authentication
SHAREPOINT_ENTRA_SECRET_VALUE = os.getenv("SHAREPOINT_ENTRA_SECRET_VALUE")
SHAREPOINT_ENTRA_CLIENT_ID = os.getenv("SHAREPOINT_ENTRA_CLIENT_ID")

# Onedrive authentication
ONEDRIVE_ENTRA_SECRET_VALUE = os.getenv("ONEDRIVE_ENTRA_SECRET_VALUE")
ONEDRIVE_ENTRA_TENANT_ID = os.getenv("ONEDRIVE_ENTRA_TENANT_ID")
ONEDRIVE_ENTRA_CLIENT_ID = os.getenv("ONEDRIVE_ENTRA_CLIENT_ID")

# Graph Authentication
GRAPH_TOKEN_ENDPOINT = os.getenv("GRAPH_TOKEN_ENDPOINT")

def get_sharepoint_token():

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    body = {
        "client_id": SHAREPOINT_ENTRA_CLIENT_ID,
        "scope": "https://graph.microsoft.com/.default",
        "client_secret": SHAREPOINT_ENTRA_SECRET_VALUE,
        "grant_type": "client_credentials"
    }

    try:
        response = requests.post(GRAPH_TOKEN_ENDPOINT, headers=headers, data=body)
        response.raise_for_status()
        token = response.json()["access_token"]
        return token
    except requests.exceptions.RequestException as e:
        logging.exception("Token request failed:", e)
        return None
    
def get_onedrive_token():

    AUTHORITY = f"https://login.microsoftonline.com/{ONEDRIVE_ENTRA_TENANT_ID}"
    SCOPE = ["https://graph.microsoft.com/.default"]  # Application permission scope

    app = msal.ConfidentialClientApplication(
        ONEDRIVE_ENTRA_CLIENT_ID,
        authority=AUTHORITY,
        client_credential=ONEDRIVE_ENTRA_SECRET_VALUE
    )

    result = app.acquire_token_for_client(scopes=SCOPE)

    if "access_token" in result:
        token = result["access_token"]
        return token
    else:
        logging.error("Failed to get token:", result.get("error_description"))
        return None