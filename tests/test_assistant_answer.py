from types import SimpleNamespace

from clearance.assistant import answer


def make_point(point_id: str = "chunk-1") -> SimpleNamespace:
    return SimpleNamespace(
        id=point_id,
        payload={
            "document_id": "IT-001",
            "version": "1.0",
            "chunk_index": 0,
            "title": "Incident Response Guide",
            "department": "IT Operations",
            "effective_date": "2026-01-15",
            "text": "Report incidents through the service portal.",
        },
    )


def test_response_schema_forbids_extra_fields() -> None:
    schema = answer.ANSWER_RESPONSE_FORMAT["json_schema"]["schema"]

    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {
        "answer",
        "citation_ids",
        "tool_result_ids",
        "abstain",
    }


def test_answer_question_returns_only_valid_retrieved_citations() -> None:
    point = make_point()
    response = answer._validated_response(
        "How do I report an incident?",
        [point],
        [],
        '{"answer":"Use the service portal.","citation_ids":["chunk-1"],"tool_result_ids":[],"abstain":false}',
    )

    assert response.answer == "Use the service portal."
    assert response.abstained is False
    assert [citation.chunk_id for citation in response.citations] == ["chunk-1"]
    assert response.citations[0].document_id == "IT-001"


def test_answer_abstains_without_any_valid_evidence() -> None:
    response = answer._validated_response(
        "What is the policy?",
        [],
        [],
        '{"answer":"A guess.","citation_ids":[],"tool_result_ids":[],"abstain":false}',
    )
    assert response.abstained is True
    assert response.citations == []


def test_answer_abstains_for_unknown_citation_id() -> None:
    response = answer._validated_response(
        "What is the policy?",
        [make_point()],
        [],
        '{"answer":"A made-up answer.","citation_ids":["hidden-chunk"],"tool_result_ids":[],"abstain":false}',
    )

    assert response.abstained is True
    assert response.answer == answer.ABSTENTION_TEXT
    assert response.citations == []
