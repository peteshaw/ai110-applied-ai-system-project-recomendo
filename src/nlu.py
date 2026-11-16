"""Turn a free-text request into a taste profile, with no model involved.

Deliberately rule-based: the mapping from words to features is inspectable, testable and
cheap, and it keeps the LLM's only job the writing of explanations. Anything the lexicon
cannot recognise is reported back, so the caller can ask a clarifying question instead of
guessing silently.
"""

import re

# Words that imply a target value. Extend with care: every entry is a test case.
ENERGY_WORDS = {
    "gym": 0.9, "workout": 0.9, "run": 0.85, "party": 0.9, "dance": 0.85,
    "energetic": 0.9, "upbeat": 0.8, "hype": 0.9, "club": 0.85,
    "chill": 0.35, "relax": 0.3, "calm": 0.25, "sleep": 0.2, "study": 0.35,
    "focus": 0.4, "reading": 0.35, "rainy": 0.35, "sad": 0.3, "quiet": 0.25,
}

TEMPO_WORDS = {"fast": 135, "pumping": 130, "driving": 125, "slow": 70, "downtempo": 75}

DECADE_WORDS = {
    "60s": 1960, "70s": 1970, "80s": 1980, "90s": 1990, "2000s": 2000,
    "2010s": 2010, "2020s": 2020, "sixties": 1960, "seventies": 1970,
    "eighties": 1980, "nineties": 1990,
}

POPULARITY_WORDS = {"popular": 65, "hits": 70, "mainstream": 70, "obscure": 30,
                    "underground": 25, "deep cut": 30}

STOPWORDS = {
    "a", "an", "and", "as", "at", "be", "for", "from", "i", "in", "is", "it", "like",
    "me", "my", "of", "on", "or", "something", "some", "that", "the", "to", "want",
    "with", "would", "you", "please", "give", "play", "music", "song", "songs", "track",
}


def _catalog_words(songs, field):
    return {str(s[field]).strip().lower() for s in songs if s.get(field)}


def parse_request(text, songs, base_profile=None):
    """Return (prefs, report).

    prefs is a profile dict the recommender understands. report lists what was recognised
    and what was ignored, so the caller can be honest about partial understanding.
    """
    text = (text or "").strip()
    lower = text.lower()
    words = re.findall(r"[a-z0-9']+", lower)

    prefs = dict(base_profile or {})
    matched, ignored = [], []

    genres = _catalog_words(songs, "genre")
    moods = _catalog_words(songs, "mood")
    tags = set()
    for song in songs:
        for tag in str(song.get("mood_tags", "")).split("|"):
            if tag.strip():
                tags.add(tag.strip().lower())

    # Genre and mood: longest phrase first, so compounds win over substrings, but keep
    # scanning — a request can name both ("chill lofi") and each field is set once.
    assigned = set()
    for value in sorted(genres | moods | tags, key=len, reverse=True):
        if not value or value not in lower:
            continue
        if value in genres:
            field = "favorite_genre"
        elif value in moods:
            field = "favorite_mood"
        else:
            field = "mood_tags"
        if field == "mood_tags":
            prefs.setdefault("mood_tags", [])
            if value not in prefs["mood_tags"]:
                prefs["mood_tags"].append(value)
                matched.append(f"tag:{value}")
        elif field not in assigned:
            prefs[field] = value
            assigned.add(field)
            matched.append(f"{field}:{value}")

    for word, energy in ENERGY_WORDS.items():
        if word in words:
            prefs["target_energy"] = energy
            matched.append(f"energy:{word}")
            break

    for word, bpm in TEMPO_WORDS.items():
        if word in words:
            prefs["target_tempo_bpm"] = bpm
            matched.append(f"tempo:{word}")
            break

    unmet = []
    for word, decade in DECADE_WORDS.items():
        if word in words:
            prefs["target_decade"] = decade
            matched.append(f"decade:{word}")
            break
    else:
        # A decade the catalog cannot serve ("1940s") is a partial match, not a silent drop.
        for token in re.findall(r"\b(19|20)\d0s\b", lower):
            pass
        for token in re.findall(r"\b((?:19|20)\d0s)\b", lower):
            if token not in DECADE_WORDS:
                unmet.append({"constraint": "decade", "value": token})

    for word, popularity in POPULARITY_WORDS.items():
        if word.replace(" ", "") in lower.replace(" ", ""):
            prefs["min_popularity"] = popularity
            matched.append(f"popularity:{word}")
            break

    # A word counts as understood if it, or a prefix of it, was used by any match —
    # otherwise "studying" gets reported as ignored after "study" set the target.
    used = {m.split(":", 1)[1] for m in matched if ":" in m}
    used |= {k for k in list(ENERGY_WORDS) + list(TEMPO_WORDS) + list(DECADE_WORDS)
             if any(w.startswith(k) for w in words)}
    for word in words:
        if word in STOPWORDS or len(word) < 3:
            continue
        if any(word.startswith(k) or k.startswith(word) for k in used if len(k) >= 3):
            continue
        if word not in ignored:
            ignored.append(word)

    report = {"matched": matched, "ignored": ignored, "empty": not matched,
              "unmet": unmet}
    return prefs, report
