import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


def generate_study_plan(missed_topics: list, final_ability: float) -> str:
    missed_str = ", ".join([f"{topic} ({count} misses)" for topic, count in missed_topics])
    prompt = (
        f"Based on the student's performance: missed topics include {missed_str}, "
        f"and final difficulty level reached is {final_ability:.2f}. "
        "Generate a concise 3-step study plan tailored to their specific weaknesses."
    )

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",  # Valid model - free tier, text handling
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        if "quota" in str(e).lower() or "limit" in str(e).lower():
            return (
                "Gemini quota issue. Fallback plan:\n"
                "1. Review missed topics like Vocabulary (focus on synonyms/antonyms).\n"
                "2. Practice Algebra/Geometry at your level ({final_ability:.2f}).\n"
                "3. Retake after 1 week to improve."
            )
        else:
            raise ValueError(f"LLM error: {str(e)}")