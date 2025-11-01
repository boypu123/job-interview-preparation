import streamlit as st
import os
from datetime import datetime
from helpers import extract_text
import PyPDF2
import docx

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.title("Welcome to Job Interview Prep Agent!")

name = st.text_input("What is your name?")
job_role = st.text_input("Which role have you applied to?")
job_company = st.text_input("Which company have you applied to?")
job_country = st.text_input("What country have you applied to?")

uploaded_file = st.file_uploader("Upload your CV/resume", type=["pdf", "doc", "docx"])

# Submit button
if st.button("Submit"):
    if name and uploaded_file and job_role and job_company and job_country:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{job_role}_{job_company}_{job_country}_{timestamp}_{uploaded_file.name}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        # Save the uploaded file
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success(f"File saved as `{filename}`")

        # Extract text from the file
        resume_text = extract_text(file_path)
        if resume_text:
            st.subheader("Extracted Resume Text (Preview)")
            st.text_area("Resume Text", resume_text[:1000], height=300)
        else:
            st.warning("No text could be extracted from this file.")

        # Save metadata
        with open(os.path.join(UPLOAD_DIR, "metadata.txt"), "a") as meta:
            meta.write(f"{datetime.now()} | {name} | {job_role} | {job_company} | {job_country} | {filename}\n")

        st.info("Metadata recorded successfully!")
    else:
        st.error("Please upload your CV/resume and enter all your details to proceed.")