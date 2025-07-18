import requests
import base64
from io import BytesIO
import pandas as pd

def fetch_anaplan_csv(username, password, workspace_id, model_id, file_id):
    auth_str = f"{username}:{password}"
    encoded_auth = base64.b64encode(auth_str.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_auth}",
        "Content-Type": "application/json"
    }

    url = f"https://api.anaplan.com/2/0/workspaces/{workspace_id}/models/{model_id}/files/{file_id}/chunks/0"

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        try:
            data = response.content
            return BytesIO(data)  # Can be passed to pd.read_csv or st.file_uploader-like use
        except Exception:
            return None
    return None
