class WorkloadCalculator:

    @staticmethod
    def calculate(active_tasks):
        """
        Calculate workload score.

        Less workload = Higher score

        Returns:
            int: Score between 0 and 100
        """

        if active_tasks <= 0:
            return 100

        if active_tasks >= 10:
            return 0

        score = 100 - (active_tasks * 10)

        return score