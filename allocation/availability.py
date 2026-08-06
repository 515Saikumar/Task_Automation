class AvailabilityChecker:

    @staticmethod
    def calculate(availability):
        """
        Calculate availability score.

        True  -> 100
        False -> 0

        Args:
            availability (bool)

        Returns:
            int
        """

        if availability:
            return 100

        return 0