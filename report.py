import pandas as pd

# ---------------------------------------------------------
# 1. Agent Overview Data (Human-friendly descriptions)
# ---------------------------------------------------------
agent_data = {
    "Agent Name": [
        "Task Creation Agent",
        "Task Allocation Agent",
        "Remarks Agent",
        "Overdue Agent",
        "Recommendations Agent",
        "Report Writing Agent"
    ],
    "What it does (Plain English)": [
        "Acts as the front door. It takes new task requests and saves them securely in our live database.",
        "The matchmaker. It looks at the team's workload and skills, then assigns tasks to the best person for the job.",
        "The note-taker. Whenever a task's status changes, it automatically writes a clear update in the task history.",
        "The watchdog. It checks our system every 30 minutes and sends alerts if any tasks are at risk of falling behind.",
        "The morning coach. It reviews how the team is doing and sends 3-5 helpful tips to each member every morning.",
        "The storyteller. It gathers all the data from our workflow and turns it into a clean, professional summary report."
    ],
    "Tools Used": [
        "create_task_tool, project_tool",
        "Vaibhav's AllocationScorer, workload & skill tools",
        "workflow_api, live DB",
        "due_date_tool, date_parser, email_tool",
        "employee_api, employee_repository, email_tool",
        "Agent state graph, excel_repository"
    ]
}

# ---------------------------------------------------------
# 2. Daily Work & Standup Notes (7-Day Breakdown)
# ---------------------------------------------------------
daily_data = {
    "Day": ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"],
    "Main Focus": [
        "Task Creation & Allocation",
        "Remarks & Overdue Agents",
        "Prompt Optimization",
        "Recommendations & Reporting",
        "Archiving & UAT Support",
        "Regression Testing",
        "Handover & Demo Support"
    ],
    "Work Completed": [
        "Reviewed code for all 6 agents. Wrote documentation and 10 test cases for the Creation and Allocation agents. Discussed initial findings with Saikumar.",
        "Wrote docs and 10 test cases for Remarks and Overdue agents. Fixed failing tests with Saikumar's help. Reached 20 total tests.",
        "Reviewed Saikumar's prompt evaluation data. Found the least accurate agent, created 2 prompt improvements, and applied them.",
        "Finished docs and 10 test cases for the Recommendations and Report agents. We are now at 30 fully documented test cases.",
        "Archived all active prompts into /docs/prompts/. Wrote a one-page summary for all 6 agents. Helped with basic UAT testing.",
        "Ran a final check on all 30 test cases—everything passed. Checked all docs and prepared a quick testing summary sheet.",
        "Wrote the final testing handover guide. Helped Saikumar present the demo and shared our passing test results. Archived final prompts."
    ],
    "Quick Standup Update": [
        "Yesterday, I documented the Task Creation and Allocation agents and ran 10 tests. Saikumar and I reviewed a few tweaks. Today, I'm tackling the Remarks and Overdue agents.",
        "Yesterday, I finished testing the Remarks and Overdue agents, bringing our test count to 20. Today, I'll review our prompt accuracy and suggest improvements.",
        "Yesterday, we identified our lowest-performing prompt and I suggested two fixes to boost its accuracy. Today, I'll wrap up testing for the final two agents.",
        "Yesterday, I finished the last 10 tests for the Recommendations and Report agents. We officially have 30 passing tests. Today, I'm organizing our files and supporting UAT.",
        "Yesterday, I organized our prompt files, wrote the final module summary, and helped test the system. Today, I'm doing a final run of all 30 tests to ensure stability.",
        "Yesterday, I ran a final check on all 30 tests—all green. I also finished our testing summary sheet. Today, I'll finalize handover docs and help Saikumar with the demo.",
        "Yesterday, I finalized the testing guide and supported the live demo, showing off our 30 passing tests. All final files are now archived and handed over."
    ]
}

# ---------------------------------------------------------
# 3. Testing Summary
# ---------------------------------------------------------
testing_data = {
    "Agent": [
        "Task Creation", "Task Allocation", "Remarks", 
        "Overdue", "Recommendations", "Report Writing"
    ],
    "Test Cases Written": [5, 5, 5, 5, 5, 5],
    "Status": ["Pass", "Pass", "Pass", "Pass", "Pass", "Pass"],
    "Notes": [
        "Tested live DB connections (No mock data)",
        "Verified Vaibhav's AllocationScorer routing",
        "Checked auto-generation triggers on updates",
        "Confirmed 30-min timer and risk escalation",
        "Checked morning tip generation per user",
        "Verified final text formatting and readability"
    ]
}

# ---------------------------------------------------------
# Create the Excel File
# ---------------------------------------------------------
# Convert dictionaries to DataFrames
df_agents = pd.DataFrame(agent_data)
df_daily = pd.DataFrame(daily_data)
df_testing = pd.DataFrame(testing_data)

# Create an Excel writer object
filename = "Govind_Agent_Presentation_Doc.xlsx"
with pd.ExcelWriter(filename, engine='openpyxl') as writer:
    df_agents.to_excel(writer, sheet_name="1. Agent Overview", index=False)
    df_daily.to_excel(writer, sheet_name="2. Weekly Log & Standups", index=False)
    df_testing.to_excel(writer, sheet_name="3. Testing Summary", index=False)

print(f"Success! Your presentation document '{filename}' has been created.")