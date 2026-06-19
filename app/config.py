import os
from dotenv import load_dotenv

load_dotenv()

PAYS_URLS: dict[str, str] = {
    "bresil": os.getenv("BRESIL_API_URL", "http://api_futurekawa:8001"),
    "equateur": os.getenv("EQUATEUR_API_URL", "http://equateur-api:8001"),
    "colombie": os.getenv("COLOMBIE_API_URL", "http://colombie-api:8001"),
}
