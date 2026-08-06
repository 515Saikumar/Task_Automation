from langgraph.graph import StateGraph, END

from agent.state import TaskState

from agent.nodes import (
    parse_input,
    check_duplicate,
    assign_project,
    check_due_date,
    create_task,
    allocate_employee,
)

workflow = StateGraph(TaskState)

# -----------------------
# Register Nodes
# -----------------------

workflow.add_node("parse_input", parse_input)

workflow.add_node("check_duplicate", check_duplicate)

workflow.add_node("assign_project", assign_project)

workflow.add_node("check_due_date", check_due_date)

workflow.add_node("create_task", create_task)

workflow.add_node("allocate_employee", allocate_employee)

# -----------------------
# Entry Point
# -----------------------

workflow.set_entry_point("parse_input")

# -----------------------
# Flow
# -----------------------

workflow.add_edge(
    "parse_input",
    "check_duplicate"
)

workflow.add_edge(
    "check_duplicate",
    "assign_project"
)

workflow.add_edge(
    "assign_project",
    "check_due_date"
)

workflow.add_edge(
    "check_due_date",
    "create_task"
)

workflow.add_edge(
    "create_task",
    "allocate_employee"
)

workflow.add_edge(
    "allocate_employee",
    END
)

graph = workflow.compile()