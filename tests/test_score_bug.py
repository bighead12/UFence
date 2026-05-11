import pytest
from src.crew.fencing_crew import FencingCrew


class TestScoreUpdateBug:
    def test_score_updates_after_exchange(self):
        """Test that score is correctly updated after each exchange"""
        crew = FencingCrew()
        crew.start_new_match()

        initial_score = crew.referee.score
        assert initial_score == {"fencer": 0, "opponent": 0}

        result1 = crew.execute_exchange("direct_attack", "torso")

        score_after_first = crew.referee.score
        print(f"After first exchange: {score_after_first}")
        print(f"Result score: {result1['score']}")

        assert score_after_first == result1['score'], f"Score mismatch: crew={score_after_first}, result={result1['score']}"

        result2 = crew.execute_exchange("fleche", "torso")
        score_after_second = crew.referee.score
        print(f"After second exchange: {score_after_second}")
        print(f"Result2 score: {result2['score']}")

        assert score_after_second == result2['score']

        result3 = crew.execute_exchange("counter_attack", "shoulders")
        score_after_third = crew.referee.score
        print(f"After third exchange: {score_after_third}")
        print(f"Result3 score: {result3['score']}")

    def test_score_consistency_between_referee_and_result(self):
        """Test that referee.score and result['score'] are always consistent"""
        crew = FencingCrew()
        crew.start_new_match()

        for i in range(5):
            result = crew.execute_exchange("direct_attack", "torso")

            referee_score = crew.referee.score
            result_score = result['score']

            print(f"Exchange {i+1}: referee={referee_score}, result={result_score}")

            assert referee_score == result_score, f"Inconsistent at exchange {i+1}: referee={referee_score}, result={result_score}"

            if result.get('match_over'):
                break


if __name__ == "__main__":
    test = TestScoreUpdateBug()
    test.test_score_updates_after_exchange()
    print("\n--- Second test ---\n")
    test.test_score_consistency_between_referee_and_result()