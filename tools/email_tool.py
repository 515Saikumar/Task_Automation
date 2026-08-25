import os
import json
import base64
from email.mime.text import MIMEText
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Initialize LLM for drafting the email content
llm = ChatGroq(
    model_name="openai/gpt-oss-20b",
    temperature=0,
    max_tokens=1000,
    groq_api_key=os.getenv("GROQ_API_KEY")
).bind(response_format={"type": "json_object"})

def authenticate_gmail():
    """Authenticates the user with the Gmail API."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def generate_ai_email_content(employee, task, formatted_due_date):
    """Uses the LLM to draft a professional email subject and body."""
    prompt = f"""
You are an engineering manager's AI assistant. Draft a professional task assignment email body.
IMPORTANT: Do NOT include any sign-off, closing, or signature (like "Best regards" or "[Your Name]") at the end of your body.
You MUST write a real, professional email. Do NOT just copy the example text.

Employee Name: {employee.get('name')}
Designation: {employee.get('designation')}
Task Name: {task.get('task_name')}
Description: {task.get('description', 'No description provided')}
Category: {task.get('category', 'General')}
Priority: {task.get('priority', 'Normal')}
Due Date: {formatted_due_date}

You MUST output your response strictly as a JSON object with two keys: "subject" and "body". Do not wrap it in markdown block quotes.

{{
    "subject": "Relevant subject line here",
    "body": "Dear {employee.get('name')}, I am assigning you a new task regarding... (Write the full email here)"
}}
"""
    try:
        response = llm.invoke(prompt)
        raw_text = response.content
        
        # Extract ONLY what is between the first { and the last }
        start_idx = raw_text.find('{')
        end_idx = raw_text.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            clean_json_str = raw_text[start_idx:end_idx+1]
            return json.loads(clean_json_str, strict=False)
        else:
            raise ValueError("No JSON object '{...}' found in the LLM response.")
            
    except Exception as e:
        print(f"⚠️ LLM failed to draft email, using fallback template: {e}")
        return {
            "subject": f"New Task Assigned: {task.get('task_name')}",
            "body": f"Hello {employee.get('name')},\n\nYou have been assigned a new task: {task.get('task_name')}.\n\nDescription: {task.get('description')}\nDue Date: {formatted_due_date}"
        }

def send_task_email(employee, task):
    """Generates the AI email and sends it via Gmail API."""
    
    # 1. Handle Due Date fallback
    raw_due_date = task.get("due_date")
    if not raw_due_date or str(raw_due_date).strip().lower() in ["not specified", "none", "", "null", "n/a"]:
        formatted_due_date = "ASAP"
    else:
        # If it's a datetime object, format it nicely. Otherwise, keep it as a string.
        try:
            formatted_due_date = raw_due_date.strftime("%b %d, %Y")
        except AttributeError:
            formatted_due_date = str(raw_due_date)

    # 2. Generate intelligent email content via LLM
    print("🤖 Generating AI-customized email content via LLM...")
    ai_email = generate_ai_email_content(employee, task, formatted_due_date)

    # 3. Create the HTML Template
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
            <h2 style="color: #2563eb;">Task Details: {task.get('task_name')}</h2>
            
            <div style="background-color: #f8fafc; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                <p><strong>Priority:</strong> {task.get('priority', 'Normal')}</p>
                <p><strong>Category:</strong> {task.get('category', 'General')}</p>
                <p><strong>Due Date:</strong> {formatted_due_date}</p>
            </div>
            
            <div style="white-space: pre-wrap;">
                {ai_email.get('body')}
            </div>
            
            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="font-size: 12px; color: #888;">Automated message from AI Task Management System</p>
        </div>
      </body>
    </html>
    """

    # 4. Send using Gmail API
    try:
        creds = authenticate_gmail()
        service = build('gmail', 'v1', credentials=creds)

        message = MIMEText(html_content, 'html')
        message['to'] = employee.get('email')
        message['from'] = "saikumarponnana515@gmail.com" 
        message['subject'] = ai_email.get('subject')

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        service.users().messages().send(
            userId="me", 
            body={'raw': raw_message}
        ).execute()
        
        print(f"✉️ AI-generated email sent successfully via Gmail API to {employee['name']} ({employee['email']})")
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to Gmail API: {e}")
        return False