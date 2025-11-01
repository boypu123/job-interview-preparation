import streamlit as st
import os
from datetime import datetime

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.title("Welcome to Job Interview Prep Agent!")

name = st.text_input("What is your name?")
job_role = st.text_input("Which role have you applied to?")
job_company = st.text_input("Which company have you applied to?")

uploaded_file = st.file_uploader("Upload your CV/resume", type=["pdf", "doc", "docx"])

# Submit button
if st.button("Submit"):
    if name and uploaded_file and job_role and job_company:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{job_role}_{job_company}_{timestamp}_{uploaded_file.name}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        # Save the file
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success(f"File saved as `{filename}`")

        # Optionally save metadata
        with open(os.path.join(UPLOAD_DIR, "metadata.txt"), "a") as meta:
            meta.write(f"{datetime.now()} | {job_role} | {job_company} | {filename}\n")

        st.info("Metadata recorded successfully!")
    else:
        st.write("Please upload your CV/resume and enter all your details to proceed.")