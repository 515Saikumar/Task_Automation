from typing import TypedDict

class TaskState(TypedDict, total=False):

    input_text: str
    parsed_task: dict
    duplicate: bool
    project: str
    due_date_valid: bool
    task: dict
    result: dict
    allocation: dict