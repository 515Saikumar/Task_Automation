from repository.employee_repository import EmployeeRepository
from allocation.skill_matcher import SkillMatcher
from allocation.workload import WorkloadCalculator
from allocation.availability import AvailabilityChecker
from allocation.performance import PerformanceCalculator
from allocation.scorer import FinalScorer


class AllocationAgent:

    def __init__(self):
        self.employee_repo = EmployeeRepository()

    def allocate(self, task):

        # -----------------------------
        # Get all employees
        # -----------------------------
        employees = self.employee_repo.get_all()

        if not employees:
            return {
                "success": False,
                "message": "No employees found."
            }

        # -----------------------------
        # Get Task Category
        # -----------------------------
        task_category = task.get("category", "").strip().lower()

        # -----------------------------
        # Filter by Primary Category
        # -----------------------------
        filtered_employees = [
            emp
            for emp in employees
            if emp.get("primary_category", "").strip().lower() == task_category
        ]

        # If no employees found, use all employees
        if not filtered_employees:
            print(f"\nNo employees found for '{task_category}'.")
            print("Using all employees...\n")
            filtered_employees = employees

        # Debug
        print("\n" + "=" * 50)
        print(f"Task Category : {task.get('category')}")
        print("=" * 50)

        print("Eligible Employees")

        for emp in filtered_employees:
            print(
                f"{emp['employee_id']} | "
                f"{emp['name']} | "
                f"{emp['primary_category']}"
            )

        print()

        # -----------------------------
        # Rank Employees
        # -----------------------------
        ranked_employees = []

        for employee in filtered_employees:

            skill_score = SkillMatcher.calculate(
                task.get("required_skills", []),
                employee.get("skills", [])
            )

            workload_score = WorkloadCalculator.calculate(
                employee.get("active_tasks", 0)
            )

            availability_score = AvailabilityChecker.calculate(
                employee.get("availability", False)
            )

            performance_score = PerformanceCalculator.calculate(
                employee.get("performance_score", 0)
            )

            final_score = FinalScorer.calculate(
                skill_score,
                workload_score,
                availability_score,
                performance_score
            )

            ranked_employees.append({
                "employee": employee,
                "skill_score": skill_score,
                "workload_score": workload_score,
                "availability_score": availability_score,
                "performance_score": performance_score,
                "final_score": final_score
            })

        # -----------------------------
        # Sort by Highest Score
        # -----------------------------
        ranked_employees.sort(
            key=lambda x: x["final_score"],
            reverse=True
        )

        # -----------------------------
        # Best Employee
        # -----------------------------
        best_employee = ranked_employees[0]["employee"]

        # Update task
        task["assigned_to"] = best_employee["employee_id"]
        task["assigned_employee"] = best_employee["name"]

        # -----------------------------
        # Return Result
        # -----------------------------
        return {
            "success": True,
            "assigned_employee": best_employee,
            "task": task,
            "ranking": ranked_employees
        }