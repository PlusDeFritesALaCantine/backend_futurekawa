import httpx
from typing import Any

TIMEOUT = 5.0


async def _get(url: str) -> Any:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.json()


async def fetch_lots(base_url: str) -> list[dict]:
    return await _get(f"{base_url}/lots")


async def fetch_mesures_latest(base_url: str) -> list[dict]:
    return await _get(f"{base_url}/mesures/latest")


async def fetch_alertes(base_url: str) -> dict:
    return await _get(f"{base_url}/alertes")


async def fetch_pays_summary(pays: str, base_url: str) -> dict:
    try:
        lots = await fetch_lots(base_url)
        alertes = await fetch_alertes(base_url)
        latest = await fetch_mesures_latest(base_url)

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
