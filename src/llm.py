"""Explanation providers.

The system talks to a single interface, `explain()`, so the verifier, the retry loop and the
harness are identical whether the writer is a live model or a deterministic stub.

Two stubs ship for tests and offline demos:
  careful — writes only what the fact sheet supports
  sloppy  — invents a release year and a song title, so the verifier has something to catch

The live path uses Gemini when `GEMINI_API_KEY` is set and `google-genai` is installed.
"""

import os

SYSTEM_RULE = (
    "You write short explanations of music recommendations. Use only the facts given. "
    "Never invent a song title, artist, genre, year or number. Two or three sentences."
)


def build_prompt(request, facts, strict=False):
    from .facts import render_fact_block

    request_line = request.strip() or "the listener's saved profile"
    extra = ("\nEvery number you write must appear above, exactly. Do not round. "
             "Do not name any song or artist that is not in the fact block.\n") if strict else ""
    return (f"{SYSTEM_RULE}\n\nListener request: {request_line}\n\n"
            f"Recommendation to explain:\n{render_fact_block(facts)}{extra}"
            f"\nExplanation:")


class Provider:
    name = "provider"

    def explain(self, request, facts, strict=False):
        raise NotImplementedError


class StubProvider(Provider):
    """Deterministic writer used by tests and by offline demos."""

    def __init__(self, behaviour="careful"):
        self.behaviour = behaviour
        self.name = f"stub-{behaviour}"

    def explain(self, request, facts, strict=False):
        if self.behaviour == "sloppy" and not strict:
            return (
                f"\"{facts['title']}\" by {facts['artist']} is a {facts['mood']} "
                f"{facts['genre']} track released in 2019, with an energy of "
                f"{facts['energy']:.2f}. It also pairs well with \"Midnight Velvet\", "
                f"which has a similar feel."
            )
        tags = ", ".join(t for t in facts["mood_tags"][:2] if t) or facts["mood"]
        article = "an" if facts["mood"][:1].lower() in "aeiou" else "a"
        return (
            f"\"{facts['title']}\" by {facts['artist']} is {article} {facts['mood']} "
            f"{facts['genre']} track from the {facts['release_decade']:.0f}s with an energy "
            f"of {facts['energy']:.2f} and a tempo of {facts['tempo_bpm']:.0f} BPM. "
            f"It scores {facts['score']:.2f} against this profile, driven by {tags}."
        )


class GeminiProvider(Provider):
    """Live writer. Raises a clear error when the key or SDK is missing."""

    name = "gemini"

    def __init__(self, model="gemini-2.0-flash"):
        self.model = model
        key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Put it in .env (see .env.example) or use "
                "--provider stub.")
        try:
            from google import genai  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "google-genai is not installed in this interpreter. "
                "Run: pip install -r requirements.txt") from exc
        from google import genai
        self._client = genai.Client(api_key=key)

    def explain(self, request, facts, strict=False):
        prompt = build_prompt(request, facts, strict=strict)
        response = self._client.models.generate_content(
            model=self.model, contents=prompt)
        return (getattr(response, "text", "") or "").strip()


def get_provider(name="stub"):
    if name in ("stub", "stub-careful"):
        return StubProvider("careful")
    if name == "stub-sloppy":
        return StubProvider("sloppy")
    if name == "gemini":
        return GeminiProvider()
    raise ValueError(f"Unknown provider {name!r}. Use stub, stub-sloppy or gemini.")
