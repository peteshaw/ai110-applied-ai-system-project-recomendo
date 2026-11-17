# 🎧 VibeFinder 2.0 — Music Recommendations You Can Trust

VibeFinder is a music recommendation program. It suggests songs based on what a listener likes, then explains why each recommendation is a good match.

**VibeFinder 2.0 checks its explanations before showing them to you.**

The song-recommendation system from VibeFinder 1.0 has not changed. Version 2.0 adds a new process that:

1. Writes an explanation for the top recommended song.
2. Checks the explanation against the song's actual information.
3. Tries once more with stricter instructions if the explanation contains unsupported information.
4. Clearly warns you if the explanation still cannot be verified.

The guiding idea is simple: a recommendation is not complete unless the program can explain it, and that explanation must be checked against real information.

## Project at a glance

| Item | Description |
|---|---|
| Starting project | VibeFinder 1.0, created for the AI110 Module 3 demonstration. It includes 31 songs, a scoring system that weighs different preferences, and a method for avoiding repetitive recommendations. |
| What version 2.0 adds | Understands written requests, writes explanations based on song information, checks those explanations, retries once when needed, and warns when an explanation cannot be confirmed. |
| Main AI feature | A process in which the program checks an AI-written explanation and asks for a corrected version if the first one does not pass. |
| Music collection | 31 songs covering 25 genres and 15 moods. |
| Automated tests | 47 tests that run without an internet connection or an API key. |
| Reliability checks | 16 sample requests tested in two different modes, with pass/fail results and detailed records of what happened. |
| Software requirements | The main program uses Python's included tools. The `google-genai` package is needed only when using Gemini to write live explanations. |

## Background: Why version 2.0 was built

VibeFinder 2.0 builds on **VibeFinder 1.0**, a music recommendation project created for Module 3.

The original program compares every song with a listener's taste preferences. It considers:

- Music genre
- Mood
- Energy level
- Tempo (how fast the music is)
- Danceability
- Acoustic sound
- Popularity
- Era

It then displays the five highest-ranked songs and explains how each song earned its score. The original goal was to make the scoring easy to understand by showing exactly how the score was calculated.

However, the explanations in version 1.0 were written in advance using fixed text templates. Version 2.0 allows an AI language model to write the explanation instead.

That creates a risk: an AI model might make up details that are not in the music collection. For example, it might give a song the wrong release decade, mention a song that is not in the collection, or change a song's energy value to make it sound like a better match.

Version 2.0 is designed to catch those mistakes before the explanation is accepted.

## How the program works

The process follows these steps:

1. **Read the listener's request.** The program accepts an ordinary written request, such as "something chill for studying."
2. **Identify the preferences.** A built-in list of words and rules looks for supported details, such as genre, mood, energy level, or decade. This step does not use an AI model.
3. **Check whether the request can be understood.** If none of the words match information the music collection can use, the program declines the request rather than pretending it understands.
4. **Find matching songs.** The existing VibeFinder 1.0 recommendation system scores and ranks the songs.
5. **Prepare the song's facts.** The program gathers the selected song's actual information and its recommendation score.
6. **Write an explanation.** A test version of the explanation writer or Google Gemini writes an explanation using the supplied facts.
7. **Check the explanation.** A separate set of fixed rules checks whether the numbers and names in the explanation match the music collection.
8. **Retry if necessary.** If the explanation does not pass, the program asks for one new version with stricter instructions.
9. **Show the result honestly.** The program returns an explanation that passes the checks. If the second attempt still fails, it returns the explanation with a warning that it could not be verified.
10. **Save a record.** The program records the steps and results so they can be reviewed later.

The diagram's original source file is `diagrams/architecture.mmd`.

### Why the program uses written rules to understand requests

Turning a request like "something chill for studying" into music preferences is mainly a matter of matching words to known categories. A list of words and rules is a good fit for this job because it can be read, tested, and updated.

Keeping an AI model out of this step also makes mistakes easier to investigate. If the program misunderstands a request, you can trace the result back to the rule that was used.

### Why the explanation checker uses fixed rules

One option would be to ask a second AI model whether the first model's explanation is correct. But the second model could make mistakes too.

Instead, VibeFinder checks the explanation directly against the song information. It compares numbers with the song's stored values and checks names against the music collection. This approach is inexpensive, easy to explain, and produces a consistent result.

## Installation and setup

Run these commands from the project's main folder:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m unittest discover -s tests -v
```

What each command does:

1. Creates a separate Python environment for this project and activates it.
2. Installs the packages listed as project requirements. The main program itself uses Python's included tools; the additional Gemini package is only needed for live explanations.
3. Creates a `.env` settings file from the example. This file is needed only if you want to use live explanations.
4. Runs all 47 automated tests. These tests do not need an API key or an internet connection.

To use Google Gemini for live explanations, provide a Gemini API key using the `GEMINI_API_KEY` setting in the `.env` file or in your environment.

Without a Gemini key, the request parser, recommendation system, explanation checker, retry process, and test harness can all run offline using built-in test versions.

## Try it out

The examples below use the program's built-in test explanation writers. They do not require a Gemini API key.

### 1. A request that is understood and explained correctly

Command:

```text
python -m src.main --request "something chill lofi for studying" --provider stub
```

Example output:

```text
REQUEST: something chill lofi for studying
UNDERSTOOD AS: favorite_mood:chill, favorite_genre:lofi, energy:chill
RETRIEVED NOTES: study_sessions, rainy_afternoons
TOP MATCH: Library Rain — Paper Lanterns (lofi/chill) score 5.00
ALSO CONSIDERED: Midnight Coding (4.86); Spacewalk Thoughts (2.86); Focus Flow (3.90); Coffee Shop Stories (1.96)

EXPLANATION:
  "Library Rain" by Paper Lanterns is a chill lofi track from the 2020s with an energy of
  0.35 and a tempo of 72 BPM. It scores 5.00 against this profile, driven by calm, focused.

VERIFIER: GROUNDED  (claim support 1.00)
ATTEMPTS: 1
```

The program understands the request, recommends a matching song, and produces an explanation whose claims are all supported by the song's information. A claim-support score of `1.00` means every checked claim was supported.

### 2. An explanation that makes things up, then gets corrected

Command:

```text
python -m src.main --request "upbeat pop for the gym" --provider stub-sloppy
```

Example final output:

```text
REQUEST: upbeat pop for the gym
UNDERSTOOD AS: favorite_genre:pop, energy:gym
RETRIEVED NOTES: gym_sessions
TOP MATCH: Gym Hero — Max Pulse (pop/intense) score 3.94

EXPLANATION:
  "Gym Hero" by Max Pulse is an intense pop track from the 2020s with an energy of 0.93
  and a tempo of 132 BPM. It scores 3.94 against this profile, driven by euphoric, confident.
VERIFIER: GROUNDED  (claim support 1.00)
ATTEMPTS: 2  (one retry with a stricter prompt)
```

The first explanation attempt is rejected because it gives an incorrect release year and mentions a song that is not in the collection. The program then tries again with stricter instructions. The final explanation passes.

The saved record includes the failed first attempt as well as the successful retry. This makes it possible to see what went wrong, not just the final answer.

### 3. A request the music collection cannot handle

Command:

```text
python -m src.main --request "polka death metal"
```

Example output:

```text
REQUEST: polka death metal
UNDERSTOOD AS: nothing recognised
IGNORED: polka, death, metal
STATUS: declined — none of those terms map to catalog features.
  None of those terms map to catalog features (genre, mood, energy, tempo, decade, popularity).
```

The program does not invent a result when it cannot match the request to information in its music collection. It explains why it declined.

### 4. A request that can only be partly matched

For example, a request for **"1940s jazz ballads"** returns a jazz song but explains the limitation:

```text
CAVEAT: The catalog has no songs from the 1940s; this matches on genre only.
```

In other words, the program found a match for the music genre, but the collection does not contain songs from the requested decade.

## How the explanation checker works

The checker reads the explanation and looks for details that can be compared with the music collection.

| Type of detail | What the program checks | Example of a mistake it should catch |
|---|---|---|
| Numbers and measurements | The value must be close enough to the value stored for that song. The allowed difference is 0.06 for features measured from 0 to 1, up to 2 for tempo or popularity, and no difference is allowed for the decade. | Saying a song was released in 2019 when the collection places it in the 2020s. |
| Song and artist names | Any quoted song title or artist name must appear in the collection. | Mentioning a song called *Midnight Velvet* when it is not in the collection. |
| Other specific names | Names must match words in the collection, including song titles, artists, genres, moods, and tags. | Calling a song "a Motown classic" when Motown is not part of the collection's information. |

The program calculates a **claim-support score**:

> Number of supported claims ÷ total number of claims

An explanation is accepted when at least **80% of its checkable claims are supported**, provided it does not contain invented names.

If it does not meet that standard, the program tries once more with stricter instructions. If the second attempt still does not pass, the program shows a warning instead of hiding the problem.

The allowed differences for numbers and the acceptance threshold are settings near the top of `src/verify.py`. They can be reviewed and changed.

## Running the tests and reliability checks

Use these commands from the project's main folder:

```bash
python -m unittest discover -s tests -q
python harness.py --provider stub-sloppy
python scripts/compare_prompt_styles.py
```

They do the following:

- **Run the automated tests:** Checks the program's features using 47 tests. No API key is needed.
- **Run the reliability test:** Sends 16 prepared requests through two different explanation methods and reports which results pass or fail.
- **Compare explanation styles:** Compares a general-purpose explanation writer with one that is instructed to use only supplied facts.

### What the automated tests cover

The 47 tests include:

- 32 tests carried over from the original recommendation project.
- 15 new tests covering the added features.

The new tests check that:

- Requests can include both a mood and a genre.
- Unknown words are reported instead of being guessed.
- The program can recognize a requested decade and popularity preference.
- Correct explanations pass the checker.
- Incorrect release years and invented song titles are caught.
- Explanations with no checkable claims are rejected.
- Relevant listener notes are included, while unrelated requests do not retrieve notes.
- A careful explanation writer passes on the first attempt.
- A careless explanation writer can fail once and pass after the stricter retry.
- The program shows a warning when the retry limit is reached.
- The program can run using a saved taste profile without a written request.
- Adding the explanation-checking process does not change which song is recommended; it changes only how the recommendation is explained.

### Reliability test results

The results are saved in `assets/harness_results.md`.

| Test mode | Successful results | What it measures |
|---|---:|---|
| Explanation only | **5 out of 16** | Whether the AI's first explanation can be accepted without checking and retrying. |
| Checked and retried | **16 out of 16** | Whether the full process produces a supported explanation or honestly declines a request it cannot answer. |

With the checking and retry process, ten requests that could be answered went from unsupported explanations to supported ones. Six requests that could not be answered were declined instead of receiving made-up answers.

These tests use `stub-sloppy`, a predictable test version of an explanation writer that deliberately invents a release year and a song title. This makes it possible to repeat the test without an API key.

You can also use `--provider gemini` to send the same 16 requests through a live Gemini model and check its explanations in the same way.

The full results are in `assets/harness_results.md`. Each run also adds records to `assets/agentic_trace.jsonl`. Each record tracks the stages of the process—understanding the request, finding relevant notes, ranking songs, and checking the explanation. It also saves every explanation attempt, including attempts that failed.

### Evidence for the additional project features

| Feature | Where to find evidence |
|---|---|
| **Using extra information to improve recommendations (+2)** | `data/context_notes.json` contains an additional set of listener-context notes. The program looks up relevant notes in `src/agent.py` and displays them in the command-line results. For example: `RETRIEVED NOTES: study_sessions, rainy_afternoons`. |
| **A multi-step AI process (+2)** | `assets/agentic_trace.jsonl` records the intermediate steps, the notes found, the rejected explanation, the stricter retry, and the final decision. `ai_interactions.md` links to and explains this record. |
| **Specialized instructions for the AI (+2)** | `python scripts/compare_prompt_styles.py` compares a general explanation writer with one instructed to use only facts. Across 10 requests, average claim support increased from **0.490 to 1.000**, and invented claims fell from **29 to 0**. Example outputs are in `model_card.md`. |
| **Automated reliability test (+2)** | `python harness.py --provider stub-sloppy` runs 16 prepared requests in two modes and displays a pass/fail summary. The result improved from **5 out of 16 to 16 out of 16**. |

## Design choices and trade-offs

Every design choice has benefits and limitations.

| Choice | Why it was made | Limitation |
|---|---|---|
| Use written rules to understand requests instead of an AI model | The rules can be inspected and tested, they are free to run, and they keep the AI focused on writing explanations. | The program understands only the words and phrases covered by its rules. New wording may need new rules. |
| Check explanations against the music collection instead of asking another AI model to judge them | This avoids relying on a second AI model and makes each checking decision explainable. | It catches factual errors, but it cannot decide whether an opinion or recommendation is good. |
| Retry once, then show a warning | This limits extra processing time and cost while making failures visible. | If the AI still makes unsupported claims after the retry, the result must be shown with a warning. |
| Check only the top recommendation | Each explanation is about one song. Checking every alternative would add work without much benefit. | The other recommended songs are listed, but their explanations are not checked in the same way. |
| Allow explanations to use only facts from the song's record | This makes it possible to check whether an explanation is supported by the stored information. | The explanations may sound a little less lively or natural. |

### What this project intentionally does not include

Some possible additions were left out because they do not solve the main problem this project addresses:

- **Training a custom AI model:** The problem was that explanations could include unsupported details, not that the model lacked general knowledge.
- **Adding advanced similarity-search technology:** The music collection has only about 30 entries. The main problem was the limited set of words the program could recognize, not the difficulty of searching a large collection.
- **Building a graphical interface:** The command-line program is the intended way to use this project.

## Project folder guide

The project files are organized as follows:

```text
ai110-music-final/
├── data/
│   ├── songs.csv                 # The 31-song music collection
│   ├── profiles.json             # Saved listener taste profiles
│   └── context_notes.json        # Extra notes about listening situations
├── src/
│   ├── recommender.py             # The original version 1.0 song scoring and ranking
│   ├── nlu.py                     # Reads written requests and identifies preferences
│   ├── retrieval.py               # Finds relevant listener-context notes
│   ├── facts.py                   # Collects song facts and known names
│   ├── llm.py                     # Connects to test writers or Google Gemini
│   ├── verify.py                  # Checks explanation details against the collection
│   ├── agent.py                   # Runs the recommend, explain, check, and retry process
│   └── main.py                    # Starts the program and handles command-line options
├── harness.py                     # Runs the 16-request reliability test and saves results
├── scripts/
│   └── compare_prompt_styles.py   # Compares two ways of instructing the explanation writer
├── tests/                          # The 47 automated tests
├── diagrams/
│   └── architecture.mmd           # Source file for the process diagram
├── assets/                         # Test results and records of program runs
├── model_card.md
└── README.md
```

## What this project demonstrates

This project shows the difference between an AI feature that looks good in a demonstration and one that can be checked for accuracy.

The most important work was not simply writing better instructions for the AI. It was deciding which facts the AI was allowed to use, building a straightforward way to check its statements, and keeping a record when an explanation failed.

The reliability test makes the improvement measurable: the explanation-only approach passed **5 out of 16** requests, while the complete checking-and-retry process passed **16 out of 16**.

That evidence is more useful than simply saying the system seems better.

## Presentation outline (5–7 minutes)

1. **Introduce the original system and its weakness (1 minute).** Explain how version 1.0 recommended songs and why its prewritten explanations were a limitation.
2. **Show how an AI explanation can get details wrong (1 minute).** Use an example of an explanation that includes a false fact about the music collection.
3. **Explain the new process (2 minutes).** Walk through the steps: understand the request, find related notes, recommend a song, collect its facts, write an explanation, check it, and retry if needed. Demonstrate how the program catches and corrects a careless explanation.
4. **Show the reliability results (1 minute).** Compare the results: 5 out of 16 without checking versus 16 out of 16 with checking and retrying. Explain why six requests were declined.
5. **Discuss what still has limitations (1 minute).** Mention the limited vocabulary, the allowed differences in numeric checks, and the fact that the program retries only once.
6. **Describe possible next steps (30 seconds).** Run the reliability test with a live AI model, check explanations for alternative songs, and use a more precise format for numerical claims.
