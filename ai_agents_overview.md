# AI Agents Overview

Your project is incredibly AI-driven! It relies on four distinct AI components (two formal "Agents" and two "LLM Pipelines") spread across the codebase. Here is the complete breakdown of every AI system running in your project and exactly what their functionality is:

## 1. The Frontend Chatbot Agent (`app.py`)
- **Type:** LangChain Tool-Calling Agent (`AgentExecutor`)
- **AI Brain:** Groq (`openai/gpt-oss-20b` or similar)
- **Functionality:** 
  This is the interactive "AI Progress Assistant" you chat with in the bottom right corner of your screen. When you ask a question like *"Are there any completed tasks today?"*, it doesn't just guess. It actively calls a custom python tool (`query_workprogress`) to search your MongoDB database, reads the results, and formulates a helpful response.
  
## 2. The Legacy Chatbot Agent (`main.py`)
- **Type:** LangChain Tool-Calling Agent (`AgentExecutor`)
- **AI Brain:** OpenAI (`gpt-4o-mini`)
- **Functionality:**
  This is almost identical to the chatbot in `app.py`, but it is powered by OpenAI instead of Groq. It seems this file was either an earlier version of your backend or an alternative server implementation. It possesses the exact same `query_workprogress` tool and instructions as the Groq-powered bot.

## 3. The Task Parsing Pipeline (`task_pipeline.py`)
- **Type:** Direct LLM JSON Extractor
- **AI Brain:** Groq (`openai/gpt-oss-20b`)
- **Functionality:**
  This is the silent engine of your system. Whenever you upload a new Excel file to the Admin Panel, this AI kicks in. Instead of chatting, it reads the raw text of every single task and extracts structured data. It figures out the **Primary Category** (e.g. AI/ML, DevOps), detects hidden **Due Dates** like "by next Friday", and evaluates urgency. The backend then uses this structured JSON to figure out exactly which employee should be assigned the task.

## 4. The Email Drafting Engine (`tools/email_tool.py`)
- **Type:** Direct LLM Content Generator
- **AI Brain:** Groq (`openai/gpt-oss-20b`)
- **Functionality:**
  Whenever a task is successfully assigned to an employee by the Task Parsing Pipeline, this AI steps in. It takes the raw details of the task and uses AI to draft a highly professional, well-formatted email notification that gets sent directly to the employee's inbox so they know exactly what they need to work on.

---

> [!NOTE]
> Currently, the system relies heavily on the **Groq API** for ultra-fast processing in the `task_pipeline`, `email_tool`, and the main `app.py` chatbot. The OpenAI agent in `main.py` serves as a solid alternative if you ever decide to switch your main chatbot over to OpenAI!
