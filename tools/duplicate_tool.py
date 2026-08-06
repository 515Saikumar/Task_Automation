existing_tasks = [
    "Fix Login Bug",
    "Update Dashboard",
    "API Testing"
]

def search_existing_tasks(task_name):
    if task_name in existing_tasks:
        return True

    return False