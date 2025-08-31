import os
from dotenv import load_dotenv
load_dotenv()

ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
ODDS_API_REGION = os.getenv("ODDS_API_REGION", "eu")  # eu, uk, us, au
ODDS_API_MARKETS = os.getenv("ODDS_API_MARKETS", "h2h")
SOCCER_SPORT_KEYS = os.getenv("SOCCER_SPORT_KEYS", ",".join([
    "soccer_epl",
    "soccer_france_ligue_one",
    "soccer_spain_la_liga",
    "soccer_italy_serie_a",
    "soccer_germany_bundesliga",
    "soccer_uefa_champs_league",
    "soccer_uefa_europa_league"
]))
BASE_URL = "https://api.the-odds-api.com/v4"
