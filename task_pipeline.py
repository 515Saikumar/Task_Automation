import json
import re
import os
from datetime import datetime, timezone, timedelta
from langchain_groq import ChatGroq

# Import the validator from your tools folder
from tools.due_date_tool import validate_due_date

llm = ChatGroq(
    model_name="llama-3.1-8b-instant",
    temperature=0,
    max_tokens=150,
    groq_api_key=os.getenv("GROQ_API_KEY")
)

def detect_dependencies(text):
    text = text.lower()
    dependencies = []
    for pattern in [r'after\s+(.+?)(\.|,|$)', r'depends on\s+(.+?)(\.|,|$)', r'blocked by\s+(.+?)(\.|,|$)']:
        match = re.search(pattern, text)
        if match:
            dependencies.append(match.group(1).strip().title())
    return dependencies

def detect_category(text):
    text = text.lower()
    categories = {
        "AI/ML": ["ai", "machine learning", "deep learning", "llm", "rag", "langchain", "embedding", "vector database", "faiss", "ollama", "qwen", "gemma", "huggingface", "tensorflow", "keras", "pytorch", "scikit-learn", "nlp", "computer vision", "prediction", "chatbot", "agent", "prompt engineering"],
        "Backend": ["backend", "api", "rest api", "fastapi", "flask", "django", "spring", "spring boot", "node", "express", "server", "microservice", "authentication", "login api", "signup api", "jwt", "redis", "bug", "crud", "endpoint"],
        "PowerBI": ["power bi", "powerbi", "dashboard", "report", "visualization", "visual", "chart", "graph", "dax", "measure", "power query", "etl", "dataset", "data source", "sql"],
        "Frontend": ["frontend", "react", "angular", "vue", "nextjs", "html", "css", "bootstrap", "tailwind", "javascript", "typescript", "ui", "ux", "page", "screen", "component", "dashboard", "login page", "signup page"],
        "DevOps": ["devops", "docker", "kubernetes", "terraform", "jenkins", "deployment", "deploy", "ci/cd", "pipeline"],
        "Database": ["database", "mongodb", "mysql", "postgresql", "sql", "query", "schema", "migration"],
        "QA": ["qa", "testing", "test case", "unit test", "automation", "selenium", "pytest"],
        "Cloud": ["cloud", "aws", "azure", "gcp", "lambda", "ec2", "s3"],
        "Security": ["security", "oauth", "encryption", "vulnerability"],
        "Project Management": ["planning", "meeting", "scrum", "agile", "jira", "sprint"]
    }
    
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in text:
                return category
    return "General"

def extract_task(text):
    # Fallback for empty rows in Excel
    if not text or str(text).strip() == "":
        text = "Empty task description provided."

    # Get today's exact date in IST
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    current_date = datetime.now(ist_tz).strftime('%Y-%m-%d')

    prompt = f"""
You are an AI Task Extraction Assistant. Extract the main task from the following text. 

IMPORTANT DATE RULES:
1. Today's date is {current_date}. 
2. Format the "due_date" STRICTLY as YYYY-MM-DD.
3. If the text mentions a day (e.g., "Tuesday"), calculate the exact YYYY-MM-DD for the upcoming Tuesday based on today's date.
4. If no date is mentioned, default to today's date: {current_date}.

Return ONLY valid JSON containing the following keys: "task_name", "priority", "due_date", "description", "required_skills".
Do not include any conversational text.

Text to analyze: {text}

JSON Output:
"""
    try:
        response = llm.invoke(prompt)
        raw_text = response.content
        
        # Extract ONLY the JSON dictionary from the AI's response
        start_idx = raw_text.find('{')
        end_idx = raw_text.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            clean_json_str = raw_text[start_idx:end_idx+1]
        else:
            clean_json_str = "" # Trigger fallback if no brackets are found
            
        task = json.loads(clean_json_str, strict=False)
        
    except Exception as e:
        print(f"⚠️ Extraction Error: Using fallback task. Reason: {e}")
        
        # Use the original text as the task name (capped at 60 chars for the UI)
        raw_input_text = str(text).strip()
        fallback_title = raw_input_text[:60] + "..." if len(raw_input_text) > 60 else raw_input_text
        
        task = {
            "task_name": fallback_title,
            "priority": "Normal",
            "due_date": current_date, # Fallback to today
            "description": raw_input_text, # Keep the full text in the description
            "required_skills": []
        }

    task["category"] = detect_category(text)
    task["dependencies"] = detect_dependencies(text)
    
    # Run the validation
    task["due_date_valid"] = validate_due_date(task["due_date"])
    
    return task