"""The agentic layer: recommend, explain, check the explanation, retry once if it fails.

This is the feature the final project adds to VibeFinder. The recommender is unchanged and
still the source of truth; what is new is that its output has to survive an audit before it
reaches the user.
"""

import json
import os

from .facts import catalog_vocabulary, fact_sheet
from .llm import get_provider
from .nlu import parse_request
from .recommender import recommend_songs
from .verify import verify_explanation

DEFAULT_THRESHOLD = 0.8


def run(request, songs, profiles, profile_name=None, mode="balanced", k=3,
        provider=None, threshold=DEFAULT_THRESHOLD, max_attempts=2, trace_path=None,
        guardrails=True):
    """Return a result dict describing the recommendation, the explanation and the audit.

    The loop is deliberately small: one retry. If a second attempt is still ungrounded the
    system returns the explanation with an explicit caveat rather than hiding the failure.
    """
    if provider is None:
        provider = get_provider("stub")

    base_profile = profiles.get(profile_name) if profile_name else None
    if request:
        prefs, nlu_report = parse_request(request, songs, base_profile=base_profile)
    else:
        if base_profile is None:
            raise ValueError("Provide a request, a profile, or both.")
        prefs, nlu_report = dict(base_profile), {"matched": [], "ignored": [], "empty": True}

    # The honest refusal: if the request names nothing the catalog can filter on, say so
    # instead of dressing up the default ranking as a match.
    if guardrails and request and nlu_report.get("empty") and base_profile is None:
        return {"status": "no_match", "request": request, "profile": profile_name,
                "nlu": nlu_report, "attempts": [],
                "message": ("None of those terms map to catalog features (genre, mood, "
                            "energy, tempo, decade, popularity).")}

    if not guardrails:
        max_attempts, threshold = 1, 0.0

    ranked = recommend_songs(prefs, songs, k=k, mode=mode)
    if not ranked:
        return {"status": "no_results", "request": request, "attempts": [],
                "nlu": nlu_report}

    top = ranked[0]
    facts = fact_sheet(top)
    vocab = catalog_vocabulary(songs)

    attempts = []
    verdict = None
    for attempt in range(1, max_attempts + 1):
        text = provider.explain(request, facts, strict=attempt > 1)
        verdict = verify_explanation(text, facts, vocab, threshold=threshold)
        attempts.append({
            "attempt": attempt,
            "provider": provider.name,
            "strict": attempt > 1,
            "text": text,
            "grounded": verdict["grounded"],
            "ratio": verdict["ratio"],
            "problems": verdict["problems"],
        })
        if verdict["grounded"]:
            break

    status = "answered" if verdict and verdict["grounded"] else "caveated"
    result = {
        "status": status,
        "request": request,
        "profile": profile_name,
        "mode": mode,
        "nlu": nlu_report,
        "recommendation": {
            "title": facts["title"],
            "artist": facts["artist"],
            "genre": facts["genre"],
            "mood": facts["mood"],
            "score": facts["score"],
        },
        "alternatives": [
            {"title": r["song"]["title"], "artist": r["song"]["artist"],
             "score": round(float(r["score"]), 2)}
            for r in ranked[1:]
        ],
        "explanation": attempts[-1]["text"],
        "grounding": {"ratio": attempts[-1]["ratio"],
                      "grounded": attempts[-1]["grounded"],
                      "problems": attempts[-1]["problems"]},
        "attempts": attempts,
        "facts": facts,
        "caveats": [
            f"The catalog has no songs from the {u['value']}; this matches on "
            f"{'genre' if 'jazz' in (request or '').lower() else 'the remaining features'} only."
            for u in nlu_report.get("unmet", [])
        ],
    }

    if trace_path:
        os.makedirs(os.path.dirname(os.path.abspath(trace_path)), exist_ok=True)
        with open(trace_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "ts": _now(), "request": request, "profile": profile_name,
                "status": status, "attempts": [
                    {k: a[k] for k in ("attempt", "provider", "strict", "grounded",
                                       "ratio", "problems")} for a in attempts],
                "recommendation": result["recommendation"],
            }) + "\n")

    return result


def _now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
