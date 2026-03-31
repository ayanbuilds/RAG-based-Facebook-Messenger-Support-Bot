from fastapi import APIRouter
from app.core.config import settings
from app.services.whatsapp_send import send_whatsapp_text

router = APIRouter(prefix="/api/debug", tags=["debug"])

@router.post("/whatsapp-send")
def whatsapp_send():
    if not settings.WHATSAPP_TEST_TO:
        return {"ok": False, "error": "WHATSAPP_TEST_TO missing"}
    # send_whatsapp_text(settings.WHATSAPP_TEST_TO, "Hello from backend (WhatsApp test).")
    # return {"ok": True}
    result = send_whatsapp_text(settings.WHATSAPP_TEST_TO, "AYAN, Hello from backend (WhatsApp test).")
    return {"ok": True, "meta": result}
