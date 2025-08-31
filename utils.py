from typing import Tuple, List
import statistics

def implied_probs_from_odds(o1: float, ox: float, o2: float) -> Tuple[float, float, float]:
    inv = [1.0/o if o and o>0 else 0.0 for o in (o1, ox, o2)]
    s = sum(inv) or 1.0
    p = [x/s for x in inv]
    return p[0], p[1], p[2]

def consensus_probs(prices_home: List[float], prices_draw: List[float], prices_away: List[float]) -> Tuple[float, float, float]:
    # Use median prices to reduce outliers, then normalize implied probs
    if not prices_home or not prices_draw or not prices_away:
        return 0.0, 0.0, 0.0
    m_home = statistics.median(prices_home)
    m_draw = statistics.median(prices_draw)
    m_away = statistics.median(prices_away)
    return implied_probs_from_odds(m_home, m_draw, m_away)
