# Clearance

Clearance is a learning project for a permission-aware company knowledge assistant. It answers questions from a fictional company's internal documents, cites its sources, and limits retrieval and tools using the authenticated user's access.

> **Synthetic data only:** The company and all policies, people, projects, and figures in this repository are fictional. Do not add real company or personal documents.

## What the project demonstrates

- Retrieval-augmented generation over versioned company documents.
- Server-side access filters derived from authenticated identity.
- Role-specific answers with citations and safe abstention.
- Permission checks inside HR and IT tools exposed through MCP.
- Evaluation of retrieval quality, faithfulness, leakage rate, latency, and cost per question.

## Learning workflow

The project is built in small, verified steps. This README will be updated at each checkpoint with verified setup instructions, design decisions, and measured results.

## Synthetic knowledge base

`CLEARANCE_SYNTHETIC_KNOWLEDGE_BASE.md` contains fictional Company, People Operations, IT Operations, Finance, and Product Strategy records. It includes department and restricted material, active and superseded versions, effective dates, and evaluation prompts. The app must use trusted server-side identity to filter this material.

## Stack

Python, FastAPI, Pydantic v2, SQLAlchemy, Alembic, PostgreSQL, Qdrant, FastEmbed, LangGraph, an MCP server, Groq, React + Vite, Docker Compose, and EC2 deployment. Package versions and provider limits will be checked against current official documentation when each installation or integration step begins.

## Setup and run

### Prerequisites

- Python 3.14.10 and `uv`
- Docker Desktop with Docker Compose
- A Groq API key

### Local services

1. Install the locked Python dependencies with `uv sync`.
2. Copy `.env.example` to `.env`, then set the PostgreSQL password, Groq API key, and a private random `JWT_SECRET_KEY` (at least 32 characters). Keep `.env` local; it is ignored by Git.
3. Start PostgreSQL and Qdrant with `docker compose up -d`.
4. Apply the database migrations with `uv run alembic upgrade head`. This creates the user, document, and per-user document-grant tables and adds the account security fields.
5. Add or update the fictional local users with `uv run python scripts/seed_demo_users.py`. It asks for one local demo password (at least 12 characters) and saves only its Argon2 hash for all six demo accounts. The Sofia Gigante account is marked as the local knowledge administrator. Run the script again to reset their shared local password and account setup.
6. Import document details into PostgreSQL with `uv run python scripts/import_knowledge_metadata.py`. The current corpus has 41 document versions.
7. Create the Qdrant collection with `uv run python scripts/create_qdrant_collection.py`.
8. Index the source corpus with `uv run python scripts/index_knowledge_base.py`. FastEmbed creates vectors locally; the first run downloads its model. At this checkpoint, the corpus produces 44 searchable chunks.
9. Run `uv run pytest -q` to check retrieval filters and grants, password and token checks, answer citations, and Groq usage handling.
10. Check service state with `docker compose ps`. PostgreSQL is published on `127.0.0.1:5433`; Qdrant is published on `127.0.0.1:6333` (HTTP) and `127.0.0.1:6334` (gRPC).
11. Start the API with `uv run fastapi dev src/clearance/main.py`. It listens on `http://127.0.0.1:8000` and provides interactive API docs at `/docs`.
12. Check `curl http://127.0.0.1:8000/health` and `curl http://127.0.0.1:8000/ready`. The first checks that the API responds; the second also checks its Postgres connection.
13. In demo mode, `GET /demo/users` lists the fictional users, `GET /demo/whoami` accepts the `X-Demo-User-ID` header to select one, and `GET /demo/search` searches the indexed documents for that user. These routes are a local learning shortcut, not production sign-in.
14. Run `uv run python scripts/groq_baseline.py` to make two short Groq calls and view their answers, token counts, response time, and estimated cost. The results are sample observations, not an answer-quality evaluation.
15. Ask from the indexed corpus with `curl -X POST http://127.0.0.1:8000/demo/ask -H 'Content-Type: application/json' -H 'X-Demo-User-ID: 2' -d '{"question":"Where should employees report an IT incident?"}'`. This demo route uses filtered search, returns citations only from retrieved chunks, and abstains when it lacks authorized evidence.
16. Sign in with `curl -X POST http://127.0.0.1:8000/auth/login -H 'Content-Type: application/json' -d '{"email":"mikasa.ackerman@astervale.example","password":"YOUR_LOCAL_DEMO_PASSWORD"}'`. The response contains a short-lived bearer token.
17. Send an authenticated ask with `curl -X POST http://127.0.0.1:8000/api/ask -H 'Content-Type: application/json' -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' -d '{"question":"Where should employees report an IT incident?"}'`. The API loads the active account from PostgreSQL for each request; it does not trust role or department values from the token or request.
18. Check the signed-in identity with `curl http://127.0.0.1:8000/auth/me -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'`.
19. Give one user access to the active restricted HR-005 version with `curl -X POST http://127.0.0.1:8000/api/admin/documents/HR-005/versions/1.0/grants -H 'Content-Type: application/json' -H 'Authorization: Bearer SOFIA_ADMIN_TOKEN' -d '{"user_id":TARGET_USER_ID}'`. Replace the placeholders with Sofia's access token and a real user ID. Only an administrator can create, list, or revoke grants; `GET` on that same URL lists grants and `DELETE` on the URL ending in `/TARGET_USER_ID` revokes one.
20. Stop the API with `Ctrl+C`, then stop PostgreSQL and Qdrant with `docker compose down`. Named volumes keep local database and vector data across container restarts.

The `User`, `KnowledgeDocument`, and `KnowledgeDocumentGrant` tables are described in `src/clearance/models.py`, and Alembic migrations under `migrations/` keep database layout changes repeatable. PostgreSQL stores document details, versions, and per-user grants; Qdrant stores searchable text chunks, vectors, and search metadata. Passwords are stored as Argon2 hashes. `POST /auth/login` issues a short-lived signed token; protected routes check that token and load the current active user record from PostgreSQL. Retrieval allows active company documents, same-department documents, and active restricted versions explicitly granted to that user. Admin-only endpoints can list, add, and revoke grants; grants for old document versions do not expose superseded content. Both ask routes use only filtered results to create a structured Groq answer, check citation IDs against retrieved chunks, and abstain when they lack valid evidence. The `X-Demo-User-ID` header remains a local learning shortcut. Specialist tools and the web interface are not implemented yet. Keep credentials in `.env`; never commit API keys or other secrets.

## Evaluation results

No project evaluation measurements are reported yet. At the evaluation checkpoint, record real values with their test-set size and method:

| Metric | Result | Dataset / method |
|---|---:|---|
| Retrieval precision | Not measured | Pending |
| Retrieval recall | Not measured | Pending |
| Faithfulness | Not measured | Pending |
| Leakage rate | Not measured | Pending |
| p50 / p95 latency | Not measured | Pending |
| Cost per question | Not measured | Pending |

The Groq baseline makes two sample calls at temperatures 0.0 and 0.7. On the development run, both returned the instructed safe fallback for a question with no source text. Their estimated costs were about $0.000038 and $0.000035. A separate live check confirmed that the configured model accepts the strict structured response schema and returns the requested answer and citation ID for supplied synthetic evidence. These checks confirm connectivity and response formatting; they are not an answer-quality evaluation.

## Architecture

An architecture diagram will be added after the end-to-end flow is implemented and verified, so the diagram reflects the actual system rather than a speculative design.
