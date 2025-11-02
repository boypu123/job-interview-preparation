# shared_types.py
from typing import TypedDict, List, Dict, Any

# This is the one and only definition of your "conveyor belt"
# All other files will import this.
class InterviewWorkflowState(TypedDict):
    # Inputs from Flask
    cv_text: str
    job_role: str
    job_company: str
    job_country: str

    # Intermediate data (from Question Generator)
    questions: Dict[str, List[str]]
    
    # Intermediate data (from Anam/Frontend)
    interview_transcript: List[Dict[str, str]]

    # Final output (from Critic)
    final_review: Dict[str, Any] # This is a Dict, not a str
    error: str