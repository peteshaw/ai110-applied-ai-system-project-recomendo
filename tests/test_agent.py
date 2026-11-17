"""Offline tests for the agentic explanation layer.

No API key, no network: every test drives the deterministic stubs, so the verifier and the
retry loop are pinned by assertions rather than by eyeballing output.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.agent import run
from src.facts import catalog_vocabulary, fact_sheet
from src.llm import StubProvider
from src.nlu import parse_request
from src.recommender import load_profiles, load_songs
from src.retrieval import load_notes, retrieve_notes
from src.verify import verify_explanation

SONGS = load_songs()
PROFILES = load_profiles()


class TestNaturalLanguage(unittest.TestCase):
    def test_mood_and_genre_recognised(self):
        prefs, report = parse_request("something chill lofi for studying", SONGS)
        self.assertEqual(prefs.get("favorite_mood"), "chill")
        self.assertEqual(prefs.get("favorite_genre"), "lofi")
        self.assertEqual(prefs.get("target_energy"), 0.35)
        self.assertIn("favorite_mood:chill", report["matched"])
        self.assertIn("favorite_genre:lofi", report["matched"])

    def test_unknown_words_are_reported_not_guessed(self):
        prefs, report = parse_request("play me some bebop from mars", SONGS)
        self.assertTrue(report["empty"])
        self.assertIn("bebop", report["ignored"])

    def test_decade_and_popularity(self):
        prefs, _ = parse_request("popular 90s hits", SONGS)
        self.assertEqual(prefs.get("target_decade"), 1990)
        self.assertIn("min_popularity", prefs)


class TestVerifier(unittest.TestCase):
    def setUp(self):
        ranked = run("chill study music", SONGS, PROFILES,
                     provider=StubProvider("careful"))
        self.facts = ranked["facts"]
        self.vocab = catalog_vocabulary(SONGS)

    def test_supported_explanation_grounds(self):
        text = (f"\"{self.facts['title']}\" by {self.facts['artist']} is a "
                f"{self.facts['mood']} {self.facts['genre']} track with energy "
                f"{self.facts['energy']:.2f} and tempo {self.facts['tempo_bpm']:.0f} BPM.")
        report = verify_explanation(text, self.facts, self.vocab)
        self.assertTrue(report["grounded"], report["problems"])
        self.assertGreaterEqual(report["ratio"], 0.8)

    def test_invented_year_is_caught(self):
        text = (f"\"{self.facts['title']}\" was released in 1975 with energy "
                f"{self.facts['energy']:.2f}.")
        report = verify_explanation(text, self.facts, self.vocab)
        self.assertFalse(report["grounded"])
        self.assertTrue(any("1975" in p for p in report["problems"]))

    def test_invented_title_is_caught(self):
        text = (f"\"{self.facts['title']}\" pairs well with \"Imaginary Sunset\".")
        report = verify_explanation(text, self.facts, self.vocab)
        self.assertFalse(report["grounded"])
        self.assertTrue(any("Imaginary Sunset" in p for p in report["problems"]))

    def test_explanation_with_no_claims_is_not_grounded(self):
        report = verify_explanation("This one feels right.", self.facts, self.vocab)
        self.assertFalse(report["grounded"])
        self.assertEqual(report["ratio"], 0.0)


class TestAgentLoop(unittest.TestCase):
    def test_careful_provider_answers_first_time(self):
        result = run("chill study music", SONGS, PROFILES,
                     provider=StubProvider("careful"))
        self.assertEqual(result["status"], "answered")
        self.assertEqual(len(result["attempts"]), 1)
        self.assertTrue(result["grounding"]["grounded"])

    def test_sloppy_provider_triggers_one_retry_then_passes(self):
        result = run("chill study music", SONGS, PROFILES,
                     provider=StubProvider("sloppy"))
        self.assertEqual(result["status"], "answered")
        self.assertEqual(len(result["attempts"]), 2)
        self.assertFalse(result["attempts"][0]["grounded"])
        self.assertTrue(result["attempts"][1]["strict"])
        self.assertTrue(result["attempts"][1]["grounded"])

    def test_no_retry_when_attempts_capped_at_one(self):
        result = run("chill study music", SONGS, PROFILES,
                     provider=StubProvider("sloppy"), max_attempts=1)
        self.assertEqual(result["status"], "caveated")
        self.assertEqual(len(result["attempts"]), 1)

    def test_profile_only_run_works(self):
        result = run("", SONGS, PROFILES, profile_name="chill_lofi",
                     provider=StubProvider("careful"))
        self.assertEqual(result["status"], "answered")
        self.assertIn("recommendation", result)

    def test_recommendation_matches_recommender(self):
        """The loop must not change what gets recommended, only how it is described."""
        from src.recommender import recommend_songs
        prefs, _ = parse_request("chill study music", SONGS)
        expected = recommend_songs(prefs, SONGS, k=3)[0]["song"]["title"]
        result = run("chill study music", SONGS, PROFILES,
                     provider=StubProvider("careful"))
        self.assertEqual(result["recommendation"]["title"], expected)

    def test_fact_sheet_keeps_tags_as_list(self):
        result = run("chill study music", SONGS, PROFILES,
                     provider=StubProvider("careful"))
        self.assertIsInstance(result["facts"]["mood_tags"], list)
        self.assertTrue(all(isinstance(t, str) for t in result["facts"]["mood_tags"]))

    def test_context_notes_are_retrieved_and_reported(self):
        result = run("something chill for studying", SONGS, PROFILES,
                     provider=StubProvider("careful"))
        keys = [note["key"] for note in result["retrieved_notes"]]
        self.assertIn("study_sessions", keys)

    def test_retrieval_ignores_unrelated_requests(self):
        notes = load_notes()
        self.assertEqual(retrieve_notes("polka death metal", notes), [])


if __name__ == "__main__":
    unittest.main()
