"""Small custom retrieval layer for listener context notes.

The notes are deliberately separate from the song catalog: they describe *when* music
works, not which songs exist. Retrieval is lexical and inspectable, like the intent parser,
and the retrieved note is passed to the explanation writer as evidence.
"""

import json
import os
import re

NOTES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                          "data", "context_notes.json")


def load_notes(path=NOTES_PATH):
    """Load context notes, failing loudly on malformed data."""
    with open(path, encoding="utf-8") as handle:
        notes = json.load(handle)
    if not isinstance(notes, dict) or not notes:
        raise ValueError(f"{path}: expected a non-empty object of context notes")
    for key, note in notes.items():
        if not isinstance(note, dict) or not note.get("note") or not note.get("tags"):
            raise ValueError(f"{path}: note {key!r} needs 'note' and 'tags'")
    return notes


def retrieve_notes(text, notes, limit=2):
    """Return the most relevant notes as [(key, note), ...], highest score first."""
    words = set(re.findall(r"[a-z0-9']+", (text or "").lower()))
    scored = []
    for key, note in notes.items():
        tags = {str(tag).lower() for tag in note["tags"]}
        overlap = words & tags
        if overlap:
            scored.append((len(overlap), key, note))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [(key, note) for _, key, note in scored[:limit]]


def render_notes(matches):
    """Render retrieved notes for a prompt or a terminal report."""
    if not matches:
        return "No context note matched this request."
    return "\n".join(f"- {note['title']}: {note['note']}" for _, note in matches)
