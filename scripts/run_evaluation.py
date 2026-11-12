import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select

from clearance.assistant.answer import answer_question
from clearance.database import SessionFactory, engine
from clearance.evaluation.runner import (
    load_cases,
    score_retrieval_case,
    summarize_answers,
    summarize_retrieval,
)
from clearance.models import User
from clearance.retrieval.grants import get_granted_document_versions
from clearance.retrieval.search import search_documents

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = PROJECT_ROOT / "evaluation" / "golden_questions.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Measure document retrieval and access boundaries on synthetic questions."
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--answers", action="store_true")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


async def run_evaluation(args: argparse.Namespace) -> dict[str, Any]:
    cases = load_cases(args.dataset)
    if not cases:
        raise ValueError("The evaluation file must contain at least one question.")
    if args.limit < 1:
        raise ValueError("The retrieval limit must be at least 1.")
    emails = {case["user_email"].strip().lower() for case in cases}
    retrieval_results = []
    answer_results = []

    async with SessionFactory() as session:
        users_result = await session.scalars(
            select(User).where(User.email.in_(emails), User.is_active.is_(True))
        )
        users = {user.email.lower(): user for user in users_result.all()}
        missing_users = emails - users.keys()
        if missing_users:
            raise ValueError(
                "Evaluation users are missing or inactive: "
                + ", ".join(sorted(missing_users))
            )

        for case in cases:
            user = users[case["user_email"].strip().lower()]
            granted_versions = await get_granted_document_versions(session, user.id)
            required_grants = set(case.get("requires_granted_document_ids", []))
            granted_document_ids = {
                document_id for document_id, _ in granted_versions
            }
            missing_grants = required_grants - granted_document_ids
            unexpected_grants = (
                set(case.get("requires_no_granted_document_ids", []))
                & granted_document_ids
            )
            if missing_grants or unexpected_grants:
                skip_reason = (
                    "Required document grant is not present."
                    if missing_grants
                    else "The user has a grant that changes this access case."
                )
                retrieval_results.append(
                    {
                        "case_id": case["id"],
                        "user_email": case["user_email"],
                        "skipped": True,
                        "skip_reason": skip_reason,
                    }
                )
                continue

            points = await search_documents(
                case["question"], user, session, limit=args.limit
            )
            retrieval_results.append(
                score_retrieval_case(case, points, granted_versions)
            )

            if args.answers:
                response = await answer_question(
                    case["question"], user, session, confirm_actions=False
                )
                answer_results.append(
                    {
                        "case_id": case["id"],
                        "expected_document_ids": case["expected_document_ids"],
                        "expected_abstention": case["expected_abstention"],
                        "abstained": response.abstained,
                        "citation_document_ids": sorted(
                            {citation.document_id for citation in response.citations}
                        ),
                        "tool_names": sorted(
                            {tool_result.tool_name for tool_result in response.tool_results}
                        ),
                    }
                )

    retrieval_metrics = summarize_retrieval(retrieval_results)
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "dataset": str(args.dataset.resolve()),
        "retrieval_limit": args.limit,
        "answer_generation_enabled": args.answers,
        "access_boundary_passed": retrieval_metrics["access_leakage_case_count"] == 0,
        "retrieval_metrics": retrieval_metrics,
        "answer_metrics": summarize_answers(answer_results),
        "cases": retrieval_results,
        "answers": answer_results,
    }


async def main() -> None:
    args = parse_args()
    try:
        report = await run_evaluation(args)
        rendered = json.dumps(report, indent=2)
        if args.output is None:
            print(rendered)
        else:
            output = args.output
            if not output.is_absolute():
                output = PROJECT_ROOT / output
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(rendered + "\n", encoding="utf-8")
            print(f"Evaluation report saved to {output}")
            print(json.dumps(report["retrieval_metrics"], indent=2))
            if args.answers:
                print(json.dumps(report["answer_metrics"], indent=2))
        if not report["access_boundary_passed"]:
            raise SystemExit("Evaluation found unauthorized document results.")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
