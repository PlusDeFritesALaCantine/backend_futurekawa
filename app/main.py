from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import pays, dashboard
from odoo.app.main import app as odoo_app

app = FastAPI(title="FutureKawa Backend — Siège", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pays.router)
app.include_router(dashboard.router)
app.mount("/odoo", odoo_app)

@app.get("/health")
def health():
    return {"status": "ok"}
