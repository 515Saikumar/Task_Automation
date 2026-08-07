import json
import re
import os
from datetime import datetime, timezone, timedelta
from langchain_groq import ChatGroq

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

Return ONLY valid JSON containing:
{{
    "task_name": "",
    "priority": "",
    "due_date": "",
    "description": "",
    "required_skills": []
}}
Text: {text}
"""
    response = llm.invoke(prompt)
    
    # Clean the response to prevent basic markdown issues
    clean_response = response.content.replace("```json", "").replace("```", "").strip()
    
    try:
        task = json.loads(clean_response)
    except json.JSONDecodeError:
        task = {
            "task_name": "Failed to parse",
            "priority": "Normal",
            "due_date": current_date, # Fallback to today
            "description": "JSON parsing error.",
            "required_skills": []
        }

    task["category"] = detect_category(text)
    task["dependencies"] = detect_dependencies(text)
    
    # Run the validation
    task["due_date_valid"] = validate_due_date(task["due_date"])
    
    return task