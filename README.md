# 🛡️ Senior Backend Engineering — AI Daily Learning Workflow

An automated GitHub repository that teaches the complete senior-backend roadmap using the Gemini API.

## What it does ✅

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

---

<div align="center">

### Made with 💙 and lots of ☕ by [Deepak Kumar](https://github.com/dpk45deepak)

**Learn. Build. Break. Debug. Repeat. 🚀**

</div>




