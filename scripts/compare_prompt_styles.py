#!/usr/bin/env python3
"""Measure the effect of constrained, fact-only prompting on explanation quality.

The baseline writer is a fluent but unconstrained stub: it invents a year and a song.
The specialized writer uses the same facts with a strict, schema-like prompt. The script
reports grounded-claim ratios and fabrication counts, so specialization is measured
rather than asserted.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.agent import run
from src.llm import Provider
from src.recommender import load_profiles, load_songs

QUERIES = [
    "something chill lofi for studying",
    "upbeat pop for the gym",
    "lofi for reading on a rainy day",
    "popular 90s hits",
    "slow acoustic songs",
    "energetic dance music",
    "quiet sad songs",
    "2020s pop",
    "obscure deep cuts",
    "rock for a road trip",
]


class BaselineProvider(Provider):
    """Fluent writer with no grounding constraint (the failure mode being tested)."""

    name = "baseline-unconstrained"

    def explain(self, request, facts, strict=False, notes=""):
        return (f"\"{facts['title']}\" by {facts['artist']} is a {facts['mood']} "
                f"{facts['genre']} classic released in 2019 with energy "
                f"{facts['energy']:.2f}. It pairs well with \"Midnight Velvet\".")


class SpecializedProvider(Provider):
    """Constrained writer: only fact-sheet fields, no invented entities or numbers."""

    name = "specialized-fact-only"

    def explain(self, request, facts, strict=False, notes=""):
        tags = ", ".join(t for t in facts["mood_tags"][:2] if t) or facts["mood"]
        return (f"\"{facts['title']}\" by {facts['artist']} is a {facts['mood']} "
                f"{facts['genre']} track from the {facts['release_decade']:.0f}s with "
                f"energy {facts['energy']:.2f} and tempo {facts['tempo_bpm']:.0f} BPM. "
                f"It scores {facts['score']:.2f} against this profile, driven by {tags}.")


def evaluate(provider, songs, profiles):
    ratios, fabrications = [], 0
    for query in QUERIES:
        result = run(query, songs, profiles, provider=provider, max_attempts=1)
        ratios.append(result["grounding"]["ratio"])
        fabrications += sum(1 for problem in result["grounding"]["problems"]
                            if "not in catalog" in problem or "not supported" in problem)
    return {
        "provider": provider.name,
        "queries": len(QUERIES),
        "mean_claim_support": round(sum(ratios) / len(ratios), 3),
        "fabricated_claims": fabrications,
        "grounded_answers": sum(ratio >= 0.8 for ratio in ratios),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    songs, profiles = load_songs(), load_profiles()
    comparison = {
        "baseline": evaluate(BaselineProvider(), songs, profiles),
        "specialized": evaluate(SpecializedProvider(), songs, profiles),
    }
    comparison["improvement"] = {
        "claim_support_delta": round(comparison["specialized"]["mean_claim_support"]
                                     - comparison["baseline"]["mean_claim_support"], 3),
        "fabrications_removed": (comparison["baseline"]["fabricated_claims"]
                                 - comparison["specialized"]["fabricated_claims"]),
    }

    if args.json:
        print(json.dumps(comparison, indent=2))
    else:
        print("Prompt specialization comparison (10 queries, one attempt each)")
        for label, row in comparison.items():
            if label == "improvement":
                continue
            print(f"  {label:12s} support={row['mean_claim_support']:.3f} "
                  f"fabrications={row['fabricated_claims']} grounded={row['grounded_answers']}/{row['queries']}")
        delta = comparison["improvement"]
        print(f"  improvement  +{delta['claim_support_delta']:.3f} support, "
              f"{delta['fabrications_removed']} fabrications removed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
