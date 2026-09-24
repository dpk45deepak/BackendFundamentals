"""
Generate two senior-backend learning notes per GitHub Actions run using Groq.

No .env file is used.

The API key is read from:
    GROQ_API_KEY

The model is read from:
    GROQ_MODEL

If GROQ_MODEL is not configured, the default model is:
    openai/gpt-oss-20b
"""

from __future__ import annotations

import json
import os
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


# Paths

ROOT = Path(__file__).resolve().parents[1]

TOPICS_FILE = ROOT / "data" / "topics.json"
PROGRESS_FILE = ROOT / "data" / "progress.json"
DOCS_DIR = ROOT / "docs"


# Groq configuration

API_KEY = os.environ.get("GROQ_API_KEY")

MODEL = os.environ.get("GROQ_MODEL") or "openai/gpt-oss-20b"

LESSONS_PER_RUN = 2

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


if not API_KEY:
    print(
        "ERROR: GROQ_API_KEY is not configured.",
        file=sys.stderr,
    )
    sys.exit(1)


# Utility functions

def load_json(path: Path) -> Any:
    """Load and parse a JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    """Save data as formatted JSON."""
    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def slugify(value: str) -> str:
    """Convert a topic name into a filesystem-safe slug."""
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")[:90]


# Topic selection

def select_topics(
    topics: list[dict],
    progress: dict,
) -> list[dict]:
    """
    Select the next incomplete topics.

    Topics are processed in deterministic order and already completed
    topics are skipped.
    """

    completed = set(
        progress.get("completed_topic_ids", [])
    )

    return [
        topic
        for topic in topics
        if topic["id"] not in completed
        and topic["status"] != "completed"
    ][:LESSONS_PER_RUN]


# Prompt generation

def build_prompt(
    topic: dict,
    all_topics: list[dict],
) -> str:
    """Build the lesson-generation prompt."""

    roadmap_position = next(
        i
        for i, item in enumerate(all_topics, 1)
        if item["id"] == topic["id"]
    )

    return f"""
You are the AI instructor for a long-term Senior Backend Engineering curriculum.

Current lesson:
- Roadmap position: {roadmap_position}/{len(all_topics)}
- Category: {topic["category"]}
- Topic: {topic["topic"]}

The learner is a developer who works with TypeScript/Node.js, Next.js,
Python/FastAPI, PostgreSQL, MongoDB, Redis and AI backends.

Teach from first principles, then move to production-level engineering depth.

Generate ONE self-contained Markdown study note.

Required structure:

# {topic["topic"]}

## 1. What problem does this solve?

Explain the motivation before terminology.

Explain:
- What problem exists
- Why the problem matters
- What happens if this concept is not used
- Where this concept appears in real backend systems

## 2. Mental model

Use a simple analogy and then the precise engineering model.

The analogy should help a beginner understand the concept before
introducing deeper technical terminology.

## 3. Deep explanation

Explain:

- Internals
- Important terminology
- Trade-offs
- Failure modes
- Limitations
- Where this concept fits in a backend architecture
- How it interacts with related backend concepts

## 4. How it works

Show a numbered step-by-step flow.

Include Mermaid diagrams when a sequence, request flow,
architecture, or distributed-system interaction benefits from one.

Use valid Mermaid syntax.

## 5. Practical implementation

Use TypeScript/Node.js examples by default.

Add SQL, Redis, Kafka, HTTP, Docker, or Python examples only
when they materially improve understanding.

Code should be runnable or close to runnable.

Add comments explaining important lines.

Prefer realistic backend examples rather than toy examples.

## 6. Production considerations

Cover relevant concerns such as:

- Scalability
- Reliability
- Security
- Observability
- Performance
- Error handling
- Resource usage
- Operational concerns
- Failure recovery
- Deployment considerations

Do not force irrelevant sections when they do not apply.

## 7. Common mistakes

List mistakes beginners and intermediate developers commonly make.

Explain why each mistake is problematic.

## 8. Senior engineer perspective

Explain what changes when this concept is used at scale.

Discuss the design decisions a senior engineer would explicitly consider.

Include:

- Architecture decisions
- Trade-offs
- Bottlenecks
- Failure scenarios
- Monitoring
- Cost/performance considerations
- When NOT to use the approach

## 9. Interview questions

Give exactly 5 questions:

- 2 beginner/intermediate
- 2 senior-level
- 1 scenario/debugging question

Include concise answer points after each question.

## 10. Hands-on task

Give one practical task that can be completed in this repository
or a small local Node.js project.

The task should require actually implementing or experimenting
with the concept.

## 11. Quick revision

Provide 8–12 concise bullet points.

These should be useful for quick interview revision.

## 12. References

Provide trustworthy official/documentation references as plain URLs
when known.

Do not invent URLs.

Prefer official documentation.

Quality rules:

- Do not make the lesson shallow or generic.
- Do not merely define terms.
- Explain WHY and WHEN.
- Distinguish similar concepts explicitly.
- Mention important trade-offs.
- Do not pretend one approach is universally best.
- Prefer concrete backend examples.
- Explain production implications.
- Do not claim a feature or API exists if uncertain.
- Do not include secrets.
- Do not fabricate documentation URLs.
- Keep examples technically realistic.
- Return only Markdown for the lesson.
- Do not wrap the entire answer in a code fence.
""".strip()


# Groq API

def call_groq(prompt: str) -> str:
    """
    Call the Groq Chat Completions API.

    Includes:
    - HTTP timeout
    - Retry handling
    - Exponential backoff
    - Jitter
    - Retry-After support
    - Handling for 429 and temporary server errors
    """

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "temperature": 0.35,
        "top_p": 0.9,
        "max_tokens": 7000,
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    retryable_statuses = {
        429,  # Rate limit / temporary capacity
        500,  # Internal server error
        502,  # Bad gateway
        503,  # Service unavailable
        504,  # Gateway timeout
    }

    max_attempts = 6

    for attempt in range(1, max_attempts + 1):

        try:
            response = requests.post(
                GROQ_API_URL,
                json=payload,
                headers=headers,
                timeout=180,
            )

        except requests.RequestException as exc:

            if attempt == max_attempts:
                raise RuntimeError(
                    f"Groq request failed after "
                    f"{max_attempts} attempts: {exc}"
                ) from exc

            # Exponential backoff:
            #
            # attempt 1 -> ~1 second
            # attempt 2 -> ~2 seconds
            # attempt 3 -> ~4 seconds
            # attempt 4 -> ~8 seconds
            # attempt 5 -> ~16 seconds
            #
            # Add jitter so multiple requests do not retry
            # at exactly the same time.

            delay = min(
                60,
                2 ** (attempt - 1),
            ) + random.uniform(0, 1)

            print(
                f"Groq network error: {exc}. "
                f"Retrying in {delay:.1f}s "
                f"(attempt {attempt}/{max_attempts})",
                file=sys.stderr,
            )

            time.sleep(delay)
            continue

        # Successful response

        if response.ok:

            try:
                data = response.json()
            except ValueError as exc:
                raise RuntimeError(
                    "Groq returned an invalid JSON response."
                ) from exc

            try:
                content = data["choices"][0]["message"]["content"]

            except (
                KeyError,
                IndexError,
                TypeError,
            ) as exc:

                raise RuntimeError(
                    "Unexpected Groq response: "
                    f"{json.dumps(data)[:2000]}"
                ) from exc

            if not content or not content.strip():
                raise RuntimeError(
                    "Groq returned an empty response."
                )

            return content.strip()

        # Non-retryable error

        if response.status_code not in retryable_statuses:

            raise RuntimeError(
                f"Groq API failed "
                f"({response.status_code}): "
                f"{response.text[:1500]}"
            )

        # Retryable error

        if attempt == max_attempts:

            raise RuntimeError(
                f"Groq API failed after "
                f"{max_attempts} attempts "
                f"({response.status_code}): "
                f"{response.text[:1500]}"
            )

        # Groq may provide Retry-After.
        #
        # If available, respect it.
        # Otherwise use exponential backoff.

        retry_after = response.headers.get("retry-after")

        try:
            delay = (
                float(retry_after)
                if retry_after
                else 2 ** (attempt - 1)
            )

        except ValueError:
            delay = 2 ** (attempt - 1)

        # Prevent an unexpectedly large server-provided value
        # from making GitHub Actions wait forever.

        delay = min(60, delay)

        # Add small random jitter.

        delay += random.uniform(0, 1)

        print(
            f"Groq returned HTTP "
            f"{response.status_code}. "
            f"Retrying in {delay:.1f}s "
            f"(attempt {attempt}/{max_attempts})",
            file=sys.stderr,
        )

        time.sleep(delay)

    raise RuntimeError(
        "Groq request failed unexpectedly."
    )


# Main workflow

def main() -> None:
    """Generate lessons and update repository progress."""

    topics = load_json(TOPICS_FILE)
    progress = load_json(PROGRESS_FILE)

    # Check completion

    if progress.get("completed"):
        print(
            "Roadmap already completed. "
            "Nothing to generate."
        )
        return

    # Select next topics

    selected = select_topics(
        topics,
        progress,
    )

    if not selected:

        progress["completed"] = True

        save_json(
            PROGRESS_FILE,
            progress,
        )

        print(
            "No pending topics remain. "
            "Marked roadmap complete."
        )

        return

    # Create today's documentation directory

    now = datetime.now(timezone.utc)

    date_dir = (
        DOCS_DIR
        / now.strftime("%Y-%m-%d")
    )

    date_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    generated_ids: list[str] = []

    # Generate lessons

    for topic in selected:

        print(
            f"Generating: "
            f"{topic['id']} — "
            f"{topic['topic']}"
        )

        prompt = build_prompt(
            topic,
            topics,
        )

        markdown = call_groq(prompt)

        # Generate filename

        filename = (
            f"{topic['id']}-"
            f"{slugify(topic['topic'])}.md"
        )

        output = date_dir / filename

        # Add metadata header

        header = (
            "<!-- Generated by Groq via GitHub Actions -->\n"
            f"<!-- Topic ID: {topic['id']} -->\n"
            f"<!-- Category: {topic['category']} -->\n"
            f"<!-- Generated at UTC: {now.isoformat()} -->\n\n"
        )

        # Write lesson

        output.write_text(
            header + markdown + "\n",
            encoding="utf-8",
        )

        # IMPORTANT:
        #
        # Topic is marked completed ONLY after the Markdown file
        # has been successfully written.

        topic["status"] = "completed"

        generated_ids.append(
            topic["id"]
        )

    # Update progress

    completed = set(
        progress.get(
            "completed_topic_ids",
            [],
        )
    )

    completed.update(
        generated_ids
    )

    progress["completed_topic_ids"] = sorted(
        completed
    )

    progress["last_run_utc"] = (
        now.isoformat()
    )

    progress["runs"] = int(
        progress.get("runs", 0)
    ) + 1

    progress["completed"] = (
        len(completed)
        >= len(topics)
    )

    # Persist changes

    save_json(
        TOPICS_FILE,
        topics,
    )

    save_json(
        PROGRESS_FILE,
        progress,
    )

    # Final output
    print(
        f"Generated {len(generated_ids)} topic(s). "
        f"Progress: {len(completed)}/{len(topics)}. "
        f"Completed={progress['completed']}"
    )

if __name__ == "__main__":
    main()
