"""Fact sheets: the only evidence an explanation is allowed to use.

An explanation of a recommendation may state numbers (energy, tempo, popularity), names
(genre, mood, decade) and the score. Every one of those must trace back to this module, so
the verifier can check a sentence against the row it supposedly describes.
"""


def song_fact_sheet(result):
    """Flatten one `recommend_songs()` result into the facts a model may cite."""
    song = result["song"]
    return {
        "title": song["title"],
        "artist": song["artist"],
        "genre": song["genre"],
        "mood": song["mood"],
        "energy": float(song["energy"]),
        "tempo_bpm": float(song["tempo_bpm"]),
        "valence": float(song["valence"]),
        "danceability": float(song["danceability"]),
        "acousticness": float(song["acousticness"]),
        "popularity": float(song["popularity"]),
        "release_decade": float(song["release_decade"]),
        "mood_tags": (song.get("mood_tags") if isinstance(song.get("mood_tags"), list)
                      else str(song.get("mood_tags", "")).split("|")),
        "score": round(float(result["score"]), 2),
        "final_score": round(float(result.get("final_score", result["score"])), 2),
        "reasons": list(result.get("reasons", [])),
    }


def fact_sheet(result):
    """Alias kept short for callers that already have a result dict."""
    return song_fact_sheet(result)


def catalog_vocabulary(songs):
    """Every proper noun an explanation is allowed to mention."""
    vocab = {"titles": set(), "artists": set(), "genres": set(), "moods": set(),
             "tags": set()}
    for song in songs:
        vocab["titles"].add(song["title"].strip().lower())
        vocab["artists"].add(song["artist"].strip().lower())
        vocab["genres"].add(song["genre"].strip().lower())
        vocab["moods"].add(song["mood"].strip().lower())
        tags = song.get("mood_tags")
        for tag in (tags if isinstance(tags, list) else str(tags or "").split("|")):
            if tag.strip():
                vocab["tags"].add(tag.strip().lower())
    return vocab


def fact_numbers(facts):
    """Numeric facts keyed by name, for tolerance checks."""
    return {
        "energy": facts["energy"],
        "tempo": facts["tempo_bpm"],
        "popularity": facts["popularity"],
        "valence": facts["valence"],
        "danceability": facts["danceability"],
        "acousticness": facts["acousticness"],
        "decade": facts["release_decade"],
        "score": facts["score"],
    }


def render_fact_block(facts):
    """A compact, prompt-ready statement of what the model may use."""
    tags = ", ".join(t for t in facts["mood_tags"] if t)
    return (
        f"Title: {facts['title']}\n"
        f"Artist: {facts['artist']}\n"
        f"Genre: {facts['genre']}\n"
        f"Mood: {facts['mood']}\n"
        f"Energy: {facts['energy']:.2f}\n"
        f"Tempo: {facts['tempo_bpm']:.0f} BPM\n"
        f"Valence: {facts['valence']:.2f}\n"
        f"Danceability: {facts['danceability']:.2f}\n"
        f"Acousticness: {facts['acousticness']:.2f}\n"
        f"Popularity: {facts['popularity']:.0f}\n"
        f"Release decade: {facts['release_decade']:.0f}\n"
        f"Mood tags: {tags}\n"
        f"Match score: {facts['score']:.2f}\n"
    )
