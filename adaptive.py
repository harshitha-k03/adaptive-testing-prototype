import numpy as np
from scipy.optimize import minimize_scalar
from database import questions_collection, sessions_collection
from bson.objectid import ObjectId


def select_next_question(session_id: str):
    session = sessions_collection.find_one({"session_id": session_id})
    if not session:
        raise ValueError("Session not found")

    asked_ids = session.get("questions_asked", [])
    current_ability = session.get("current_ability", 0.5)

    # Fetch all available questions (small bank, efficient)
    all_questions = list(questions_collection.find())
    available = [q for q in all_questions if q["_id"] not in asked_ids]

    if not available:
        raise ValueError("No more questions available")

    # Select the one with difficulty closest to current ability
    best_question = min(available, key=lambda q: abs(q["difficulty"] - current_ability))
    return best_question


def update_ability(session_id: str) -> float:
    session = sessions_collection.find_one({"session_id": session_id})
    if not session:
        raise ValueError("Session not found")

    answers = session.get("answers", [])
    if not answers:
        return 0.5

    def neg_log_likelihood(theta: float) -> float:
        ll = 0.0
        for ans in answers:
            q = questions_collection.find_one({"_id": ObjectId(ans["question_id"])})
            if not q:
                raise ValueError("Question not found")
            b = q["difficulty"]
            p = 1 / (1 + np.exp(-(theta - b)))
            if ans["correct"]:
                ll += np.log(p + 1e-9)  # Avoid log(0)
            else:
                ll += np.log(1 - p + 1e-9)
        return -ll

    # Optimize (MLE) within bounds matching difficulty scale
    result = minimize_scalar(neg_log_likelihood, bounds=(0.0, 1.0), method="bounded")
    if not result.success:
        raise ValueError("Ability update failed")
    return float(result.x)