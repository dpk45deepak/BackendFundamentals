# Prompt to generate this repository with an AI coding agent

Build a production-quality GitHub repository named `senior-backend-ai-learning-workflow`.

## Goal

Create an automated, self-progressing Senior Backend Engineering learning system.

The repository must contain the complete topic roadmap supplied by the user across:

1. Core Backend Fundamentals
2. Databases
3. Caching
4. Messaging & Event-Driven Architecture
5. System Design
6. Distributed Systems
7. Backend Security
8. Reliability Engineering
9. Observability
10. DevOps / Infrastructure
11. Cloud Backend
12. Performance Engineering
13. Architecture Patterns
14. API Architecture
15. Testing
16. Data Engineering Concepts
17. AI Backend

Preserve every topic from the supplied roadmap. Do not silently remove topics.

## Automation behavior

Use GitHub Actions.

Run exactly twice per day:
- 07:00 Asia/Kolkata
- 19:00 Asia/Kolkata

Because GitHub cron uses UTC, use:
- `30 1 * * *`
- `30 13 * * *`

Each run must:
1. Read `data/progress.json`.
2. Find the next two incomplete topics from `data/topics.json`.
3. Call the Gemini API.
4. Generate two detailed Markdown notes under `docs/YYYY-MM-DD/`.
5. Mark those topics completed.
6. Update progress.
7. Commit and push the generated files back to the repository.
8. If fewer than two topics remain, generate only the remaining topics.
9. Once all topics are completed, set `completed: true` and skip future Gemini calls.

Also support `workflow_dispatch` for manual execution.

## Gemini configuration

Use the Gemini REST API from Python.

Secret:
- `GEMINI_API_KEY`

Repository variable:
- `GEMINI_MODEL`

Default model in code if the variable is absent:
- `gemini-2.5-flash`

IMPORTANT:
- Never create or commit `.env`.
- Never hardcode the API key.
- Never print the API key.
- Read the secret only through `${{ secrets.GEMINI_API_KEY }}` and `os.environ["GEMINI_API_KEY"]`.
- Read the non-secret model through `${{ vars.GEMINI_MODEL }}`.

## Lesson quality

Each generated topic note must include:

- What problem it solves
- Mental model
- Deep explanation
- How it works
- Mermaid architecture/sequence diagrams where useful
- Practical TypeScript/Node.js examples
- Relevant PostgreSQL/Redis/Kafka/Python examples when useful
- Production considerations
- Scalability
- Reliability
- Security
- Observability
- Performance
- Common mistakes
- Senior engineer perspective
- 5 interview questions with answer points
- One hands-on task
- Quick revision section
- Trustworthy references

Teach from beginner to advanced, but don't stay shallow. Explain WHY, WHEN, trade-offs,
failure modes, and what changes at scale.

## State design

Use deterministic IDs such as `T001`, `T002`, etc.

`data/topics.json` should contain:
- id
- category
- topic
- status

`data/progress.json` should contain:
- completed_topic_ids
- last_run_utc
- runs
- completed

The workflow must be idempotent enough that reruns don't regenerate already completed topics.

## Repository structure

```text
.
├── .github/
│   └── workflows/
│       └── daily-learning.yml
├── data/
│   ├── topics.json
│   └── progress.json
├── docs/
│   └── YYYY-MM-DD/
├── scripts/
│   └── generate_lessons.py
├── .gitignore
├── requirements.txt
└── README.md
```

## GitHub Actions requirements

Use:
- `actions/checkout@v4`
- `actions/setup-python@v5`
- Python 3.12
- `permissions: contents: write`
- concurrency to prevent overlapping runs

Commit generated changes as:
`docs: generate daily backend lessons`

Use the GitHub Actions bot identity.

## Reliability requirements

- Fail loudly when `GEMINI_API_KEY` is missing.
- Use a reasonable HTTP timeout.
- Handle non-2xx Gemini responses.
- Handle malformed Gemini responses.
- Do not mark a topic complete until its note is successfully written.
- Keep the workflow simple and maintainable.
- Do not add unnecessary cloud services or databases.
- Do not introduce an application server; GitHub Actions is the scheduler.

## README

Explain:
- project purpose
- schedule
- how GitHub Secrets and Variables are configured
- why `.env` is intentionally absent
- local testing
- repository structure
- completion behavior
- how generated lessons are stored

At the end, validate:
- JSON is valid
- Python compiles
- workflow YAML is syntactically correct
- no `.env` file exists
- no API key exists in source
- every supplied topic exists exactly once
- workflow schedules are 7 AM and 7 PM IST
- two topics are generated per run
- completion stops future generation
