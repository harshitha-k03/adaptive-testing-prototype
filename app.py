import uuid
from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel
from database import sessions_collection, questions_collection
from adaptive import select_next_question, update_ability
from llm import generate_study_plan
from bson.objectid import ObjectId
from collections import Counter
from typing import Dict, Any

app = FastAPI(title="Adaptive Testing Prototype")


class SubmitAnswer(BaseModel):
    answer: str


@app.post("/start_session", response_model=Dict[str, str])
def start_session():
    session_id = str(uuid.uuid4())
    session = {
        "session_id": session_id,
        "current_ability": 0.5,
        "answers": [],
        "questions_asked": []
    }
    sessions_collection.insert_one(session)
    return {"session_id": session_id}


@app.get("/next_question/{session_id}", response_model=Dict[str, Any])
def get_next_question(session_id: str = Path(..., description="Session ID")):
    session = sessions_collection.find_one({"session_id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if len(session["questions_asked"]) >= 10:
        raise HTTPException(status_code=400, detail="Test has ended. Use /study_plan")

    try:
        question = select_next_question(session_id)
        sessions_collection.update_one(
            {"session_id": session_id},
            {"$push": {"questions_asked": question["_id"]}}
        )
        # Return question without correct_answer or _id
        question_out = {
            "question_text": question["question_text"],
            "options": question["options"],
            "difficulty": question["difficulty"],
            "topic": question["topic"]
        }
        return question_out
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/submit_answer/{session_id}", response_model=Dict[str, Any])
def submit_answer(session_id: str = Path(..., description="Session ID"), body: SubmitAnswer = None):
    session = sessions_collection.find_one({"session_id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session["questions_asked"]:
        raise HTTPException(status_code=400, detail="No question asked yet")

    last_question_id = session["questions_asked"][-1]
    question = questions_collection.find_one({"_id": last_question_id})
    if not question:
        raise HTTPException(status_code=500, detail="Question not found")

    correct = body.answer.upper() == question["correct_answer"].upper()
    answer_record = {
        "question_id": str(last_question_id),
        "response": body.answer,
        "correct": correct
    }
    sessions_collection.update_one(
        {"session_id": session_id},
        {"$push": {"answers": answer_record}}
    )

    try:
        new_ability = update_ability(session_id)
        sessions_collection.update_one(
            {"session_id": session_id},
            {"$set": {"current_ability": new_ability}}
        )
        return {"correct": correct, "new_ability": new_ability}
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/study_plan/{session_id}", response_model=Dict[str, str])
def get_study_plan(session_id: str = Path(..., description="Session ID")):
    session = sessions_collection.find_one({"session_id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if len(session["answers"]) < 10:
        raise HTTPException(status_code=400, detail="Complete the test first (10 questions)")

    # Collect missed topics
    missed_topics = []
    for answer in session["answers"]:
        if not answer["correct"]:
            q_id = ObjectId(answer["question_id"])
            question = questions_collection.find_one({"_id": q_id})
            if question:
                missed_topics.append(question["topic"])

    missed_counter = Counter(missed_topics).most_common()
    final_ability = session["current_ability"]

    try:
        plan = generate_study_plan(missed_counter, final_ability)
        return {"study_plan": plan}
    except ValueError as e:
        return {"study_plan": "Error generating plan: fallback message here."}  # Graceful fallback