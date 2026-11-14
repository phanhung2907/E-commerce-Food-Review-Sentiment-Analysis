"""Regression checks for held-out counts and multiple-testing correction."""

import unittest
import numpy as np
from scipy.sparse import csc_matrix
from scipy.stats import norm

from evaluate import apply_holm, phrase_counts


class EvaluationTests(unittest.TestCase):
    def test_clustered_table_and_wald(self):
        # Each group contributes a known 2x2 table; each row is one review.
        tables = [(4, 2, 3, 6), (3, 1, 5, 4), (4, 2, 2, 7),
                  (2, 3, 4, 5), (3, 1, 5, 6), (2, 2, 2, 5)]
        present, ratings, groups = [], [], []
        for group, cells in enumerate(tables):
            for (has_phrase, target), count in zip(
                [(1, 1), (1, 0), (0, 1), (0, 0)], cells
            ):
                present.extend([has_phrase] * count)
                ratings.extend([target] * count)
                groups.extend([group] * count)
        groups = np.array(groups)
        result, _ = phrase_counts(
            {"rating": 1, "column": 0}, csc_matrix(np.array(present)[:, None]),
            np.array(ratings), groups, groups, [],
        )
        totals = np.array(tables).sum(axis=0)
        np.testing.assert_array_equal([result[k] for k in ("tp", "fp", "fn", "tn")], totals)
        expected_or = totals[0] * totals[3] / (totals[1] * totals[2])
        influence = (np.array(tables) / totals) @ np.array([1, -1, -1, 1])
        se = np.sqrt(len(tables) / (len(tables) - 1) * np.sum(influence ** 2))
        self.assertAlmostEqual(result["or"], expected_or)
        self.assertAlmostEqual(result["p_raw"], norm.sf(np.log(expected_or) / se))

    def test_holm_includes_untestable_hypothesis(self):
        rows = []
        for index, p in enumerate([0.01, 0.03, 0.04, None]):
            rows.append(dict(p_raw=p, p_holm=None, language="en", rating=4, phrase=str(index),
                             p1=0.5, p2=0.2, **{"or": 2.0, "ci_low": 1.1}))
        apply_holm(rows)
        np.testing.assert_allclose([x["p_holm"] for x in rows[:3]], [0.04, 0.09, 0.09])
        self.assertIsNone(rows[3]["p_holm"])
        self.assertEqual(rows[3]["holm_input"], 1.0)


if __name__ == "__main__":
    unittest.main()
