from datetime import UTC, datetime, timedelta


def _future_iso(hours_from_now: int):
    return (datetime.now(UTC) + timedelta(hours=hours_from_now)).isoformat()


def featured_matches():
    return [
        {
            "id": 900001,
            "home": "Real Madrid",
            "away": "Barcelona",
            "league_id": 140,
            "league": "La Liga",
            "country": "Spain",
            "date": _future_iso(4),
            "status": "NS",
            "status_long": "Featured schedule",
            "score": "-",
            "home_goals": None,
            "away_goals": None,
            "popularity_score": 140,
            "is_live": False,
            "is_finished": False,
        },
        {
            "id": 900002,
            "home": "Manchester City",
            "away": "Arsenal",
            "league_id": 39,
            "league": "Premier League",
            "country": "England",
            "date": _future_iso(7),
            "status": "NS",
            "status_long": "Featured schedule",
            "score": "-",
            "home_goals": None,
            "away_goals": None,
            "popularity_score": 132,
            "is_live": False,
            "is_finished": False,
        },
        {
            "id": 900003,
            "home": "Bayern Munich",
            "away": "Borussia Dortmund",
            "league_id": 78,
            "league": "Bundesliga",
            "country": "Germany",
            "date": _future_iso(10),
            "status": "NS",
            "status_long": "Featured schedule",
            "score": "-",
            "home_goals": None,
            "away_goals": None,
            "popularity_score": 122,
            "is_live": False,
            "is_finished": False,
        },
        {
            "id": 900004,
            "home": "Inter",
            "away": "Juventus",
            "league_id": 135,
            "league": "Serie A",
            "country": "Italy",
            "date": _future_iso(13),
            "status": "NS",
            "status_long": "Featured schedule",
            "score": "-",
            "home_goals": None,
            "away_goals": None,
            "popularity_score": 118,
            "is_live": False,
            "is_finished": False,
        },
        {
            "id": 900005,
            "home": "PSG",
            "away": "Marseille",
            "league_id": 61,
            "league": "Ligue 1",
            "country": "France",
            "date": _future_iso(16),
            "status": "NS",
            "status_long": "Featured schedule",
            "score": "-",
            "home_goals": None,
            "away_goals": None,
            "popularity_score": 110,
            "is_live": False,
            "is_finished": False,
        },
    ]


def featured_standings(league: dict):
    templates = {
        39: [
            {"rank": 1, "team": "Arsenal", "points": 76, "played": 30},
            {"rank": 2, "team": "Liverpool", "points": 74, "played": 30},
            {"rank": 3, "team": "Manchester City", "points": 70, "played": 30},
            {"rank": 4, "team": "Tottenham", "points": 61, "played": 30},
        ],
        140: [
            {"rank": 1, "team": "Real Madrid", "points": 78, "played": 30},
            {"rank": 2, "team": "Barcelona", "points": 72, "played": 30},
            {"rank": 3, "team": "Atletico Madrid", "points": 65, "played": 30},
            {"rank": 4, "team": "Athletic Club", "points": 57, "played": 30},
        ],
    }
    return templates.get(
        league["id"],
        [
            {"rank": 1, "team": "Top Club", "points": 70, "played": 30},
            {"rank": 2, "team": "Second Club", "points": 66, "played": 30},
            {"rank": 3, "team": "Third Club", "points": 60, "played": 30},
            {"rank": 4, "team": "Fourth Club", "points": 56, "played": 30},
        ],
    )
