from pydantic import BaseModel
from typing import Optional, List

class Competition(BaseModel):
    id: str
    name: str
    country: Optional[str] = None

class Odds1X2(BaseModel):
    home: float
    draw: float
    away: float

class Probas1X2(BaseModel):
    p_home: float
    p_draw: float
    p_away: float

class FixtureView(BaseModel):
    id: str
    competition: Competition
    utc_datetime: str
    home: str
    away: str
    probas: Probas1X2  # consensus probs (median across books), normalized
    odds: Odds1X2     # best price per outcome across books

class MatchCombo(BaseModel):
    id: str
    p: List[float]  # [p1, px, p2]

class LotoFootReq(BaseModel):
    matches: List[MatchCombo]
    k: int = 2
    N: int = 50

class ComboResp(BaseModel):
    issues: List[int]
    p: float
