import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from qdrant_client.models import ScoredPoint

from clearance.models import User


def load_cases(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as file:
        cases = json.load(file)
    if not isinstance(cases, list) or not all(isinstance(case, dict) for case in cases):
        raise ValueError("The evaluation file must contain a list of question records.")
    return cases


def retrieved_versions(points: Iterable[ScoredPoint]) -> set[tuple[str, str]]:
    versions = set()
    for point in points:
        payload = point.payload or {}
        document_id = payload.get("document_id")
        version = payload.get("version")
        if document_id is not None and version is not None:
            versions.add((str(document_id), str(version)))
    return versions


def score_retrieval_case(
    case: dict[str, Any],
    points: list[ScoredPoint],
    allowed_granted_versions: set[tuple[str, str]],
) -> dict[str, Any]:
    found_versions = retrieved_versions(points)
    found_document_ids = {document_id for document_id, _ in found_versions}
    expected_document_ids = set(case["expected_document_ids"])
    denied_document_ids = set(case["denied_document_ids"])
    granted_document_ids = {
        document_id for document_id, _ in allowed_granted_versions
    }
    active_denials = denied_document_ids - granted_document_ids
    forbidden_versions = {
        (str(document_id), str(version))
        for document_id, version in case["forbidden_versions"]
    }
    leaked_document_ids = found_document_ids & active_denials
    leaked_versions = found_versions & forbidden_versions
    return {
        "case_id": case["id"],
        "user_email": case["user_email"],
        "question": case["question"],
        "expected_document_ids": sorted(expected_document_ids),
        "retrieved_document_ids": sorted(found_document_ids),
        "retrieved_versions": [list(version) for version in sorted(found_versions)],
        "hit_document_ids": sorted(found_document_ids & expected_document_ids),
        "active_denied_document_ids": sorted(active_denials),
        "leaked_document_ids": sorted(leaked_document_ids),
        "forbidden_versions": [list(version) for version in sorted(forbidden_versions)],
        "leaked_versions": [list(version) for version in sorted(leaked_versions)],
        "expected_abstention": bool(case["expected_abstention"]),
    }


def summarize_retrieval(results: list[dict[str, Any]]) -> dict[str, Any]:
    measured = [result for result in results if not result.get("skipped")]
    expected = [result for result in measured if result["expected_document_ids"]]
    total_expected = sum(len(result["expected_document_ids"]) for result in expected)
    total_retrieved = sum(len(result["retrieved_document_ids"]) for result in measured)
    total_hits = sum(len(result["hit_document_ids"]) for result in expected)
    leakage_cases = sum(
        bool(result["leaked_document_ids"] or result["leaked_versions"])
        for result in measured
    )
    return {
        "case_count": len(measured),
        "skipped_case_count": len(results) - len(measured),
        "document_precision_at_k": (
            round(total_hits / total_retrieved, 4) if total_retrieved else None
        ),
        "document_recall_at_k": (
            round(total_hits / total_expected, 4) if total_expected else None
        ),
        "expected_document_hit_rate": (
            round(
                sum(bool(result["hit_document_ids"]) for result in expected)
                / len(expected),
                4,
            )
            if expected
            else None
        ),
        "access_leakage_case_count": leakage_cases,
        "access_leakage_case_rate": round(leakage_cases / len(measured), 4)
        if measured
        else None,
    }


def summarize_answers(
    answer_results: list[dict[str, Any]],
) -> dict[str, Any]:
    if not answer_results:
        return {}
    expected = [result for result in answer_results if result["expected_document_ids"]]
    all_citations = sum(len(result["citation_document_ids"]) for result in answer_results)
    matching_citations = sum(
        len(set(result["citation_document_ids"]) & set(result["expected_document_ids"]))
        for result in answer_results
    )
    all_expected = sum(len(result["expected_document_ids"]) for result in expected)
    matching_expected = sum(
        len(set(result["citation_document_ids"]) & set(result["expected_document_ids"]))
        for result in expected
    )
    return {
        "answer_count": len(answer_results),
        "abstention_accuracy": round(
            sum(
                result["abstained"] == result["expected_abstention"]
                for result in answer_results
            )
            / len(answer_results),
            4,
        ),
        "citation_precision": (
            round(matching_citations / all_citations, 4) if all_citations else None
        ),
        "citation_recall": (
            round(matching_expected / all_expected, 4) if all_expected else None
        ),
    }
