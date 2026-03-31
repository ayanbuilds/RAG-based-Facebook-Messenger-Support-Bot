import requests
from app.core.config import settings

GRAPH_URL = "https://graph.facebook.com/v19.0"

def fetch_fb_name(psid: str) -> str | None:
    token = settings.FB_PAGE_ACCESS_TOKEN
    if not token:
        return None

    r = requests.get(
        f"{GRAPH_URL}/{psid}",
        params={"fields": "name", "access_token": token},
        timeout=15,
    )
    # TEMP DEBUG
    print("FB PROFILE STATUS:", r.status_code)
    print("FB PROFILE RESPONSE:", r.text)

    if r.status_code >= 400:
        return None

    data = r.json()
    name = data.get("name")
    return name if isinstance(name, str) and name.strip() else None
