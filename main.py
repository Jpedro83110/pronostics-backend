from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime
import math
from models import FixtureView, LotoFootReq, ComboResp
from providers.odds_api import fetch_soccer_odds

app = FastAPI(title="Pronostics Backend (Real API - Value Edge)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/fixtures", response_model=List[FixtureView])
def fixtures(date_from: Optional[str] = Query(None), date_to: Optional[str] = Query(None), competition_id: Optional[str] = None):
    items = fetch_soccer_odds()
    # Optional date filtering
    def within(d):
        try:
            ts = datetime.fromisoformat(d.replace("Z","+00:00"))
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
