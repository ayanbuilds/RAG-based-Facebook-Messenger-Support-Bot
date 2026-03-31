import requests
from app.core.config import settings

def send_whatsapp_text(to: str, text: str) -> None:
    url = f"https://graph.facebook.com/{settings.GRAPH_API_VERSION}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }

    r = requests.post(url, headers=headers, json=payload, timeout=15)
    # if r.status_code >= 400:
    #     raise RuntimeError(f"WhatsApp send failed {r.status_code}: {r.text}")

    try:
        data = r.json()
    except Exception:
        data = {"raw": r.text}

    return {"status_code": r.status_code, "response": data}