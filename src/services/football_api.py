import requests
from src.config.settings import FOOTBALL_API_KEY

BASE_URL = "https://v3.football.api-sports.io"


def get_today_fixtures():
    if not FOOTBALL_API_KEY:
        raise ValueError("FOOTBALL_API_KEY is not set")

    url = f"{BASE_URL}/fixtures"

    headers = {
        "x-apisports-key": FOOTBALL_API_KEY
    }

    params = {
        "timezone": "UTC"
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=10
    )
    response.raise_for_status()

    data = response.json()
    return data.get("response", [])


def get_fixtures_by_date(date: str):
    if not FOOTBALL_API_KEY:
        raise ValueError("FOOTBALL_API_KEY is not set")

    url = f"{BASE_URL}/fixtures"

    headers = {
        "x-apisports-key": FOOTBALL_API_KEY
    }

    params = {
        "date": date,
        "timezone": "UTC"
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=10
    )
    response.raise_for_status()

    data = response.json()
    return data.get("response", [])

def get_league_standings(league_id: int, season: int = 2024):
    if not FOOTBALL_API_KEY:
        raise ValueError("FOOTBALL_API_KEY is not set")

    url = f"{BASE_URL}/standings"

    headers = {
        "x-apisports-key": FOOTBALL_API_KEY
    }

    params = {
        "league": league_id,
        "season": season
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=10
    )
    response.raise_for_status()

    data = response.json()

    # ✅ SAFE CHECK 1
    if not data.get("response"):
        return []

    league = data["response"][0].get("league")
    if not league:
        return []

    standings = league.get("standings")
    if not standings:
        return []

    return standings[0]
