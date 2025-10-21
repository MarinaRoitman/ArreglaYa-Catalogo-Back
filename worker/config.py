# api/worker/config.py
import os
from dotenv import load_dotenv

load_dotenv()

def get_api_base_url():
    env = os.getenv("ENV", "local").lower()
    if env == "prod":
        return os.getenv("API_URL_PROD")
    return os.getenv("API_URL_LOCAL")
