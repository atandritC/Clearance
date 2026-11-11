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

Python, FastAPI, Pydantic v2, PostgreSQL, Qdrant, LangGraph, an MCP server, Groq, a local embedding model, React + Vite, Docker Compose, and EC2 deployment. Package versions and provider limits will be checked against current official documentation when each installation or integration step begins.

## Setup and run

### Prerequisites

- Python 3.14.10 and `uv`
- Docker Desktop with Docker Compose
- A Groq API key for the later model integration steps

### Local services

1. Create a `.env` file in the project root with `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD`. Keep this file local; `.env` is ignored by Git.
2. Start PostgreSQL and Qdrant with `docker compose up -d`.
3. Check service state with `docker compose ps`. PostgreSQL is published on `127.0.0.1:5433`; Qdrant is published on `127.0.0.1:6333` (HTTP) and `127.0.0.1:6334` (gRPC).
4. Stop the services with `docker compose down`. Named volumes keep local database and vector data across container restarts.

The API and web interface are not implemented yet. Keep credentials in `.env`; never commit API keys or other secrets.

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
