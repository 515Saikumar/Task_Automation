from datetime import datetime

from agent.state import TaskState

from task_pipeline import extract_task

from tools.duplicate_tool import search_existing_tasks
from tools.project_tool import get_project_list
from tools.due_date_tool import validate_due_date
from tools.create_task_tool import create_task_in_db
from tools.date_parser_tool import normalize_date

from allocation_agent import AllocationAgent


allocator = AllocationAgent()


# -----------------------------------
# Node 1 : Parse Input
# -----------------------------------

def parse_input(state: TaskState):

    task = extract_task(state["input_text"])

    task["due_date"] = normalize_date(task["due_date"])

    state["parsed_task"] = task

    return state


# -----------------------------------
# Node 2 : Duplicate Check
# -----------------------------------

def check_duplicate(state: TaskState):

    task_name = state["parsed_task"]["task_name"]

    state["duplicate"] = search_existing_tasks(task_name)

    return state


# -----------------------------------
# Node 3 : Project Assignment
# -----------------------------------

def assign_project(state: TaskState):

    projects = get_project_list()

    state["project"] = projects[0]

    return state


# -----------------------------------
# Node 4 : Due Date Validation
# -----------------------------------

def check_due_date(state: TaskState):

    try:

        due_date = datetime.strptime(
            state["parsed_task"]["due_date"],
            "%Y-%m-%d"
        )

        state["due_date_valid"] = validate_due_date(due_date)

    except ValueError:

        state["due_date_valid"] = False

    return state


# -----------------------------------
# Node 5 : Create Task
# -----------------------------------

def create_task(state: TaskState):

    parsed = state["parsed_task"]

    task = {

        "task_name": parsed["task_name"],

        "description": parsed["description"],

        "priority": parsed["priority"],

        "category": parsed["category"],

        "dependencies": parsed["dependencies"],

        "required_skills": parsed.get(
            "required_skills",
            []
        ),

        "project": state["project"],

        "due_date": parsed["due_date"]

    }

    db_result = create_task_in_db(task)

    state["task"] = task

    state["result"] = db_result

    return state


# -----------------------------------
# Node 6 : Allocate Employee
# -----------------------------------

def allocate_employee(state: TaskState):

    allocation = allocator.allocate(state["task"])

    state["allocation"] = allocation

    return state