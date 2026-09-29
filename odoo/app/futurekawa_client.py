"""Client HTTP vers backend_futurekawa (le "backend central siège", déjà déployé).

Client synchrone (httpx.Client, pas AsyncClient) : sync.py — et donc tout ce module —
tourne entièrement en synchrone, car les appels XML-RPC vers Odoo le sont de toute
façon (xmlrpc.client est bloquant). Le point d'entrée FastAPI (app/main.py) délègue
l'ensemble de run_sync() à un thread via asyncio.to_thread, comme le fait déjà
api_futurekawa pour sa propre boucle périodique — inutile de mélanger async/sync
à l'intérieur du pipeline lui-même.

Contrairement à backend_futurekawa/app/services/aggregator.py::fetch_pays_summary
(qui avale les exceptions pour dégrader gracieusement), les erreurs HTTP sont ici
laissées remonter : sync.py a besoin de l'exception brute pour distinguer un pays
indisponible d'une erreur de mapping, et pour construire un SyncReport détaillé.
"""

from __future__ import annotations

import httpx


class FuturekawaClient:
    def __init__(self, base_url: str, timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _get(self, path: str) -> object:
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(f"{self.base_url}{path}")
            response.raise_for_status()
            return response.json()

    def fetch_pays(self) -> list[dict]:
        return self._get("/pays")

    def fetch_lots(self, pays: str) -> list[dict]:
        return self._get(f"/pays/{pays}/lots")

    def fetch_alertes(self, pays: str) -> dict:
        return self._get(f"/pays/{pays}/alertes")

    def patch_lot(self, pays: str, lot_id: str, champs: dict) -> dict:
        """Remonte vers FutureKawa une correction faite dans Odoo.

        PATCH et non PUT : l'API pays fusionne les champs fournis (exclude_unset)
        au lieu de remplacer le lot. Envoyer un PUT partiel viderait les champs
        absents de la charge utile.
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.patch(
                f"{self.base_url}/pays/{pays}/lots/{lot_id}", json=champs
            )
            response.raise_for_status()
            return response.json()
