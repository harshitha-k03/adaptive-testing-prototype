# Adaptive Testing Prototype

This is a 1-Dimension Adaptive Testing system built as per the intern assignment. It dynamically selects questions based on user responses to estimate proficiency, using Item Response Theory (IRT). After 10 questions, it generates a personalized study plan via an LLM.

## Instructions on How to Run the Project

1. **Prerequisites**:
   - Python 3.10+ installed.
   - MongoDB Atlas (URI in .env).
   - Google API key for Gemini (in .env as GOOGLE_API_KEY).

2. **Setup**:
   - Clone this repository.
   - Create .env with MONGO_URI and GOOGLE_API_KEY.
   - Install dependencies: `pip install -r requirements.txt`

3. **Seed the Database**:
   - Run `python seed.py`.

4. **Run the Backend**:
   - Run `uvicorn app:app --reload`.

5. **Run the Frontend**:
   - Run `streamlit run frontend.py` (opens in browser).

6. **Testing Flow**:
   - Start test (auto).
   - Answer question, submit—see feedback.
   - Click "Next Question".
   - After 10, click "Get AI Recommendations" for plan.

## Brief Explanation of Adaptive Algorithm Logic

Uses 1-parameter IRT (Rasch model):
- Start at ability 0.5.
- Select question closest to ability.
- Update ability via MLE after response.
- Ends after 10, analyzes misses for LLM.

## AI Log

Used Grok to generate structure, IRT, LLM integration. Challenges: SSL debug, manual testing in PyCharm.

## API Documentation

- POST /start_session: New session.
- GET /next_question/{session_id}: Next question.
- POST /submit_answer/{session_id}: Submit (body {"answer": "B"}).
- GET /study_plan/{session_id}: Plan after 10.

Error handling included.