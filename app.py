# streamlit_app.py
import streamlit as st
import os
from datetime import datetime
from helpers import extract_text

# --- 1. [NEW] Import your LangGraph "Factory" ---
try:
    from main_orchestrator import app as langgraph_app
    from main_orchestrator import InterviewWorkflowState
    print("=== LangGraph Factory Loaded Successfully ===")
except ImportError:
    st.error("CRITICAL ERROR: Could not import 'main_orchestrator.py'.")
    # Stop the app if the factory cannot be loaded
    st.stop()


UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.title("Welcome to Job Interview Prep Agent!")

# (UI part... completely unchanged)
name = st.text_input("What is your name?")
job_role = st.text_input("Which role have you applied to?")
job_company = st.text_input("Which company have you applied to?")

uploaded_file = st.file_uploader("Upload your CV/resume", type=["pdf", "doc", "docx"])

# Submit button
if st.button("Submit"):
    if name and uploaded_file and job_role and job_company:
        # (File saving logic... unchanged)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{job_role}_{job_company}_{timestamp}_{uploaded_file.name}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        # Save the uploaded file
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success(f"File saved as `{filename}`")

        # (Text extraction logic... unchanged)
        resume_text = extract_text(file_path)
        
        # (Metadata saving logic... unchanged)
        with open(os.path.join(UPLOAD_DIR, "metadata.txt"), "a") as meta:
            meta.write(f"{datetime.now()} | {name} | {job_role} | {job_company} | {filename}\n")
        st.info("Metadata recorded successfully!")

        # --- 2. [NEW] Check for text and call LangGraph ---
        if resume_text:
            st.subheader("Extracted Resume Text (Preview)")
            st.text_area("Resume Text", resume_text[:1000], height=300)
            
            # A. Prepare the initial state for the "conveyor belt"
            # !! Note: We are now passing the resume_text directly !!
            initial_state = {
                "cv_text": resume_text, # <-- [NEW] Pass the extracted text directly
                "job_role": job_role,
                "job_company": job_company,
                "questions": {},
                "interview_transcript": [],
                "final_review": "",
                "error": ""
            }

            # B. Display a "loading" message and call the "factory"
            with st.spinner("Agent pipeline started... (Generating Questions, Calling Anam)..."):
                try:
                    # C. !! Send the order to the "factory" !!
                    final_state = langgraph_app.invoke(initial_state)
                    
                    # D. Display the "finished product"
                    st.success("Interview Complete! Here is your final review:")
                    st.subheader(f"Feedback for {name}")
                    st.write(final_state.get("final_review", "Error: No review was generated."))

                    st.subheader("Interview Transcript:")
                    st.json(final_state.get("interview_transcript", "No transcript available."))

                except Exception as e:
                    st.error(f"An error occurred in the agent pipeline: {e}")
                    st.exception(e)
        else:
            st.warning("No text could be extracted from this file. Cannot start Agent.")
    else:
        st.error("Please upload your CV/resume and enter all your details to proceed.")