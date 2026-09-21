# Senior Backend Engineering — AI Daily Learning Workflow

An automated GitHub repository that teaches the complete senior-backend roadmap using the Gemini API.

## What it does

- Runs **twice every day** at **7:00 AM and 7:00 PM IST**.
- Each run generates **2 topic notes** using Gemini.
- Topics are consumed in deterministic order and never repeated after completion.
- Stops generating new lessons once every topic is completed.
- Commits generated Markdown notes and progress back to the repository.
- Keeps the Gemini API key only in **GitHub Actions Secrets** — there is **no `.env` file**.
- Uses a GitHub Actions repository variable for non-secret configuration such as the Gemini model.
- Each lesson contains:
  - beginner-friendly mental model
  - deep explanation
  - request/response or architecture flow
  - Mermaid diagrams where useful
  - production examples
  - TypeScript/Node.js examples
  - PostgreSQL/Redis/Kafka examples when relevant
  - common mistakes
  - senior-level interview questions
  - hands-on task
  - recap / key takeaways
  - references

## GitHub configuration

Create:

### Secret
`GEMINI_API_KEY`

Path:
**Repository → Settings → Secrets and variables → Actions → Secrets**

### Repository variable
`GEMINI_MODEL`

Suggested value:
`gemini-2.5-flash`

Path:
**Repository → Settings → Secrets and variables → Actions → Variables**

The workflow never writes the API key into the repository.

## Schedule

GitHub Actions cron uses UTC.

- `30 1 * * *` → 7:00 AM IST
- `30 13 * * *` → 7:00 PM IST

GitHub-hosted scheduled workflows can occasionally start later than the scheduled time because of platform load.

## Manual run

The workflow supports `workflow_dispatch`, so you can trigger it manually from the Actions tab.

## Local test

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

For local testing, set `GEMINI_API_KEY` in your shell rather than committing a secret. The repository itself intentionally contains no `.env` file.

```bash
python scripts/generate_lessons.py
```

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

## Completion model

There are **303 topics** in the roadmap. At 2 topics per run and 2 runs per day, the normal maximum is 4 topics/day. The final run automatically handles the remaining 1–2 topics and then marks the roadmap complete.

The workflow also checks `data/progress.json` before calling Gemini, so completed repositories do not continue consuming API calls.
