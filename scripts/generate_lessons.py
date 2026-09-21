#!/usr/bin/env python3
"""
Generate two senior-backend learning notes per GitHub Actions run using Gemini.

No .env file is used. The API key is read from GEMINI_API_KEY.
Non-secret configuration can be supplied via GEMINI_MODEL.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
TOPICS_FILE = ROOT / "data" / "topics.json"
PROGRESS_FILE = ROOT / "data" / "progress.json"
DOCS_DIR = ROOT / "docs"

API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
LESSONS_PER_RUN = 2

if not API_KEY:
    print("ERROR: GEMINI_API_KEY is not configured.", file=sys.stderr)
    sys.exit(1)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")[:90]


def select_topics(topics: list[dict], progress: dict) -> list[dict]:
    completed = set(progress.get("completed_topic_ids", []))
    return [t for t in topics if t["id"] not in completed and t["status"] != "completed"][:LESSONS_PER_RUN]


def build_prompt(topic: dict, all_topics: list[dict]) -> str:
    roadmap_position = next(
        i for i, item in enumerate(all_topics, 1) if item["id"] == topic["id"]
    )
    return f"""
You are the AI instructor for a long-term Senior Backend Engineering curriculum.

Current lesson:
- Roadmap position: {roadmap_position}/{len(all_topics)}
- Category: {topic["category"]}
- Topic: {topic["topic"]}

The learner is a developer who works with TypeScript/Node.js, Next.js, Python/FastAPI,
PostgreSQL, MongoDB, Redis and AI backends. Teach from first principles, then move to
production-level engineering depth.

Generate ONE self-contained Markdown study note.

Required structure:
# {topic["topic"]}

## 1. What problem does this solve?
Explain the motivation before terminology.

## 2. Mental model
Use a simple analogy and then the precise engineering model.

## 3. Deep explanation
Explain internals, trade-offs, failure modes, and where this concept fits in a backend stack.

## 4. How it works
Show a numbered flow. Include Mermaid when a sequence/architecture diagram helps.

## 5. Practical implementation
Use TypeScript/Node.js examples by default. Add SQL, Redis, Kafka, HTTP, Docker,
or Python examples only when they materially improve understanding.
Code should be runnable or close to runnable, with comments explaining important lines.

## 6. Production considerations
Cover scalability, reliability, security, observability, performance, and operational concerns
that are relevant to this topic.

## 7. Common mistakes
List mistakes beginners and intermediate developers commonly make.

## 8. Senior engineer perspective
Explain what changes when this is used at scale and what design decisions a senior engineer
would explicitly consider.

## 9. Interview questions
Give 5 questions:
- 2 beginner/intermediate
- 2 senior-level
- 1 scenario/debugging question
Include concise answer points after each.

## 10. Hands-on task
Give one practical task that can be completed in this repository or a small local Node.js project.

## 11. Quick revision
Provide 8–12 concise bullet points.

## 12. References
Provide trustworthy official/documentation references as plain URLs when known.
Do not invent URLs.

Quality rules:
- Do not make the lesson shallow or generic.
- Do not merely define terms; explain WHY and WHEN.
- Distinguish similar concepts explicitly.
- Mention important trade-offs rather than pretending one approach is universally best.
- Prefer concrete backend examples.
- Do not claim a feature or API exists if uncertain.
- Do not include secrets.
- Return only Markdown for the lesson, without wrapping the entire answer in a code fence.
""".strip()


def call_gemini(prompt: str) -> str:
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{MODEL}:generateContent?key={API_KEY}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.35,
            "topP": 0.9,
            "maxOutputTokens": 7000,
        },
    }
    response = requests.post(
        url,
        json=payload,
        timeout=120,
        headers={"Content-Type": "application/json"},
    )
    if not response.ok:
        raise RuntimeError(
            f"Gemini API failed ({response.status_code}): {response.text[:1000]}"
        )

    data = response.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected Gemini response: {json.dumps(data)[:1500]}") from exc


def main() -> None:
    topics = load_json(TOPICS_FILE)
    progress = load_json(PROGRESS_FILE)

    if progress.get("completed"):
        print("Roadmap already completed. Nothing to generate.")
        return

    selected = select_topics(topics, progress)
    if not selected:
        progress["completed"] = True
        save_json(PROGRESS_FILE, progress)
        print("No pending topics remain. Marked roadmap complete.")
        return

    now = datetime.now(timezone.utc)
    date_dir = DOCS_DIR / now.strftime("%Y-%m-%d")
    date_dir.mkdir(parents=True, exist_ok=True)

    generated_ids = []
    for topic in selected:
        print(f"Generating: {topic['id']} — {topic['topic']}")
        markdown = call_gemini(build_prompt(topic, topics))

        filename = f"{topic['id']}-{slugify(topic['topic'])}.md"
        output = date_dir / filename

        header = (
            f"<!-- Generated by Gemini via GitHub Actions -->\n"
            f"<!-- Topic ID: {topic['id']} -->\n"
            f"<!-- Category: {topic['category']} -->\n"
            f"<!-- Generated at UTC: {now.isoformat()} -->\n\n"
        )
        output.write_text(header + markdown + "\n", encoding="utf-8")

        topic["status"] = "completed"
        generated_ids.append(topic["id"])

    completed = set(progress.get("completed_topic_ids", []))
    completed.update(generated_ids)

    progress["completed_topic_ids"] = sorted(completed)
    progress["last_run_utc"] = now.isoformat()
    progress["runs"] = int(progress.get("runs", 0)) + 1
    progress["completed"] = len(completed) >= len(topics)

    save_json(TOPICS_FILE, topics)
    save_json(PROGRESS_FILE, progress)

    print(
        f"Generated {len(generated_ids)} topic(s). "
        f"Progress: {len(completed)}/{len(topics)}. "
        f"Completed={progress['completed']}"
    )


if __name__ == "__main__":
    main()
