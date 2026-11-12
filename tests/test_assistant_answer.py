from types import SimpleNamespace

import pytest

from clearance.assistant import answer
from clearance.models import User


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


def make_user() -> User:
    return User(
        id=2,
        email="engineer@astervale.example",
        display_name="Demo Engineer",
        role="engineer",
        department="IT Operations",
        is_active=True,
    )


def test_response_schema_forbids_extra_fields() -> None:
    schema = answer.ANSWER_RESPONSE_FORMAT["json_schema"]["schema"]

    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {"answer", "citation_ids", "abstain"}


@pytest.mark.asyncio
async def test_answer_question_returns_only_valid_retrieved_citations(monkeypatch: pytest.MonkeyPatch) -> None:
    point = make_point()
    monkeypatch.setattr(answer, "search_documents", lambda question, user: _resolved([point]))
    monkeypatch.setattr(
        answer,
        "generate_text",
        lambda *args, **kwargs: _resolved(
            SimpleNamespace(
                content='{"answer":"Use the service portal.","citation_ids":["chunk-1"],"abstain":false}'
            )
        ),
    )

    response = await answer.answer_question("How do I report an incident?", make_user())

    assert response.answer == "Use the service portal."
    assert response.abstained is False
    assert [citation.chunk_id for citation in response.citations] == ["chunk-1"]
    assert response.citations[0].document_id == "IT-001"


@pytest.mark.asyncio
async def test_answer_question_abstains_when_search_has_no_allowed_results(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    async def no_results(question: str, user: User) -> list[SimpleNamespace]:
        return []

    async def model_must_not_be_called(*args: object, **kwargs: object) -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(answer, "search_documents", no_results)
    monkeypatch.setattr(answer, "generate_text", model_must_not_be_called)

    response = await answer.answer_question("What is the policy?", make_user())

    assert response.abstained is True
    assert response.citations == []
    assert called is False


@pytest.mark.asyncio
async def test_answer_question_abstains_for_unknown_citation_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(answer, "search_documents", lambda question, user: _resolved([make_point()]))
    monkeypatch.setattr(
        answer,
        "generate_text",
        lambda *args, **kwargs: _resolved(
            SimpleNamespace(
                content='{"answer":"A made-up answer.","citation_ids":["hidden-chunk"],"abstain":false}'
            )
        ),
    )

    response = await answer.answer_question("What is the policy?", make_user())

    assert response.abstained is True
    assert response.answer == answer.ABSTENTION_TEXT
    assert response.citations == []


async def _resolved(value: object) -> object:
    return value
