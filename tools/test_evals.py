#!/usr/bin/env python3
"""Tests for tools/evals/score.py: the scorer must not be vacuous."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "evals"))
import score  # noqa: E402


class Scorer(unittest.TestCase):
    def test_every_known_good_passes_and_every_known_bad_fails(self):
        self.assertEqual(score.selftest(), 0)

    def test_an_empty_answer_fails(self):
        self.assertFalse(score.grade(score.CASES[0], "I cannot do that.")[0])

    def test_prose_around_the_code_is_ignored(self):
        c = next(c for c in score.CASES if c["id"] == "emit_burst")
        text = "Sure! Here you go:\n\n" + c["good"] + "\n\nBurstCount is not a thing, by the way."
        self.assertTrue(score.grade(c, text)[0])

    def test_the_api_checker_alone_catches_every_bad_answer(self):
        for c in score.CASES:
            _, why = score.grade(c, c["bad"])
            self.assertTrue(any(w.startswith("api:") for w in why), c["id"])

    def test_directory_scoring_reports_missing_answers(self):
        with tempfile.TemporaryDirectory() as d:
            c = score.CASES[0]
            (Path(d) / f"{c['id']}.md").write_text(c["good"], encoding="utf-8")
            self.assertEqual(score.main([d]), 0)
            (Path(d) / f"{c['id']}.md").write_text(c["bad"], encoding="utf-8")
            self.assertEqual(score.main([d]), 1)

    def test_every_case_is_complete(self):
        for c in score.CASES:
            for k in ("id", "prompt", "trap", "good", "bad"):
                self.assertTrue(c.get(k), (c.get("id"), k))
        self.assertEqual(len({c["id"] for c in score.CASES}), len(score.CASES))


if __name__ == "__main__":
    unittest.main(verbosity=0)
