from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes.health import router as health_router
from app.api.routes.chat import router as chat_router

from app.api.routes.messenger import router as messenger_router

from app.api.routes.admin import router as admin_router

from app.api.routes.whatsapp_test import router as whatsapp_test_router

from app.api.routes.whatsapp_webhook import router as whatsapp_webhook_router


app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(chat_router)

app.include_router(messenger_router)

app.include_router(admin_router)


app.include_router(whatsapp_test_router)

app.include_router(whatsapp_webhook_router)

@app.get("/")
def root():
    return {"message": "FB Support Bot API is running"}
