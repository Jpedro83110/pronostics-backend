import requests
from typing import List, Dict, Any
from ..models import FixtureView, Competition, Odds1X2, Probas1X2
from ..settings import ODDS_API_KEY, ODDS_API_REGION, ODDS_API_MARKETS, SOCCER_SPORT_KEYS, BASE_URL
from ..utils import implied_probs_from_odds, consensus_probs

HEADERS = {"Accept": "application/json"}

def fetch_soccer_odds() -> List[FixtureView]:
    if not ODDS_API_KEY:
        raise RuntimeError("ODDS_API_KEY missing. Create a .env with your key.")
    fixtures: List[FixtureView] = []
    sport_keys = [s.strip() for s in SOCCER_SPORT_KEYS.split(",") if s.strip()]
    for sport in sport_keys:
        url = f"{BASE_URL}/sports/{sport}/odds"
        params = {
            "apiKey": ODDS_API_KEY,
            "regions": ODDS_API_REGION,
            "markets": ODDS_API_MARKETS,
            "oddsFormat": "decimal"
        }
        r = requests.get(url, headers=HEADERS, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        for ev in data:
            prices_home, prices_draw, prices_away = [], [], []
            best_home, best_draw, best_away = 0.0, 0.0, 0.0

            hm_name = ev.get("home_team")
            aw_name = ev.get("away_team")

            for bk in ev.get("bookmakers", []):
                for mk in bk.get("markets", []):
                    if mk.get("key") != "h2h":
                        continue
                    outs = mk.get("outcomes", [])
                    # The Odds API names can be exact team names or generic "Home Team"/"Away Team"
                    price_home = None
                    price_draw = None
                    price_away = None
                    for oc in outs:
                        nm = oc.get("name")
                        pr = oc.get("price")
                        if pr is None:
                            continue
                        if nm == "Draw":
                            price_draw = float(pr)
                        elif nm == hm_name or nm == "Home Team":
                            price_home = float(pr)
                        elif nm == aw_name or nm == "Away Team":
                            price_away = float(pr)
                    if price_home: 
                        prices_home.append(price_home); best_home = max(best_home, price_home)
                    if price_draw: 
                        prices_draw.append(price_draw); best_draw = max(best_draw, price_draw)
                    if price_away: 
                        prices_away.append(price_away); best_away = max(best_away, price_away)

            # Need complete triad
            if not (prices_home and prices_draw and prices_away):
                continue

            # CONSENSUS probabilities (median prices across books), normalized
            p1, px, p2 = consensus_probs(prices_home, prices_draw, prices_away)

            comp = Competition(id=sport.upper(), name=ev.get("sport_title", sport), country=None)
            fixtures.append(FixtureView(
                id=str(ev.get("id")),
                competition=comp,
                utc_datetime=ev.get("commence_time"),
                home=hm_name,
                away=aw_name,
                probas=Probas1X2(p_home=p1, p_draw=px, p_away=p2),   # consensus
                odds=Odds1X2(home=best_home, draw=best_draw, away=best_away),  # best
            ))
    return fixtures
