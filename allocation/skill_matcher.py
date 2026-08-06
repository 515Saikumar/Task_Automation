class SkillMatcher:

    @staticmethod
    def calculate(required_skills, employee_skills):
        """
        Calculate skill matching percentage.

        Args:
            required_skills (list): Skills required for the task.
            employee_skills (list): Skills possessed by the employee.

        Returns:
            float: Skill match percentage (0 - 100)
        """

        if not required_skills:
            return 0

        required = {skill.lower() for skill in required_skills}
        employee = {skill.lower() for skill in employee_skills}

        matched_skills = required.intersection(employee)

        score = (len(matched_skills) / len(required)) * 100

        return round(score, 2)