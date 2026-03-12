import streamlit as st
import requests
import json

# API base URL (local backend)
API_URL = "http://127.0.0.1:8000"

if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "question_count" not in st.session_state:
    st.session_state.question_count = 0
if "study_plan" not in st.session_state:
    st.session_state.study_plan = None
if "feedback" not in st.session_state:
    st.session_state.feedback = None  # For correct/incorrect after submit
if "show_next" not in st.session_state:
    st.session_state.show_next = False  # Control next button


def start_session():
    response = requests.post(f"{API_URL}/start_session")
    if response.status_code == 200:
        return response.json()["session_id"]
    else:
        st.error("Failed to start session. Check backend logs.")
        return None


def get_next_question(session_id):
    response = requests.get(f"{API_URL}/next_question/{session_id}")
    if response.status_code == 200:
        return response.json()
    else:
        st.error(response.json().get("detail", "Unknown error"))
        return None


def submit_answer(session_id, answer):
    response = requests.post(
        f"{API_URL}/submit_answer/{session_id}",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"answer": answer})
    )
    if response.status_code == 200:
        return response.json()
    else:
        st.error(response.json().get("detail", "Unknown error"))
        return None


def get_study_plan(session_id):
    response = requests.get(f"{API_URL}/study_plan/{session_id}")
    if response.status_code == 200:
        return response.json()["study_plan"]
    else:
        st.error(response.json().get("detail", "Unknown error"))
        return None


# Main UI
st.title("Adaptive Testing Prototype")

if st.session_state.session_id is None:
    st.session_state.session_id = start_session()
    if st.session_state.session_id:
        st.success(f"Session started: {st.session_state.session_id}")

if st.session_state.study_plan is None:
    if st.session_state.current_question is None:
        st.session_state.current_question = get_next_question(st.session_state.session_id)

    if st.session_state.current_question:
        q = st.session_state.current_question
        st.subheader(f"Question {st.session_state.question_count + 1}/10: {q['question_text']}")
        st.write(f"Topic: {q['topic']}")

        # Radio buttons for options
        options = list(q["options"].keys())
        selected = st.radio("Select your answer:", options, format_func=lambda x: f"{x}: {q['options'][x]}")

        if st.button("Submit Answer") and not st.session_state.show_next:
            result = submit_answer(st.session_state.session_id, selected)
            if result:
                st.session_state.feedback = {
                    "correct": result['correct'],
                    "new_ability": result['new_ability']
                }
                st.session_state.show_next = True  # Show next button
                st.rerun()  # Refresh to show feedback

        # Show feedback if available
        if st.session_state.feedback:
            st.write(f"Correct: {st.session_state.feedback['correct']}")
            st.write(f"Updated Ability: {st.session_state.feedback['new_ability']:.2f}")

        # Next button after feedback
        if st.session_state.show_next:
            if st.button("Next Question"):
                st.session_state.question_count += 1
                st.session_state.current_question = get_next_question(st.session_state.session_id)
                st.session_state.feedback = None
                st.session_state.show_next = False
                st.rerun()

        # Check for end
        if st.session_state.question_count >= 10:
            st.success("Test complete! Click below for recommendations.")
            if st.button("Get AI Recommendations"):
                st.session_state.study_plan = get_study_plan(st.session_state.session_id)
                st.rerun()
else:
    st.subheader("Test Complete! Personalized Study Plan:")
    st.write(st.session_state.study_plan)

if st.button("Restart Test"):
    st.session_state.session_id = None
    st.session_state.current_question = None
    st.session_state.question_count = 0
    st.session_state.study_plan = None
    st.session_state.feedback = None
    st.session_state.show_next = False
    st.rerun()