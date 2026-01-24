from openai import OpenAI
from src.config.settings import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def fallback_analysis(home: str, away: str, league: str, date: str) -> str:
    return (
        "📊 Предматчевый анализ (fallback)\n\n"
        f"Матч: {home} vs {away}\n"
        f"Лига: {league}\n"
        f"Дата: {date}\n\n"
        "Ожидается конкурентный матч.\n"
        "Ключевыми факторами могут стать форма команд, "
        "домашнее преимущество и реализация моментов.\n\n"
        "⚠️ AI-анализ временно недоступен из-за лимитов API."
    )


def analyze_match(home: str, away: str, league: str, date: str) -> str:
    prompt = (
        f"Give a short football match analysis.\n\n"
        f"Match: {home} vs {away}\n"
        f"League: {league}\n"
        f"Date: {date}\n\n"
        f"Focus on form, strengths, and expected outcome."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a football analyst."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200
        )

        return response.choices[0].message.content

    except Exception as e:
        # 👉 ЛЮБАЯ ошибка → fallback
        return fallback_analysis(home, away, league, date)
