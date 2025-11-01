# main_orchestrator.py
from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END

# --- 1. Import the [simplified] workstations (nodes) ---
from question_generator import generate_questions_node 
from anam_interviewer import run_interview_node
from critic import generate_critique_node

# --- 2. Define the [new] "conveyor belt" (State) ---
# It now [receives] cv_text as an input
class InterviewWorkflowState(TypedDict):
    # Inputs from Streamlit
    cv_text: str      # <-- [NEW] This is now an input
    job_role: str
    job_company: str
    
    # Outputs from the pipeline
    questions: Dict[str, List[str]]
    interview_transcript: List[Dict[str, str]]
    final_review: str
    error: str

# --- 3. Build the [simplified] "factory" ---
workflow = StateGraph(InterviewWorkflowState)


workflow.add_node("generate_questions", generate_questions_node) 
workflow.add_node("run_interview", run_interview_node)
workflow.add_node("generate_critique", generate_critique_node)

# --- 4. Define the [new] pipeline sequence ---
workflow.set_entry_point("generate_questions") 

workflow.add_edge("generate_questions", "run_interview")
workflow.add_edge("run_interview", "generate_critique")
workflow.add_edge("generate_critique", END)

# --- 5. Compile the factory (unchanged) ---
app = workflow.compile()