# main.py
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from datetime import datetime
import math
import requests

from models import FixtureView, LotoFootReq, ComboResp
from providers.odds_api import fetch_soccer_odds
from routes import fixtures_enriched
app.include_router(fixtures_enriched.router)

# --- Lecture clé RapidAPI depuis l'environnement (via settings si tu préfères)
import os
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY", "")
API_FOOTBALL_HOST = os.getenv("API_FOOTBALL_HOST", "api-football-v1.p.rapidapi.com")  # RapidAPI par défaut

app = FastAPI(title="Pronostics Backend (Real API - Value Edge)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------
# Utils
# --------------------------------------------------------------------
def _af_headers() -> Dict[str, str]:
    """Headers attendus par API-FOOTBALL via RapidAPI."""
    if not API_FOOTBALL_KEY:
        # On ne lève pas d'exception ici (pour /health), on laissera les routes /af/* gérer proprement
        return {}
    return {
        "X-RapidAPI-Key": API_FOOTBALL_KEY,
        "X-RapidAPI-Host": API_FOOTBALL_HOST,
    }

def _af_base() -> str:
    # RapidAPI = https://api-football-v1.p.rapidapi.com/v3
    return f"https://{API_FOOTBALL_HOST}/v3"

# --------------------------------------------------------------------
# Base
# --------------------------------------------------------------------
@app.get("/health")
def health():
    return {"ok": True}

@app.get("/fixtures", response_model=List[FixtureView])
def fixtures(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    competition_id: Optional[str] = None
):
    """
    Matchs issus de The Odds API (agrégés), avec filtre de dates optionnel.
    """
    items = fetch_soccer_odds()

    def within(d: str) -> bool:
        try:
            ts = datetime.fromisoformat(d.replace("Z", "+00:00"))
        except Exception:
            return True
        ok_from = True if not date_from else ts.date() >= datetime.fromisoformat(date_from).date()
        ok_to = True if not date_to else ts.date() <= datetime.fromisoformat(date_to).date()
        return ok_from and ok_to

    items = [it for it in items if within(it.utc_datetime)]
    if competition_id:
        items = [it for it in items if it.competition.id == competition_id]
    return items

@app.post("/lotofoot/combos", response_model=List[ComboResp])
def combos(req: LotoFootReq):
    """
    Beam search simple pour générer N meilleures combinaisons (1/N/2) sur K issues par match.
    """
    beams = [(0.0, [])]  # (logp, path)
    for m in req.matches:
        idx = sorted(range(3), key=lambda i: m.p[i], reverse=True)[:req.k]
        next_beams = []
        for logp, path in beams:
            for i in idx:
                next_beams.append((logp + math.log(m.p[i] + 1e-12), path + [i]))
        next_beams.sort(key=lambda x: x[0], reverse=True)
        beams = next_beams[:req.N]
    return [{"issues": path, "p": math.exp(logp)} for (logp, path) in beams[:req.N]]

# --------------------------------------------------------------------
# API-FOOTBALL (RapidAPI) — routes de test simples
# --------------------------------------------------------------------

@app.get("/af/status")
def af_status() -> Dict[str, Any]:
    """
    Vérifie rapidement ta clé/API. Ne consomme (quasiment) pas de quota.
    """
    if not API_FOOTBALL_KEY:
        raise HTTPException(status_code=503, detail="API_FOOTBALL_KEY manquante (Render > Environment).")
    url = _af_base() + "/status"
    r = requests.get(url, headers=_af_headers(), timeout=15)
    try:
        r.raise_for_status()
    except requests.HTTPError:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()

@app.get("/af/fixtures")
def af_fixtures(
    # On accepte les deux syntaxes: ?from=YYYY-MM-DD&to=YYYY-MM-DD ou ?date_from=&date_to=
    from_: Optional[str] = Query(None, alias="from"),
    to_: Optional[str] = Query(None, alias="to"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Liste brute des fixtures API-FOOTBALL entre 2 dates.
    Utile pour valider que tout est branché avant d'aller plus loin.
    """
    if not API_FOOTBALL_KEY:
        raise HTTPException(status_code=503, detail="API_FOOTBALL_KEY manquante (Render > Environment).")

    df = from_ or date_from
    dt = to_ or date_to
    if not df or not dt:
        raise HTTPException(status_code=400, detail="Paramètres manquants: utilisez ?from=YYYY-MM-DD&to=YYYY-MM-DD")

    url = _af_base() + "/fixtures"
    params = {"from": df, "to": dt}
    r = requests.get(url, headers=_af_headers(), params=params, timeout=25)
    try:
        r.raise_for_status()
    except requests.HTTPError:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    js = r.json()
    return js.get("response", [])
