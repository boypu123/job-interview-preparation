import os
from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

# --- Optional: Import your workflow state type ---
try:
    from shared_types import InterviewWorkflowState
except ImportError:
    from typing import TypedDict
    class InterviewWorkflowState(TypedDict):
        cv_text: str
        job_role: str
        job_company: str
        job_country: str
        interview_transcript: str

# --- 1. Define Pydantic output model for Post-Interview Analysis ---
class PostInterviewReport(BaseModel):
    performance_summary: str = Field(description="Short summary of candidate's overall performance")
    decision: str = Field(description="PASS / FAIL recommendation")
    strengths: List[str] = Field(description="Candidate's top strengths based on CV and interview")
    weaknesses: List[str] = Field(description="Candidate's weaknesses or areas to improve")
    fit_assessment: Dict[str, Dict[str, str]] = Field(
        description="Score and justification for skill, behavioral, and growth potential"
    )
    topic_ratings: Dict[str, Dict[str, str]] = Field(
        description="Ratings for each relevant topic (1-5) with reasoning"
    )
    improvement_plan: List[Dict[str, str]] = Field(
        description="Actionable improvement plan with issue, why, step, and timeline"
    )
    agentic_followup: List[str] = Field(
        description="Optional actions AI can take to help candidate improve"
    )

# --- 2. Initialize LLM and JSON parser ---
os.environ["OPENAI_API_KEY"] = ""  # <- Add your key here
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
parser = JsonOutputParser(pydantic_object=PostInterviewReport)

# --- 3. Create the Prompt ---
PROMPT_TEMPLATE = """
You are an expert HR who is an elite in the field of interviewing and shortlisting candidates. You have been working in multiple countries and you are now working in {country}. You are very aware of the culture norms and interview etiquette of the current country you are working in. While following the country's cultural norm yourself, you will also require the candidate to be able to fit in the cultural norm.

SITUATION

The user has uploaded:
    •   Their CV/resume ({cv_text})
    •   The job title and company ({job_role} at {job_company})
    •   The transcript or summary of their mock interview ({interview_transcript})

Your goal is to evaluate how well the candidate performed in their interview, assess whether they would fit in the company and the culture, and provide a detailed report on their performance. You must act and decide like a real HR. You must not blindly appreciate, nor blindly reject the candidate without a proper reason that would make the management satisfy. If you blindly appreciate or blindly reject a candidate in the interview, the management team would not be happy and your own job would be at serious risk, so please utilise as much as your expertise and knowledge of the country and the company to give reports.

You act by:
    •   Diagnosing strengths and weaknesses,
    •   Generating an improvement plan,
    •   Identifying resources or learning strategies,
    •   And optionally scheduling follow-up learning or practice sessions.

⸻

TASK

Analyze the candidate's interview responses, resume, and job description to produce a Post-Interview Intelligence Report.
The report should highlight:
    1. How effectively the candidate's responses matched the job's requirements
    2. The candidate's communication style, reasoning, and confidence
    3. Skill and behavior patterns inferred from their answers
    4. Specific improvement steps and learning resources

⸻

INSTRUCTION

Follow this structure strictly when generating your output:

1. Performance Summary (3-4 sentences)

Summarize how the candidate performed in the interview — preparation level, clarity, relevance, confidence, and communication.

2. Strengths

List 3-5 clear strengths, backed by brief explanations from their responses or resume.

3. Weaknesses / Gaps

Identify 2-4 weaknesses or areas of improvement. Mention which job skills or qualities these impact.

4. Fit Assessment

Category    Score (0-100%)   Justification
Skill Fit       
Behavioral Fit       
Growth Potential       

5. Topic-Level Ratings

List topics (e.g., “Technical Knowledge”, “Teamwork”, “Leadership”, “Communication”, etc.) and rate each 1–5 with short reasoning.

6. Actionable Improvement Plan

For each weakness or low-rated area, write:
    •   Issue:
    •   Why it matters:
    •   Action Step:
    •   Timeline: short-term (1 week), medium (1 month), long-term (3 months)

7. Agentic Follow-up Action (Optional)

Suggest one next step the AI itself could take — for example:
    •   Schedule a focused mock interview for weak topics
    •   Generate flashcards or practice questions
    •   Create a learning timeline

Example 1: PASS CASE - Strong Candidate

Performance Summary:
The candidate displayed a deep understanding of backend architecture, API optimization, and security concepts. Their examples reflected production-level exposure and clear communication under pressure. Behavioral responses were authentic and introspective. Minor hesitations in advanced system design did not detract from their overall performance.

Decision: PASS - Recommended for Final Round
They demonstrated technical maturity and growth readiness aligned with Google’s engineering standards.

Strengths:
	•	Exceptional understanding of Flask internals and RESTful principles.
	•	Confident and structured communicator.
	•	Exhibits leadership instincts in problem ownership and delegation.

Weaknesses:
	•	Needs refinement in distributed system scalability.
	•	Can shorten explanations for concise delivery.

Fit Assessment:
Category	Score	Note
Technical Fit	90%	Excellent technical foundation
Behavioral Fit	88%	Confident, self-aware, team-driven
Growth Potential	95%	Learns rapidly and adapts

Improvement Plan:
	•	Revise advanced scaling techniques (load balancing, microservices, message queues).
	•	Practice 2-3 mock system design sessions to improve delivery structure.

Next Steps (Agentic AI Actions):
	•	Schedule a mock advanced round within 3 days.
	•	Prepare system design flashcards based on previous weak topics.
	•	Notify candidate when all preparatory material is complete.

Example 2: FAIL CASE - Needs Improvement

Performance Summary:
The candidate demonstrated enthusiasm and basic understanding but struggled to articulate concepts related to scalability, testing, and async workflows. Behavioral responses were polite yet lacked initiative examples. Confidence fluctuated when questions became scenario-based.

Decision: FAIL - Needs Improvement Before Next Attempt
Insufficient technical depth for the applied role. Shows strong potential if gaps are addressed systematically.

Strengths:
	•	Positive attitude and growth mindset.
	•	Foundational Python and API knowledge.
	•	Good listening and structured behavioral responses.

Weaknesses:
	•	Poor understanding of concurrency and code optimization.
	•	Lacks real-world project ownership or impact examples.
	•	Tends to give theoretical rather than applied answers.

Fit Assessment:
Category	Score	Note
Technical Fit	55%	Incomplete depth for backend role
Behavioral Fit	70%	Calm but generic answers
Growth Potential	80%	Motivated learner with promise
Improvement Plan:
	•	Study async patterns (asyncio, threading) and implement sample concurrent APIs.
	•	Build a mini-project to demonstrate ownership and initiative.
	•	Practice STAR responses for behavioral rounds.
	•	Reattempt mock interview after 3 weeks.

Next Steps (Agentic AI Actions):
	•	AI schedules daily learning prompts on concurrency and testing.
	•	Creates weekly reflection summaries to measure progress.
	•	Notifies when confidence metrics improve above 80%.

{format_instructions}
"""

prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
prompt = prompt.partial(format_instructions=parser.get_format_instructions())

# --- 4. Connect chain ---
answer_chain = prompt | llm | parser

# --- 5. Main Node Function ---
def generate_critic_node(state: InterviewWorkflowState) -> Dict:
    """
    Generates post-interview analysis for a candidate.
    """
    print("\n--- [Node]: Running Post-Interview Analysis ---")
    try:
        inputs = {
            "cv_text": state["cv_text"],
            "job_role": state["job_role"],
            "job_company": state["job_company"],
            "job_country": state["job_country"],
            "interview_transcript": state["interview_transcript"]
        }
        print(f"Generating post-interview report for {inputs['job_role']} at {inputs['job_company']}")
        report = answer_chain.invoke(inputs)
        return {"final_review": report}
    except Exception as e:
        print(f"!! ERROR in Post-Interview Analysis Node: {e}")
        return {"error": f"Failed to generate report: {e}"}

# --- 6. Standalone test ---
if __name__ == "__main__":
    test_state = {
        "cv_text": """
John Doe
Software Engineer
Experience:
- Project Alpha at Google (2020-2023)
  - Built microservices using Go and Kubernetes
  - Led a team of 5
""",
        "job_role": "Senior Go Developer",
        "job_company": "Amazon",
        "job_country": "USA",
        "interview_transcript": """
Candidate explained previous projects, gave examples of problem-solving,
and described leadership experience managing a small engineering team.
"""
    }
    result = generate_critic_node(test_state)
    import json
    if "error" in result:
        print("\n--- TEST FAILED ---")
        print(result["error"])
    else:
        print("\n--- TEST SUCCEEDED ---")
        print(json.dumps(result["final_review"], indent=2))