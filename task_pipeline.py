import json
import re
import os
from datetime import datetime, timezone, timedelta
from langchain_groq import ChatGroq

# Import the validator from your tools folder
from tools.due_date_tool import validate_due_date
from tools.date_parser_tool import normalize_date

llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    temperature=0,
    max_tokens=512,
    groq_api_key=os.getenv("GROQ_API_KEY")
)

# High-priority phrase signals that always win over keyword counting.
# Key: phrase that must appear at the START of the task text.
# Value: the category it maps to.
STRONG_SIGNALS = {
    "create a frontend": "Frontend",
    "build a frontend": "Frontend",
    "design a frontend": "Frontend",
    "create a ui": "Frontend",
    "build a ui": "Frontend",
    "create an interface": "Frontend",
    "design a page": "Frontend",
    "create a page": "Frontend",
    "create a dashboard": "Frontend",
    "build a dashboard": "Frontend",
    "create a react": "Frontend",
    "build a react": "Frontend",
    "create an api": "Backend",
    "build an api": "Backend",
    "create a rest api": "Backend",
    "write an api": "Backend",
    "setup docker": "DevOps",
    "deploy the": "DevOps",
    "train the model": "AI/ML",
    "train a model": "AI/ML",
    "build a rag": "AI/ML",
    "fine-tune": "AI/ML",
}

def detect_dependencies(text):
    text = text.lower()
    dependencies = []
    for pattern in [r'after\s+(.+?)(\.|,|$)', r'depends on\s+(.+?)(\.|,|$)', r'blocked by\s+(.+?)(\.|,|$)']:
        match = re.search(pattern, text)
        if match:
            dependencies.append(match.group(1).strip().title())
    return dependencies

def detect_category(text):
    """Detect category using a two-pass approach:
    1. Check high-priority STRONG_SIGNALS phrases (prefix-based).
    2. Fall back to weighted keyword counting.
    """
    normalized = text.strip().lower()

    # Pass 1: Strong signal phrases — these always win
    for phrase, category in STRONG_SIGNALS.items():
        if normalized.startswith(phrase) or f" {phrase} " in f" {normalized} ":
            print(f"[Category] Strong signal matched: '{phrase}' -> {category}")
            return category

    # Pass 2: Weighted keyword counting
    categories = {
        "Frontend": ["frontend", "react", "angular", "vue", "nextjs", "html", "css",
                     "bootstrap", "tailwind", "javascript", "typescript", "ui", "ux",
                     "page", "screen", "component", "login page", "signup page"],
        "Backend": ["backend", "api", "rest api", "fastapi", "flask", "django",
                    "spring boot", "node", "express", "server", "microservice",
                    "authentication", "jwt", "redis", "crud", "endpoint"],
        "AI/ML": ["machine learning", "deep learning", "llm", "rag", "langchain",
                  "embedding", "vector database", "faiss", "ollama", "huggingface",
                  "tensorflow", "pytorch", "scikit-learn", "nlp", "computer vision",
                  "prediction", "chatbot", "prompt engineering", "ai agent",
                  "language model", "generative ai", "fine tune", "fine-tune"],
        "PowerBI": ["power bi", "powerbi", "report", "visualization", "dax",
                    "measure", "power query", "etl", "data source"],
        "DevOps": ["devops", "docker", "kubernetes", "terraform", "jenkins",
                   "deployment", "deploy", "ci/cd"],
        "Database": ["database", "mongodb", "mysql", "postgresql", "query",
                     "schema", "migration"],
        "QA": ["qa", "testing", "test case", "unit test", "automation",
               "selenium", "pytest"],
        "Cloud": ["cloud", "aws", "azure", "gcp", "lambda", "ec2", "s3"],
        "Security": ["security", "oauth", "encryption", "vulnerability"],
        "Project Management": ["planning", "meeting", "scrum", "agile", "jira", "sprint"]
    }

    category_counts = {category: 0 for category in categories}
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in normalized:
                category_counts[category] += normalized.count(keyword)

    if all(count == 0 for count in category_counts.values()):
        return "General"

    best = max(category_counts, key=category_counts.get)
    print(f"[Category] Keyword scores: { {k: v for k, v in category_counts.items() if v > 0} }")
    print(f"[Category] Winner: {best}")
    return best

def extract_task(text):
    # Fallback for empty rows in Excel
    if not text or str(text).strip() == "":
        text = "Empty task description provided."

    # Notice how much simpler the prompt is now! No more math rules.
    prompt = f"""
You are an AI Task Extraction Assistant. Extract the main task from the following text. 

Extract the "due_date" EXACTLY as it is written in the text.
If no date is mentioned, leave "due_date" as an empty string "".

Determine the "category" of the task. It MUST be exactly one of the following: "AI/ML", "Backend", "PowerBI", "Frontend", "DevOps", "Database", "QA", "Cloud", "Security", "Project Management", or "General".

CRITICAL RULE: If the task mentions building a UI, interface, screen, or frontend (e.g. "create a frontend..."), it MUST be categorized as "Frontend", regardless of any other keywords like "agent" or "AI".

Examples:
- Text: "create a frontend for task allocation agent project" -> Category: "Frontend"
- Text: "build an api for the llm pipeline" -> Category: "Backend"
- Text: "train the rag model for the chatbot" -> Category: "AI/ML"
- Text: "setup docker for the react app" -> Category: "DevOps"

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

    # Always override the LLM category with our deterministic keyword detector.
    # The LLM is unreliable for classification — it confuses 'agent' with AI/ML, etc.
    # detect_category uses high-priority phrase signals first, then weighted keyword scoring.
    skills_str = " ".join(task.get("required_skills", []))
    search_text = f"{text} {task.get('task_name', '')} {task.get('description', '')} {skills_str}"

    detected_category = detect_category(search_text)
    if task.get("category") != detected_category:
        print(f"[Category Override] LLM said '{task.get('category')}', overriding with '{detected_category}'")
    task["category"] = detected_category

    task["dependencies"] = detect_dependencies(search_text)

    return task