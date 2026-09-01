import json
import re
import os
from datetime import datetime, timezone, timedelta
from langchain_groq import ChatGroq

# Import the validator from your tools folder
from tools.due_date_tool import validate_due_date
from tools.date_parser_tool import normalize_date

llm = ChatGroq(
    model_name="openai/gpt-oss-20b",
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
        "DevOps": ["devops", "docker", "dockar", "kubernetes", "terraform", "jenkins", "deployment", "deploy", "ci/cd", "pipeline"],
        "Database": ["database", "mongodb", "mysql", "postgresql", "sql", "query", "schema", "migration"],
        "QA": ["qa", "testing", "test case", "unit test", "automation", "selenium", "pytest"],
        "Cloud": ["cloud", "aws", "azure", "gcp", "lambda", "ec2", "s3"],
        "Security": ["security", "oauth", "encryption", "vulnerability"],
        "Project Management": ["planning", "meeting", "scrum", "agile", "jira", "sprint"]
    }

    category_counts = {category: 0 for category in categories}
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in text:
                category_counts[category] += text.count(keyword)
                
    if all(count == 0 for count in category_counts.values()):
        return "General"
        
    return max(category_counts, key=category_counts.get)

def extract_task(text):
    # Fallback for empty rows in Excel
    if not text or str(text).strip() == "":
        text = "Empty task description provided."

    # Notice how much simpler the prompt is now! No more math rules.
    prompt = f"""
You are an AI Task Extraction Assistant. Extract the main task from the following text. 

Extract the "due_date" EXACTLY as it is written in the text (e.g., "Monday", "tomorrow", "August 10"). 
If no date is mentioned, leave "due_date" as an empty string "".

Determine the "category" of the task. It MUST be exactly one of the following: "AI/ML", "Backend", "PowerBI", "Frontend", "DevOps", "Database", "QA", "Cloud", "Security", "Project Management", or "General".
Note: If the task is primarily about building a user interface, UI, or frontend, categorize it as "Frontend" even if the project itself involves AI or agents.

Return ONLY valid JSON containing the following keys: "task_name", "priority", "due_date", "description", "required_skills", "category".
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
        raw_input_text = str(text).strip()
        fallback_title = raw_input_text[:60] + "..." if len(raw_input_text) > 60 else raw_input_text
        task = {
            "task_name": fallback_title,
            "priority": "Normal",
            "due_date": "", 
            "description": raw_input_text, 
            "required_skills": [],
            "category": ""
        }

    # --- THE MAGIC HAPPENS HERE ---
    # 1. Grab whatever the AI found (e.g., "Monday", or "")
    raw_date = task.get("due_date", "")
    
    # 2. If it's empty, default it to today's date in IST
    if not raw_date:
        # Fallback to scanning the full text for words like 'monday'
        raw_date = normalize_date(text)
        
        # If no date keywords were found, it returns the lowercased text
        if raw_date == text.lower() or raw_date == "Not Specified":
            ist_tz = timezone(timedelta(hours=5, minutes=30))
            raw_date = datetime.now(ist_tz).strftime('%Y-%m-%d')

    # 3. Pass it to your powerful dateparser tool
    date_info = validate_due_date(raw_date)
    
    # 4. Save the PERFECT date and the validation check back into the task dictionary
    task["due_date"] = date_info["clean_date"]
    task["due_date_valid"] = date_info["is_valid"]
    # ------------------------------

    # 1. Use the AI's category if it provided a valid one (this handles typos naturally)
    valid_categories = ["AI/ML", "Backend", "PowerBI", "Frontend", "DevOps", "Database", "QA", "Cloud", "Security", "Project Management"]
    
    # 2. If the AI failed or defaulted to General, fallback to our robust keyword matching
    skills_str = " ".join(task.get("required_skills", []))
    search_text = f"{text} {task.get('task_name', '')} {task.get('description', '')} {skills_str}"
    
    if task.get("category") not in valid_categories:
        task["category"] = detect_category(search_text)
        
    task["dependencies"] = detect_dependencies(search_text)
    
    return task