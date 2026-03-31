from datetime import datetime
from zoneinfo import ZoneInfo


def format_datetime(value: str | None, timezone: str = "UTC"):
    if not value:
        return "TBD"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        local_dt = dt.astimezone(ZoneInfo(timezone))
        return local_dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return value


def main_menu_text(timezone: str, user_label: str | None = None):
    greeting = f"Welcome, {user_label}!\n\n" if user_label else ""
    return (
        "Football Assistant\n\n"
        f"{greeting}"
        "Choose what you want to open from the menu below.\n"
        f"Current timezone: {timezone}"
    )


def help_text():
    return (
        "How to use the bot\n\n"
        "1. Open Today's matches or Live to browse fixtures.\n"
        "2. Tap Notify under a match to schedule a reminder 15 minutes before kickoff.\n"
        "3. Open Search to find a team and add it to favorites.\n"
        "4. Favorites are used by the scheduler to keep upcoming reminders in sync.\n"
        "5. Set your timezone so all displayed times are local for you."
    )


def matches_text(title: str, matches: list[dict], timezone: str, page: int, total_pages: int):
    if not matches:
        return f"{title}\n\nNo data available right now."

    lines = [f"{title} ({page + 1}/{total_pages})", ""]
    for index, match in enumerate(matches, start=1):
        score = f"  {match['score']}" if match.get("score") and match["score"] != "-" else ""
        status = match.get("status_long", "Unknown")
        league_line = match["league"]
        if match.get("country") and match["country"] != "Unknown country":
            league_line = f"{match['country']} - {match['league']}"

        lines.append(f"[{index}] {match['home']} vs {match['away']}{score}")
        lines.append(f"League: {league_line}")
        lines.append(f"Time: {format_datetime(match.get('date'), timezone)} | {status}")
        lines.append("")
    return "\n".join(lines).strip()


def match_card_text(title: str, match: dict | None, timezone: str, page: int, total_pages: int):
    if not match:
        return f"{title}\n\nNo data available right now."

    score = f" {match['score']}" if match.get("score") and match["score"] != "-" else ""
    league_line = match["league"]
    if match.get("country") and match["country"] != "Unknown country":
        league_line = f"{match['country']} - {match['league']}"

    return (
        f"{title} ({page + 1}/{total_pages})\n\n"
        f"{match['home']} vs {match['away']}{score}\n"
        f"League: {league_line}\n"
        f"Time: {format_datetime(match.get('date'), timezone)} | {match.get('status_long', 'Unknown')}"
    )


def standings_text(league_name: str, rows: list[dict], page: int, total_pages: int):
    if not rows:
        return f"{league_name}\n\nStandings are unavailable right now."

    lines = [f"{league_name} ({page + 1}/{total_pages})", ""]
    for row in rows:
        lines.append(f"{row['rank']}. {row['team']} - {row['points']} pts ({row['played']} played)")
    return "\n".join(lines)


def scorers_text(league_name: str, rows: list[dict], page: int, total_pages: int):
    if not rows:
        return f"{league_name}\n\nTop scorers are unavailable right now."

    lines = [f"{league_name} ({page + 1}/{total_pages})", ""]
    for row in rows:
        lines.append(f"{row['player']} ({row['team']}) - {row['goals']} goals")
    return "\n".join(lines)


def search_prompt_text():
    return "Search mode\n\nSend a team name in the chat. The bot will update this screen with results."


def search_results_text(query: str, results: list[dict], page: int, total_pages: int):
    if not results:
        return f"Search results for '{query}'\n\nNothing found."

    lines = [f"Search results for '{query}' ({page + 1}/{total_pages})", ""]
    for team in results:
        lines.append(f"{team['name']} ({team['country']})")
    lines.append("")
    lines.append("Tap a button below to add a team to favorites.")
    return "\n".join(lines)


def favorites_text(favorites: list[dict], pending_count: int, timezone: str, page: int, total_pages: int):
    lines = [f"Favorites ({page + 1}/{total_pages})", ""]
    if not favorites:
        lines.append("No favorite teams yet.")
        lines.append("Use Search to add a team.")
    else:
        for index, team in enumerate(favorites, start=1):
            lines.append(f"{index}. {team['team_name']}")
            next_match = team.get("next_match")
            last_match = team.get("last_match")
            if next_match:
                lines.append(
                    "Next: "
                    f"{next_match['home']} vs {next_match['away']} "
                    f"({format_datetime(next_match.get('date'), timezone)})"
                )
            else:
                lines.append("Next: unavailable")
            if last_match:
                lines.append(
                    "Last: "
                    f"{last_match['home']} vs {last_match['away']} "
                    f"{last_match.get('score', '-')}"
                )
            lines.append("")
    lines.append("")
    lines.append(f"Pending notifications: {pending_count}")
    lines.append(f"Timezone: {timezone}")
    return "\n".join(lines)


def timezone_text(current_timezone: str):
    current_time = datetime.now(ZoneInfo(current_timezone)).strftime("%Y-%m-%d %H:%M")
    return (
        "Timezone settings\n\n"
        f"Current timezone: {current_timezone}\n"
        f"Current local time: {current_time}\n\n"
        "Choose the timezone you want to use for match times and reminders."
    )


def notification_added_text(match: dict, timezone: str):
    return (
        "Notification scheduled\n\n"
        f"{match['home']} vs {match['away']}\n"
        f"{match['league']}\n"
        f"Kickoff: {format_datetime(match.get('date'), timezone)} ({timezone})\n\n"
        "You will receive a reminder 15 minutes before kickoff."
    )


def notification_unavailable_text():
    return (
        "Notification could not be scheduled.\n\n"
        "This match may have already started or the API did not return a valid kickoff time."
    )


def service_error_text(message: str):
    return (
        "Data is temporarily unavailable\n\n"
        f"{message}\n\n"
        "You can go back or return to the main menu."
    )


def match_details_text(match: dict, timezone: str):
    league_line = match["league"]
    if match.get("country") and match["country"] != "Unknown country":
        league_line = f"{match['country']} - {match['league']}"
    return (
        "Match details\n\n"
        f"{match['home']} vs {match['away']}\n"
        f"League: {league_line}\n"
        f"Kickoff: {format_datetime(match.get('date'), timezone)} ({timezone})\n"
        f"Status: {match.get('status_long', 'Unknown')}\n"
        f"Score: {match.get('score', '-')}"
    )


def analysis_text(match: dict, analysis: str, timezone: str):
    league_line = match["league"]
    if match.get("country") and match["country"] != "Unknown country":
        league_line = f"{match['country']} - {match['league']}"
    return (
        "AI match analysis\n\n"
        f"{match['home']} vs {match['away']}\n"
        f"{league_line}\n"
        f"Kickoff: {format_datetime(match.get('date'), timezone)} ({timezone})\n\n"
        f"{analysis}"
    )


def daily_summary_text(matches: list[dict], timezone: str):
    lines = [f"Today's matches ({timezone})", ""]
    for match in matches[:5]:
        lines.append(f"{match['home']} vs {match['away']}")
        lines.append(match["league"])
        lines.append(format_datetime(match["date"], timezone))
        lines.append("")
    return "\n".join(lines).strip()


def reminder_text(match: dict, timezone: str):
    kickoff = format_datetime(match["date"], timezone)
    return (
        "Match reminder\n\n"
        f"{match['home']} vs {match['away']}\n"
        f"{match['league']}\n"
        f"Kickoff: {kickoff} ({timezone})"
    )
