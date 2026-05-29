from fastapi import APIRouter, HTTPException
from app.config import PAYS_URLS
from app.services.aggregator import fetch_lots, fetch_mesures_latest, fetch_alertes, _get

router = APIRouter(prefix="/pays", tags=["pays"])


@router.get("")
async def lister_pays():
    return [{"nom": p, "url": url} for p, url in PAYS_URLS.items()]


@router.get("/{pays}/lots")
async def lots_pays(pays: str):
    url = _get_url(pays)
    try:
        return await fetch_lots(url)
    except Exception:
        raise HTTPException(status_code=503, detail=f"API {pays} indisponible")


@router.get("/{pays}/mesures")
async def mesures_pays(pays: str, entrepot_id: str | None = None):
    url = _get_url(pays)
    try:
        path = f"{url}/mesures"
        if entrepot_id:
            path += f"?entrepot_id={entrepot_id}"
        return await _get(path)
    except Exception:
        raise HTTPException(status_code=503, detail=f"API {pays} indisponible")


@router.get("/{pays}/alertes")
async def alertes_pays(pays: str):
    url = _get_url(pays)
    try:
        return await fetch_alertes(url)
    except Exception:
        raise HTTPException(status_code=503, detail=f"API {pays} indisponible")


def _get_url(pays: str) -> str:
    if pays not in PAYS_URLS:
        raise HTTPException(status_code=404, detail=f"Pays '{pays}' inconnu")
    return PAYS_URLS[pays]
