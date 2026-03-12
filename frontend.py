import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"


def api_post(url, data=None):
    r = requests.post(url, json=data)
    if r.status_code != 200:
        st.error(r.json().get("detail", "API Error"))
        return None
    return r.json()


def api_get(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()


st.title("Adaptive Diagnostic Engine")


# -----------------------
# Session Initialization
# -----------------------

if "session_id" not in st.session_state:

    session = api_post(f"{API_URL}/start_session")

    st.session_state.session_id = session["session_id"]
    st.session_state.q_index = 0
    st.session_state.question = None
    st.session_state.feedback = None
    st.session_state.study_plan = None


TOTAL_QUESTIONS = 10

# -----------------------
# Progress Bar (FIXED)
# -----------------------

answered = st.session_state.q_index

if st.session_state.feedback:
    answered += 1

progress_value = min(answered / TOTAL_QUESTIONS, 1.0)

st.progress(progress_value)


# -----------------------
# Result Page
# -----------------------

if st.session_state.study_plan:

    st.balloons()
    st.header("Personalized Study Plan")

    st.write(st.session_state.study_plan)

    if st.button("Restart Test"):
        st.session_state.clear()
        st.rerun()


# -----------------------
# Test Flow
# -----------------------

else:

    # Load question
    if st.session_state.question is None and st.session_state.q_index < TOTAL_QUESTIONS:

        q = api_get(f"{API_URL}/next_question/{st.session_state.session_id}")

        if q:
            st.session_state.question = q

        else:
            plan = api_get(f"{API_URL}/study_plan/{st.session_state.session_id}")

            if plan:
                st.session_state.study_plan = plan["study_plan"]
                st.rerun()

    if st.session_state.question is None:
        st.stop()

    q = st.session_state.question

    st.subheader(f"Question {st.session_state.q_index + 1}/{TOTAL_QUESTIONS}")

    st.write(q["question_text"])
    st.caption(f"Topic: {q['topic']}")
    st.caption(f"Difficulty: {q['difficulty']:.2f}")

    options = list(q["options"].keys())

    answer = st.radio(
        "Choose an option",
        options,
        format_func=lambda x: f"{x}: {q['options'][x]}",
    )

    # -----------------------
    # Submit Answer
    # -----------------------

    if st.button("Submit Answer") and st.session_state.feedback is None:

        result = api_post(
            f"{API_URL}/submit_answer/{st.session_state.session_id}",
            {"answer": answer},
        )

        if result:
            st.session_state.feedback = result
            st.rerun()

    # -----------------------
    # Feedback
    # -----------------------

    if st.session_state.feedback:

        if st.session_state.feedback["correct"]:
            st.success("Correct")
        else:
            st.error("Incorrect")

        st.info(f"Estimated Ability: {st.session_state.feedback['new_ability']:.2f}")

        # Last question
        if st.session_state.q_index == TOTAL_QUESTIONS - 1:

            if st.button("Finish Test"):

                plan = api_get(
                    f"{API_URL}/study_plan/{st.session_state.session_id}"
                )

                if plan:
                    st.session_state.study_plan = plan["study_plan"]
                    st.rerun()

        else:

            if st.button("Next Question"):

                st.session_state.q_index += 1
                st.session_state.question = None
                st.session_state.feedback = None

                st.rerun()