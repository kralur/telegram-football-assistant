import requests
from datetime import datetime
from src.config.settings import FOOTBALL_API_KEY

BASE_URL = "https://v3.football.api-sports.io"


# -------------------------------------------------
# INTERNAL HELPER (ONE PLACE FOR ALL HTTP REQUESTS)
# -------------------------------------------------
def _get(endpoint: str, params: dict):
    if not FOOTBALL_API_KEY:
        raise ValueError("FOOTBALL_API_KEY is not set")

    headers = {
        "x-apisports-key": FOOTBALL_API_KEY
    }

    response = requests.get(
        f"{BASE_URL}{endpoint}",
        headers=headers,
        params=params,
        timeout=10
    )
    response.raise_for_status()
    return response.json()


# -------------------------------------------------
# MATCHES TODAY
# -------------------------------------------------
def get_today_fixtures():
    today = datetime.utcnow().strftime("%Y-%m-%d")

    data = _get(
        "/fixtures",
        {
            "date": today,
            "timezone": "UTC"
        }
    )

    return data.get("response", [])


# -------------------------------------------------
# MATCHES BY DATE
# -------------------------------------------------
def get_fixtures_by_date(date: str):
    data = _get(
        "/fixtures",
        {
            "date": date,
            "timezone": "UTC"
        }
    )

    return data.get("response", [])


# -------------------------------------------------
# LEAGUE STANDINGS
# -------------------------------------------------
def get_league_standings(league_id: int, season: int = 2024):
    data = _get(
        "/standings",
        {
            "league": league_id,
            "season": season
        }
    )

    if not data.get("response"):
        return []

    league = data["response"][0].get("league")
    if not league:
        return []

    standings = league.get("standings")
    if not standings:
        return []

    return standings[0]


# -------------------------------------------------
# GET TEAM ID BY TEAM NAME
# -------------------------------------------------
def get_team_id_by_name(team_name: str):
    data = _get(
        "/teams",
        {
            "search": team_name
        }
    )

    if not data.get("response"):
        return None

    return data["response"][0]["team"]["id"]


# -------------------------------------------------
# NEXT FIXTURES BY TEAM ID
# -------------------------------------------------
def get_next_fixtures_by_team_id(team_id: int, limit: int = 1):
    data = _get(
        "/fixtures",
        {
            "team": team_id,
            "next": limit,
            "timezone": "UTC"
        }
    )

    return data.get("response", [])
