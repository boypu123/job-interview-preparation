# flask_server.py
import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS  # <-- [NEW] 1. Import CORS
from typing import TypedDict, List, Dict

# --- 1. Import your "workstations" (nodes) ---
from helpers import extract_text 
from question_generator import generate_questions_node 
# from critic import generate_critique_node 

# --- 2. Define the "conveyor belt" (State) ---
# (This is just to make your code clearer, Flask doesn't use it directly)
class InterviewWorkflowState(TypedDict):
    cv_text: str
    job_role: str
    job_company: str
    job_country: str
    questions: Dict[str, List[str]]
    interview_transcript: List[Dict[str, str]]
    final_review: str
    error: str

# --- 3. Build the Flask "shopfront" ---
app = Flask(__name__)
os.makedirs("uploads", exist_ok=True)

# --- [NEW] 2. Enable CORS ---
# This tells the browser: "Allow all origins to access my API"
# (For a Hackathon, "*" is the fastest setting)
CORS(app) 

# (This is a temporary "database", same as before)
global_session_store = {}


# --- 4. API Endpoint 1: /api/start ---
# (This part's code is [completely unchanged])
@app.route('/api/start', methods=['POST'])
def start_interview_session():
    print("\n--- [API /start]: Received new session request ---")
    try:
        # A. Get data from frontend JSON
        data = request.get_json()
        cv_text = data.get("cv_text")
        job_role = data.get("job_role")
        job_company = data.get("job_company")
        job_country = data.get("job_country")

        print(f"Received job_role: {job_role}, job_company: {job_company}, job_country: {job_country}")
        if not cv_text:
            return jsonify({"error": "cv_text missing"}), 400

        # B. Prepare the state
        state_for_questions = {
            "cv_text": cv_text,
            "job_role": job_role,
            "job_company": job_company,
            "job_country": job_country
        }

        # C. Call question generator node
        print("--- [API /start]: Calling Question Generator Node ---")
        question_result = generate_questions_node(state_for_questions)

        if "error" in question_result:
            raise Exception(question_result["error"])

        questions = question_result.get("questions")

        # D. Save session
        session_id = "session_" + str(hash(cv_text))
        global_session_store[session_id] = {
            "cv_text": cv_text,
            "job_role": job_role,
            "job_company": job_company,
            "job_country": job_country,
            "questions": questions
        }

        print(f"--- [API /start]: Session {session_id} created. Returning questions. ---")

        return jsonify({"session_id": session_id, "questions": questions})

    except Exception as e:
        print(f"!! ERROR in /start: {e} !!")
        return jsonify({"error": str(e)}), 500



# --- 5. API Endpoint 2: /api/finish ---
# (This part's code is [completely unchanged])
@app.route('/api/finish', methods=['POST'])
def finish_interview_session():
    print("\n--- [API /finish]: Received finish request ---")
    try:
        # A. Get data from the Vue.js JSON
        data = request.json
        session_id = data.get("session_id")
        transcript = data.get("transcript") 

        if not session_id or not transcript:
            return jsonify({"error": "Missing session_id or transcript"}), 400

        # B. Retrieve the session
        session_data = global_session_store.get(session_id)
        if not session_data:
            return jsonify({"error": "Session not found or expired"}), 404

        # C. Prepare the "conveyor belt" (State)
        state_for_critic = {
            "cv_text": session_data["cv_text"],
            "job_role": session_data["job_role"],
            "job_company": session_data["job_company"],
            "job_country": session_data["job_country"],
            "questions": session_data["questions"],
            "interview_transcript": transcript 
        }
        
        # D. !! [MANUALLY] call "workstation 3" (Critic) !!
        print("--- [API /finish]: Calling Critic Node ---")
        critic_result = generate_critique_node(state_for_critic) 
        
        if "error" in critic_result:
            raise Exception(critic_result["error"])
        
        final_review = critic_result.get("final_review")
        
        # E. Clean up the session
        del global_session_store[session_id]
        
        # F. Send the [final report] back to Vue.js
        print("--- [API /finish]: Returning final review. ---")
        return jsonify({"final_review": final_review})

    except Exception as e:
        print(f"!! ERROR in /finish: {e} !!")
        return jsonify({"error": str(e)}), 500


# --- 6. Start the server ---
if __name__ == "__main__":
    print("=== Starting Job Interview Agent Backend (Flask) ===")
    # Your Vue.js teammate will call http://127.0.0.1:5000/api/start
    app.run(debug=True, port=5000)