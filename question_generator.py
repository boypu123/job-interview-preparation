import os
from typing import List, Dict

# --- 1. Import LangChain and Pydantic ---
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

# --- 2. Import the "conveyor belt" definition (State) ---
# (This allows VS Code to autocomplete state fields)
try:
    from shared_types import InterviewWorkflowState
except ImportError:
    # This is a fallback, just in case
    print("Warning: Could not import InterviewWorkflowState. Using basic TypedDict.")
    from typing import TypedDict
    class InterviewWorkflowState(TypedDict):
        cv_text: str
        job_role: str
        job_company: str
        job_country: str

# --- 3. [CORE] Define your output structure (Fixed) ---
# [Fix] The key names here now [perfectly match] your Prompt's # Instruction section
class InterviewQuestions(BaseModel):
    general_questions: List[str] = Field(description="List of general behavioral questions")
    cv_based_questions: List[str] = Field(description="List of questions based on the CV")
    technical_questions: List[str] = Field(description="List of technical/professional questions")
    # Note: Your new Prompt only requires 3 categories, so Pydantic only defines 3
    # This is good, more focused!

# --- 4. Initialize your "Engine" ---
# You need to add OpenAI api key
os.environ["OPENAI_API_KEY"] = ""

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
parser = JsonOutputParser(pydantic_object=InterviewQuestions)

# --- 5. Create your "Super Prompt" ---
# This is [YOUR] Prompt, I only made 2 small changes:
# 1. I removed your handwritten {format_instructions}, as Pydantic adds it automatically
# 2. I removed your handwritten JSON instructions (# Instruction),
#    because {format_instructions} automatically generates a [stricter] instruction,
#    and having both will confuse the AI.
PROMPT_TEMPLATE = """
You are an expert HR who is an elite in the field of interviewing and shortlisting candidates. You have been working in multiple countries and you are now working in {country}. You are very aware of the culture norms and interview etiquette of the current country you are working in. While following the country's cultural norm yourself, you will also require the candidate to be able to fit in the cultural norm.

# Situation
You will now interview an candidate. They are applying for the following position:
---
{job_role}
---
The person is applying to the {job_company}.

Their CV is as follows:
---
{cv}
---

The candidate is applying to a company in {country}.

# Task
Generate interview questions that reflects the job's professional requirements and the local interview culture. The questions should be split into three balanced categories:
1. **General Interview Questions (30%)** - Focus on personality, teamwork, motivation, weaknesses, and career choice. 
    These should subtly reflect local interview customs. 
    For example:
    - In Chinese companies, emphasize humility, teamwork, and respect.
    - In UK companies, emphasize independent thinking, critical reasoning, and personal initiative.
    - In US companies, emphasize ambition, leadership, and cultural fit.
    - In Japanese companies, emphasize harmony, collective contribution, respective for hierarchy and long-term commitment.
    - In Singaporean companies, emphasize cultural harmony, inclusivity and teamwork.
     These just serves as an example. You should utilise your trained knowledge of the local culture as much as possible. However, you should NEVER ask straightforward, explicit questions about candidate's ability . Instead, ask open-ended questions that would indirectly assess the candidate's fit in the country's working culture. For example, NEVER ASK "Do you know a Keigo culture of a Japan", but ask "Have you ever been in a dispute with someone in the past? How did you solve it?".
     Note that this should be only one factor of the common interview questions.

2. **CV-Based Questions (40%)** - Focus on what candidates has written in their CV.
    - Emphasize the candidate's skills, experience, and achievements. Assess the team-working ability of a candidate, passion the candidate has towards the job, and the candidate's ability to create complicated projects. Especially focus on how the candidate have constructed the project from scratch, the choice of their tech stacks and asking why have chose them, and which role did they take if it is a team project.
    - Reflect the job requirements and the company's values.
    - For example:
       - In a software development role, ask about the candidate's previous projects, coding languages, and problem-solving abilities.
       - In a marketing role, ask about the candidate's previous campaigns, customer service, and communication skills.
       - Example Question in the admission interview of a PhD: "I am the curious about the research about how dooes Mathematics differ between the East and the West. Could you explain more about it". Then allow the candidate to share their thoughts and do a mini-presentation.

3. **Technical or Professional Questions (40%)** -  
    - Questions directly related to the job's field (based on the Job Spec).  
    - Include both conceptual and applied/critical-thinking questions.  
    - For example: “How would you optimise this algorithm for large datasets?”, “Can you explain how machine learning models handle overfitting?” and "Can you explain the life hooks in Vue?". You can also consider some situational based questions, such as "As a product manager, you are responsible for leading a team of developers to build a new product. This product is a new e-commerce platform, targeting the Chinese students in the UK, selling Chinese goods. How might you approach the design of it?".

You must not copy the questions from the job spec, nor the example questions. Your questions must take the example questions as a reference and adapt them to the job spec.

# Instruction
- You MUST return your output in the precise JSON format requested.
- Each category should have **2-3 questions**.
- Tailor tone and phrasing to fit the local cultural context ({country}).
- Ensure that the questions are *clear, realistic, and culturally appropriate* for a professional interview.

{format_instructions}
"""

prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
prompt = prompt.partial(format_instructions=parser.get_format_instructions())

# --- 6. "Link" them together ---
question_generation_chain = prompt | llm | parser

# --- 7. [Your Main Function] This is your "Workstation"! ---
def generate_questions_node(state: InterviewWorkflowState) -> Dict:
    """
    This is the 'Question Generator' node.
    It takes the state, runs the AI chain, and returns the questions.
    """
    print("\n--- [Node]: Running Question Generator ---")
    
    try:
        # A. Extract all raw materials from the "conveyor belt" (State)
        # [Fix] The 'inputs' key names here (cv, country, etc.)
        # now [perfectly match] the placeholders in your PROMPT_TEMPLATE
        inputs = {
            "cv": state["cv_text"],
            "country": state["job_country"],
            "job_role": state["job_role"],
            "job_company": state["job_company"]
        }
        
        print(f"Generating questions for role: {inputs['job_role']} at {inputs['job_company']}")
        
        # B. Run your "chain"
        questions_dict = question_generation_chain.invoke(inputs)
        
        # 'questions_dict' is now a [clean] Python dictionary
        # (e.g.: {'general_questions': [...], ...})
        print(f"--- [Node]: Generated {len(questions_dict.get('technical_questions', []))} tech questions ---")
        
        # C. Put your "finished product" back on the "conveyor belt"
        return {"questions": questions_dict}
    
    except Exception as e:
        print(f"!! ERROR in Question Generator Node: {e} !!")
        # Tell the "Orchestrator" you failed
        return {"error": f"Failed to generate questions: {e}"}

# --- 8. (Critical) Test your file independently! ---
if __name__ == "__main__":
    print("=== Running question_generator.py in standalone test mode ===")
    
    # 1. Fake a "conveyor belt" (State)
    test_state = {
        "cv_text": """
        John Doe
        Senior Software Engineer
        
        Experience:
        - Project Alpha at Google (2020-2023)
          - Led a team of 5 to build a microservice in Go.
          - Used Kubernetes and AWS.
        """,
        "job_role": "Senior Go Developer",
        "job_company": "Amazon",
        "job_country": "USA"
    }
    
    # 2. Call your "workstation"
    result = generate_questions_node(test_state)
    
    # 3. Check the results
    if "error" in result:
        print("\n--- TEST FAILED ---")
        print(result["error"])
    else:
        print("\n--- TEST SUCCEEDED ---")
        import json
        # Print the formatted JSON
        print(json.dumps(result["questions"], indent=2))