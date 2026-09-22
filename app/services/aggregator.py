import httpx
from typing import Any

TIMEOUT = 5.0


async def _get(url: str) -> Any:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.json()


async def fetch_lots(base_url: str, pays: str | None = None) -> list[dict]:
    url = f"{base_url}/lots"
    if pays:
        url += f"?pays={pays}"
    return await _get(url)


async def fetch_mesures_latest(base_url: str, pays: str | None = None) -> list[dict]:
    url = f"{base_url}/mesures/latest"
    if pays:
        url += f"?pays={pays}"
    return await _get(url)


async def fetch_alertes(base_url: str, pays: str | None = None) -> dict:
    url = f"{base_url}/alertes"
    if pays:
        url += f"?pays={pays}"
    return await _get(url)


async def fetch_pays_summary(pays: str, base_url: str) -> dict:
    try:
        lots = await fetch_lots(base_url, pays)
        alertes = await fetch_alertes(base_url, pays)
        latest = await fetch_mesures_latest(base_url, pays)

        derniere = latest[0] if latest else None
        nb_alertes = (
            len(alertes.get("lots_problematiques", []))
            + len(alertes.get("mesures_hors_seuil", []))
        )

        return {
            "nom": pays,
            "status": "ok",
            "nb_lots": len(lots),
            "nb_alertes": nb_alertes,
            "derniere_mesure": derniere,
        }
    except Exception:
        return {
            "nom": pays,
            "status": "indisponible",
            "nb_lots": None,
            "nb_alertes": None,
            "derniere_mesure": None,
        }


async def relayer(methode: str, url: str, *, params: dict | None = None,
                  json_body: Any = None) -> httpx.Response:
    """Relaie un appel vers une API pays et rend la réponse brute.

    Contrairement à `_get`, ne lève pas sur un statut d'erreur : c'est
    l'appelant qui décide quoi en faire. Un 409 « lot déjà existant » renvoyé
    par l'API pays doit arriver au front tel quel, pas déguisé en 503 —
    sinon l'utilisateur voit « pays indisponible » alors que le service
    répond parfaitement.
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        return await client.request(methode, url, params=params, json=json_body)
