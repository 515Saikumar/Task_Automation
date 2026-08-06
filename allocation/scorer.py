class FinalScorer:

    # Weight configuration
    SKILL_WEIGHT = 0.50
    PERFORMANCE_WEIGHT = 0.25
    WORKLOAD_WEIGHT = 0.15
    AVAILABILITY_WEIGHT = 0.10

    @staticmethod
    def calculate(
        skill_score,
        workload_score,
        availability_score,
        performance_score
    ):
        """
        Calculate the final employee score.

        Formula:
        Final Score =
            Skill * 50%
          + Performance * 25%
          + Workload * 15%
          + Availability * 10%

        Returns:
            float
        """

        final_score = (
            skill_score * FinalScorer.SKILL_WEIGHT
            + performance_score * FinalScorer.PERFORMANCE_WEIGHT
            + workload_score * FinalScorer.WORKLOAD_WEIGHT
            + availability_score * FinalScorer.AVAILABILITY_WEIGHT
        )

        return round(final_score, 2)