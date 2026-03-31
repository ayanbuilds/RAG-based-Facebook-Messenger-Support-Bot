import requests
from app.core.config import settings

GRAPH_URL = f"https://graph.facebook.com/{settings.GRAPH_API_VERSION}/me/messages"
# GRAPH_URL = "https://graph.facebook.com/v19.0/me/messages"

def send_text_message(psid: str, text: str) -> None:
    token = settings.FB_PAGE_ACCESS_TOKEN
    if not token:
        raise RuntimeError("FB_PAGE_ACCESS_TOKEN is missing")

    payload = {
        "recipient": {"id": psid},
        "message": {"text": text},
        "messaging_type": "RESPONSE"
    }

    r = requests.post(
        GRAPH_URL,
        params={"access_token": token},
        json=payload,
        timeout=15
    )
    if r.status_code >= 400:
        raise RuntimeError(f"Send API error {r.status_code}: {r.text}")
