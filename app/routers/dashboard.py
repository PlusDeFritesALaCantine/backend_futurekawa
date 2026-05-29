import asyncio
from fastapi import APIRouter
from app.config import PAYS_URLS
from app.services.aggregator import fetch_pays_summary

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
async def dashboard():
    tasks = [fetch_pays_summary(pays, url) for pays, url in PAYS_URLS.items()]
    resultats = await asyncio.gather(*tasks)
    return {"pays": list(resultats)}
