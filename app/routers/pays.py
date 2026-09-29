"""Point d'entrée unique du front, relayé vers les API pays.

Le siège n'était jusqu'ici qu'un agrégateur en lecture : POST /lots et
DELETE /lots partaient du front vers lui et répondaient 404, parce qu'aucune
route en écriture n'existait. En production Kubernetes ça « marchait » parce
que l'ingress renvoyait discrètement ces chemins vers l'API pays — donc le
front écrivait en direct, contredisant l'architecture annoncée.

Ce module ferme l'écart : les écritures passent désormais par le siège, qui
les relaie en préservant le code de statut de l'API pays.
"""

from datetime import datetime
from typing import Any, Optional

import httpx
from fastapi import APIRouter, Body, HTTPException, Query, Response

from app.config import PAYS_URLS
from app.services.aggregator import fetch_alertes, fetch_lots, relayer

router = APIRouter(prefix="/pays", tags=["pays"])


def _get_url(pays: str) -> str:
    if pays not in PAYS_URLS:
        raise HTTPException(status_code=404, detail=f"Pays '{pays}' inconnu")
    return PAYS_URLS[pays]


async def _relais(pays: str, methode: str, chemin: str, *,
                  params: dict | None = None, corps: Any = None) -> Response | Any:
    """Relaie et traduit : indisponibilité -> 503, erreur métier -> code d'origine."""
    url = _get_url(pays) + chemin
    propres = {k: v for k, v in (params or {}).items() if v is not None}
    try:
        reponse = await relayer(methode, url, params=propres, json_body=corps)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail=f"API {pays} indisponible")

    if reponse.status_code == 204:
        return Response(status_code=204)
    if reponse.status_code >= 400:
        try:
            detail = reponse.json().get("detail", reponse.text)
        except ValueError:
            detail = reponse.text
        raise HTTPException(status_code=reponse.status_code, detail=detail)
    return reponse.json()


@router.get("")
async def lister_pays():
    return [{"nom": p, "url": url} for p, url in PAYS_URLS.items()]


# --- Lots : lecture et écriture ------------------------------------------

@router.get("/{pays}/lots")
async def lots_pays(pays: str):
    url = _get_url(pays)
    try:
        return await fetch_lots(url, pays)
    except Exception:
        raise HTTPException(status_code=503, detail=f"API {pays} indisponible")


@router.post("/{pays}/lots", status_code=201)
async def creer_lot(pays: str, lot: dict = Body(...)):
    """Le pays de l'URL fait foi : il n'est pas possible de créer un lot
    colombien en passant par l'API brésilienne."""
    return await _relais(pays, "POST", "/lots", corps={**lot, "pays": pays})


@router.patch("/{pays}/lots/{lot_id}")
async def modifier_lot(pays: str, lot_id: str, maj: dict = Body(...)):
    return await _relais(pays, "PATCH", f"/lots/{lot_id}", corps=maj)


@router.delete("/{pays}/lots/{lot_id}", status_code=204)
async def supprimer_lot(pays: str, lot_id: str):
    return await _relais(pays, "DELETE", f"/lots/{lot_id}")


@router.get("/{pays}/lots/{lot_id}/mesures")
async def mesures_du_lot(pays: str, lot_id: str):
    return await _relais(pays, "GET", f"/lots/{lot_id}/mesures")


# --- Mesures : paginées ---------------------------------------------------

@router.get("/{pays}/mesures")
async def mesures_pays(
    pays: str,
    entrepot_id: Optional[str] = None,
    lot_id: Optional[str] = None,
    debut: Optional[datetime] = None,
    fin: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """Relaie la pagination telle quelle. Le siège ne rapatrie plus tout
    l'historique d'un pays pour le retransmettre au navigateur."""
    return await _relais(pays, "GET", "/mesures", params={
        "entrepot_id": entrepot_id,
        "lot_id": lot_id,
        "debut": debut.isoformat() if debut else None,
        "fin": fin.isoformat() if fin else None,
        "limit": limit,
        "offset": offset,
    })


@router.get("/{pays}/mesures/latest")
async def dernieres_mesures(pays: str):
    """Un relevé par entrepôt, le plus récent.

    Évite aux pages qui n'ont besoin que de l'état courant (liste des lots,
    dashboard) de rapatrier tout l'historique du pays pour n'en garder qu'une
    ligne par entrepôt.
    """
    return await _relais(pays, "GET", "/mesures/latest")


# --- Alertes --------------------------------------------------------------

@router.get("/{pays}/alertes")
async def alertes_pays(pays: str):
    url = _get_url(pays)
    try:
        return await fetch_alertes(url, pays)
    except Exception:
        raise HTTPException(status_code=503, detail=f"API {pays} indisponible")


@router.get("/{pays}/alertes/journal")
async def journal_alertes(
    pays: str,
    statut: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    return await _relais(pays, "GET", "/alertes/journal", params={
        "statut": statut, "limit": limit, "offset": offset,
    })


@router.post("/{pays}/alertes/synchroniser")
async def synchroniser_alertes(pays: str):
    return await _relais(pays, "POST", "/alertes/synchroniser")


@router.patch("/{pays}/alertes/{alerte_id}/acquitter")
async def acquitter_alerte(pays: str, alerte_id: str, corps: dict | None = Body(None)):
    return await _relais(pays, "PATCH", f"/alertes/{alerte_id}/acquitter", corps=corps or {})


@router.patch("/{pays}/alertes/{alerte_id}/resoudre")
async def resoudre_alerte(pays: str, alerte_id: str):
    return await _relais(pays, "PATCH", f"/alertes/{alerte_id}/resoudre")


# --- Paramétrage ----------------------------------------------------------

@router.get("/{pays}/parametres")
async def lire_parametres(pays: str):
    return await _relais(pays, "GET", f"/parametres/pays/{pays}")


@router.patch("/{pays}/parametres")
async def modifier_parametres(pays: str, maj: dict = Body(...)):
    return await _relais(pays, "PATCH", f"/parametres/pays/{pays}", corps=maj)
