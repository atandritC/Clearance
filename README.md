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
- A Groq API key for the later model integration steps

### Local services

1. Install the locked Python dependencies with `uv sync`.
2. Create a `.env` file in the project root with `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD`. Keep this file local; `.env` is ignored by Git.
3. Start PostgreSQL and Qdrant with `docker compose up -d`.
4. Apply the database migrations with `uv run alembic upgrade head`. This creates the `users` and `knowledge_documents` tables.
5. Add the fictional local users with `uv run python scripts/seed_demo_users.py`. It skips users that already exist.
6. Import document details into PostgreSQL with `uv run python scripts/import_knowledge_metadata.py`. The current corpus has 41 document versions.
7. Create the Qdrant collection with `uv run python scripts/create_qdrant_collection.py`.
8. Index the source corpus with `uv run python scripts/index_knowledge_base.py`. FastEmbed creates vectors locally; the first run downloads its model. At this checkpoint, the corpus produces 44 searchable chunks.
9. Run `uv run pytest -q` to check that search excludes other-department, restricted, and superseded documents.
10. Check service state with `docker compose ps`. PostgreSQL is published on `127.0.0.1:5433`; Qdrant is published on `127.0.0.1:6333` (HTTP) and `127.0.0.1:6334` (gRPC).
11. Start the API with `uv run fastapi dev src/clearance/main.py`. It listens on `http://127.0.0.1:8000` and provides interactive API docs at `/docs`.
12. Check `curl http://127.0.0.1:8000/health` and `curl http://127.0.0.1:8000/ready`. The first checks that the API responds; the second also checks its Postgres connection.
13. In demo mode, `GET /demo/users` lists the fictional users, `GET /demo/whoami` accepts the `X-Demo-User-ID` header to select one, and `GET /demo/search` searches the indexed documents for that user. These routes are a local learning shortcut, not production sign-in. Stop the API with `Ctrl+C`.
14. Stop PostgreSQL and Qdrant with `docker compose down`. Named volumes keep local database and vector data across container restarts.

The `User` and `KnowledgeDocument` tables are described in `src/clearance/models.py`, and Alembic migration files under `migrations/` keep database layout changes repeatable. PostgreSQL stores document details and versions; Qdrant stores searchable text chunks, their vectors, and search metadata. The demo search route filters to active company documents and documents from the selected user's department; restricted documents remain excluded until explicit grants are implemented. Demo identity selection is a local learning shortcut, not production sign-in. Production authentication, answer generation, tools, and the web interface are not implemented yet. Keep credentials in `.env`; never commit API keys or other secrets.

## Evaluation results

No measurements are reported yet. At the evaluation checkpoint, record real values with their test-set size and method:

| Metric | Result | Dataset / method |
|---|---:|---|
| Retrieval precision | Not measured | Pending |
| Retrieval recall | Not measured | Pending |
| Faithfulness | Not measured | Pending |
| Leakage rate | Not measured | Pending |
| p50 / p95 latency | Not measured | Pending |
| Cost per question | Not measured | Pending |

## Architecture

An architecture diagram will be added after the end-to-end flow is implemented and verified, so the diagram reflects the actual system rather than a speculative design.
