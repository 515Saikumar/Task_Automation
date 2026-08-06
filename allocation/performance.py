class PerformanceCalculator:

    @staticmethod
    def calculate(performance_score):
        """
        Calculate performance score.

        Args:
            performance_score (int or float)

        Returns:
            float: Score between 0 and 100
        """

        if performance_score is None:
            return 0

        # Keep score within valid range
        performance_score = max(0, min(100, performance_score))

        return round(performance_score, 2)