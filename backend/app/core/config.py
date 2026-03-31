import os
from dotenv import load_dotenv

load_dotenv()  # loads backend/.env

class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "fb-support-bot")
    ENV: str = os.getenv("ENV", "dev")

    FB_VERIFY_TOKEN: str = os.getenv("FB_VERIFY_TOKEN", "")
    FB_PAGE_ACCESS_TOKEN: str = os.getenv("FB_PAGE_ACCESS_TOKEN", "")
    FB_APP_SECRET: str = os.getenv("FB_APP_SECRET", "")


    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_JWT_AUD: str = os.getenv("SUPABASE_JWT_AUD", "authenticated")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")


    WHATSAPP_ACCESS_TOKEN: str = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    WHATSAPP_TEST_TO: str = os.getenv("WHATSAPP_TEST_TO", "")
    GRAPH_API_VERSION: str = os.getenv("GRAPH_API_VERSION", "v22.0")


    WHATSAPP_VERIFY_TOKEN: str = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
    WHATSAPP_APP_SECRET: str = os.getenv("WHATSAPP_APP_SECRET", "")  # same as Meta App Secret



settings = Settings()
