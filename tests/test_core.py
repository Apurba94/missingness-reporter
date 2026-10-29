import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from missingness_reporter.cli import main
from missingness_reporter.core import (co_missingness, column_summary, little_mcar_hint, missing_matrix, patterns,
                                       report, row_summary)

HEADER = ["id", "age", "income", "score"]
ROWS = [["1", "30", "NA", "5"], ["2", "", "", "6"], ["3", "40", "50", "7"], ["4", "45", "52", "-99"],
        ["5", "", "", "4"]]


class SummaryTests(unittest.TestCase):
    def setUp(self):
        self.m = missing_matrix(ROWS)

    def test_matrix_codes(self):
        self.assertEqual(self.m[0], [False, False, True, False])
        self.assertTrue(self.m[3][3])

    def test_columns_and_rows(self):
        cols = {c["column"]: c["missing"] for c in column_summary(HEADER, self.m)}
        self.assertEqual(cols, {"id": 0, "age": 2, "income": 3, "score": 1})
        r = row_summary(self.m)
        self.assertEqual((r["complete_rows"], r["distribution"]), (1, {0: 1, 1: 2, 2: 2}))

    def test_patterns(self):
        self.assertEqual(patterns(HEADER, self.m)[0], (2, ["age", "income"]))

    def test_co_missingness(self):
        top = co_missingness(HEADER, self.m)[0]
        self.assertEqual(top[:3], ("age", "income", 2))
        self.assertGreater(top[3], 0.5)


class MarTests(unittest.TestCase):
    def test_hint_detects_dependence(self):
        header = ["income", "age"]
        rows = [["", str(60 + i)] for i in range(6)] + [[str(1000 + i), str(25 + i)] for i in range(6)]
        hints = little_mcar_hint(header, rows, missing_matrix(rows))
        self.assertEqual(hints[0]["missing_in"], "income")
        self.assertGreater(hints[0]["t"], 2)

    def test_report_and_cli(self):
        rep = report(HEADER, ROWS)
        self.assertEqual(rep["rows"]["rows"], 5)
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "d.csv")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(",".join(HEADER) + "\n" + "\n".join(",".join(r) for r in ROWS) + "\n")
            with redirect_stdout(io.StringIO()) as buf:
                main([p, "--codes", "7"])
            self.assertIn("| score | 2 | 40.0 |", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
