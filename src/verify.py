"""Deterministic verifier: does an explanation stay inside the fact sheet?

The model may mention numbers and names; it may not invent them. This module extracts
checkable claims from a sentence and grades each one against the song's row. It is
deliberately rule-based — a second model judging the first one would add a second failure
mode, not remove one.
"""

import re

NUMBER_RE = re.compile(r"(?<![\w.])(\d{1,4}(?:\.\d+)?)(\s?%)?(?![\w.])")
QUOTED_RE = re.compile(r"[\"“']([^\"”']{3,60})[\"”']")
PROPER_RE = re.compile(r"\b([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,}){1,3})\b")

# Words that look like proper nouns but are part of our own vocabulary.
ALLOWED_PROPER = {"VibeFinder", "BPM", "JSON", "CSV", "CLI", "LLM"}

FIELD_HINTS = {
    "energy": ("energy",),
    "tempo": ("tempo", "bpm", "beats per minute"),
    "popularity": ("popularity", "popular"),
    "valence": ("valence", "positivity", "positive"),
    "danceability": ("danceability", "danceable"),
    "acousticness": ("acousticness", "acoustic"),
    "decade": ("decade", "released", "release", "from the", "era", "year"),
    "score": ("score", "match"),
}

FACT_KEY = {"tempo": "tempo_bpm", "decade": "release_decade"}

TOLERANCE = {"energy": 0.06, "valence": 0.06, "danceability": 0.06, "acousticness": 0.06,
             "score": 0.06, "tempo": 2.0, "popularity": 2.0, "decade": 0.0}


def _hint_for(prefix):
    """Return the field whose keyword sits closest to the number.

    Prefixes routinely contain two keywords ("energy of 0.35 and a tempo of 72"), so the
    first match in dict order mislabels the second number. Position beats order.
    """
    prefix = prefix.lower()
    best, best_pos = None, -1
    for field, words in FIELD_HINTS.items():
        for word in words:
            pos = prefix.rfind(word)
            if pos > best_pos:
                best, best_pos = field, pos
    return best


def _number_ok(value, field, facts):
    if field:
        target = facts[FACT_KEY.get(field, field)]
        if field == "decade":
            # "released in 1980" or "1980s" both mean the decade fact.
            return abs(value - target) <= 0.0 or (target <= value <= target + 9)
        return abs(value - target) <= TOLERANCE[field]
    return any(abs(value - facts[FACT_KEY.get(f, f)]) <= TOLERANCE[f] for f in TOLERANCE)


def verify_explanation(text, facts, vocab, threshold=0.8):
    """Grade one explanation. Returns a dict with a verdict and per-claim detail."""
    claims, problems = [], []
    text = text or ""

    for match in NUMBER_RE.finditer(text):
        raw = match.group(1)
        percent = bool(match.group(2))
        prefix = text[max(0, match.start() - 45):match.start()]
        field = _hint_for(prefix)
        value = float(raw)
        if percent:
            value = value / 100.0
            if field in ("energy", "valence", "danceability", "acousticness", "score"):
                pass
        if field is None and not percent and value < 10:
            continue  # "top 3", "5 songs" — not factual claims
        ok = _number_ok(value, field, facts)
        claims.append({"kind": "number", "text": raw + ("%" if percent else ""),
                       "field": field, "ok": ok})
        if not ok:
            problems.append(f"number {raw}{'%' if percent else ''} not supported"
                            + (f" as {field}" if field else ""))

    known = set()
    for group in ("titles", "artists", "tags", "genres", "moods"):
        known |= vocab.get(group, set())

    for quoted in QUOTED_RE.findall(text):
        ok = quoted.strip().lower() in known
        claims.append({"kind": "entity", "text": quoted, "ok": ok})
        if not ok:
            problems.append(f"quoted name not in catalog: {quoted}")

    for proper in PROPER_RE.findall(text):
        cleaned = proper.strip()
        if cleaned in ALLOWED_PROPER:
            continue
        low = cleaned.lower()
        if low in known:
            claims.append({"kind": "entity", "text": cleaned, "ok": True})
        else:
            claims.append({"kind": "entity", "text": cleaned, "ok": False})
            problems.append(f"name not in catalog: {cleaned}")

    if not claims:
        return {"grounded": False, "ratio": 0.0, "claims": [], "problems":
                ["no checkable claims: the explanation makes no verifiable statement"]}

    supported = sum(1 for c in claims if c["ok"])
    ratio = supported / len(claims)
    grounded = ratio >= threshold and not any(
        p.startswith(("quoted name", "name not")) for p in problems)
    return {"grounded": grounded, "ratio": round(ratio, 3), "claims": claims,
            "problems": problems}
