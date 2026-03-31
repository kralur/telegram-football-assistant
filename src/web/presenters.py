def serialize_match(match: dict | None):
    if not match:
        return None

    return {
        "id": match.get("id"),
        "home": match.get("home"),
        "away": match.get("away"),
        "league_id": match.get("league_id"),
        "league": match.get("league"),
        "country": match.get("country"),
        "date": match.get("date"),
        "status": match.get("status"),
        "status_long": match.get("status_long"),
        "score": match.get("score"),
        "home_goals": match.get("home_goals"),
        "away_goals": match.get("away_goals"),
        "popularity_score": match.get("popularity_score", 0),
        "is_live": match.get("status") in {"1H", "2H", "HT", "ET", "P"},
        "is_finished": match.get("status") in {"FT", "AET", "PEN"},
    }


def serialize_matches(matches: list[dict]):
    return [serialize_match(match) for match in matches]


def serialize_favorite(item: dict):
    return {
        "user_id": item.get("user_id"),
        "team_id": item.get("team_id"),
        "team_name": item.get("team_name"),
        "next_match": serialize_match(item.get("next_match")),
        "last_match": serialize_match(item.get("last_match")),
    }


def serialize_favorites(items: list[dict]):
    return [serialize_favorite(item) for item in items]
