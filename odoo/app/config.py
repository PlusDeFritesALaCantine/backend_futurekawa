import os

from dotenv import load_dotenv

load_dotenv()


def _bool_env(name: str, default: str) -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


# Instance Odoo cible (URL sans slash final, ex. https://futurekawa.odoo.com).
ODOO_URL = os.getenv("ODOO_URL", "")
ODOO_DB = os.getenv("ODOO_DB", "")
ODOO_USERNAME = os.getenv("ODOO_USERNAME", "")
# Clé API Odoo (Réglages > Utilisateurs > Clés API) — jamais le mot de passe du compte.
ODOO_API_KEY = os.getenv("ODOO_API_KEY", "")
ODOO_TIMEOUT_SECONDS = float(os.getenv("ODOO_TIMEOUT_SECONDS", "10"))

# Si vrai, aucune écriture n'est effectuée dans Odoo (create/write/message_post/
# activity_schedule sont journalisés mais jamais appelés).
ODOO_DRY_RUN = _bool_env("ODOO_DRY_RUN", "false")

# Référence du produit Odoo représentant le café vert FutureKawa (product.product.default_code).
ODOO_DEFAULT_PRODUCT_DEFAULT_CODE = os.getenv("ODOO_DEFAULT_PRODUCT_DEFAULT_CODE", "CAFE-VERT")

# Login de l'utilisateur Odoo à qui assigner les activités planifiées sur alerte critique.
# Si vide, les alertes sont notées dans le chatter mais aucune activité n'est planifiée.
ODOO_ACTIVITY_USER_LOGIN = os.getenv("ODOO_ACTIVITY_USER_LOGIN", "")

# Backend central siège (déjà déployé, lecture seule depuis ce service).
BACKEND_FUTUREKAWA_URL = os.getenv("BACKEND_FUTUREKAWA_URL", "http://backend_futurekawa:8002")
BACKEND_FUTUREKAWA_TIMEOUT_SECONDS = float(os.getenv("BACKEND_FUTUREKAWA_TIMEOUT_SECONDS", "5"))

# Fréquence de la boucle de synchronisation périodique.
SYNC_INTERVAL_SECONDS = int(os.getenv("SYNC_INTERVAL_SECONDS", "300"))

API_PORT = int(os.getenv("API_PORT", "8003"))
