import json
import re
import os
from langchain_groq import ChatGroq

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

    # AI/ML checked first so words like "agent" aren't stolen by Frontend
    categories = {
        "AI/ML": [
            "ai", "machine learning", "deep learning", "llm", "rag", 
            "langchain", "embedding", "vector database", "faiss", 
            "ollama", "qwen", "gemma", "huggingface", "tensorflow", 
            "keras", "pytorch", "scikit-learn", "nlp", "computer vision", 
            "prediction", "chatbot", "agent", "prompt engineering"
        ],
        "Backend": [
            "backend", "api", "rest api", "fastapi", "flask", "django", 
            "spring", "spring boot", "node", "express", "server", 
            "microservice", "authentication", "login api", "signup api", 
            "jwt", "redis", "bug", "crud", "endpoint"
        ],
         "PowerBI": [
            "power bi", "powerbi", "dashboard", "report", "visualization",
            "visual", "chart", "graph", "bar chart", "line chart", "pie chart",
            "table", "matrix", "card", "kpi", "gauge", "slicer", "filter",
            "drill down", "drillthrough", "tooltip", "bookmark",
            "dax", "measure", "calculated column", "calculated table",
            "power query", "m query", "query editor", "data transformation",
            "etl", "data cleaning", "data model", "data modeling",
            "relationship", "star schema", "snowflake schema",
            "fact table", "dimension table",
            "dataset", "data source", "excel", "csv", "sql",
            "mysql", "postgresql", "sql server", "oracle",
            "api", "sharepoint", "onedrive",
            "refresh", "scheduled refresh", "gateway",
            "workspace", "app", "publish", "power bi service",
            "report server", "row level security", "rls",
            "business intelligence", "bi", "analytics",
            "sales dashboard", "finance dashboard",
            "hr dashboard", "marketing dashboard",
            "inventory dashboard", "performance dashboard"
        ],
        "Frontend": [
            "frontend", "react", "angular", "vue", "nextjs", "html", 
            "css", "bootstrap", "tailwind", "javascript", "typescript", 
            "ui", "ux", "page", "screen", "component", "dashboard", 
            "login page", "signup page", "landing page", "form"
        ],
        "DevOps": ["devops", "docker", "kubernetes", "terraform", "jenkins", "deployment", "deploy", "ci/cd", "pipeline"],
        "Database": ["database", "mongodb", "mysql", "postgresql", "sql", "query", "schema", "migration"],
        "QA": ["qa", "testing", "test case", "unit test", "automation", "selenium", "pytest"],
        "Cloud": ["cloud", "aws", "azure", "gcp", "lambda", "ec2", "s3"],
        "Security": ["security", "oauth", "encryption", "vulnerability"],
        "Documentation": ["documentation", "readme", "report", "presentation", "wiki"],
        "Project Management": ["planning", "meeting", "scrum", "agile", "jira", "sprint"]
    }
    
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in text:
                return category

    return "General"

def extract_task(text):
    prompt = f"""
You are an AI Task Extraction Assistant. Extract the main task from the following text. Return ONLY valid JSON containing:
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
    clean_response = response.content.replace("```json", "").replace("```", "").strip()
    
    try:
        task = json.loads(clean_response)
    except json.JSONDecodeError:
        task = {
            "task_name": "Failed to parse",
            "priority": "Normal",
            "due_date": "",
            "description": "JSON parsing error.",
            "required_skills": []
        }

    task["category"] = detect_category(text)
    task["dependencies"] = detect_dependencies(text)
    return task