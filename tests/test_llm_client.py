from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clearance.llm import client as llm_client


async def stream_chunks(*chunks: object):
    for chunk in chunks:
        yield chunk


@pytest.mark.asyncio
async def test_generate_text_returns_usage_and_estimated_cost(monkeypatch: pytest.MonkeyPatch) -> None:
    response = stream_chunks(
        SimpleNamespace(
            choices=[SimpleNamespace(delta=SimpleNamespace(content="A grounded answer."), finish_reason=None)],
            usage=None,
            model="openai/gpt-oss-20b",
            id="request-123",
        ),
        SimpleNamespace(
            choices=[SimpleNamespace(delta=SimpleNamespace(content=None), finish_reason="stop")],
            usage=SimpleNamespace(prompt_tokens=100, completion_tokens=20, total_tokens=120),
            model="openai/gpt-oss-20b",
            id="request-123",
        ),
    )
    create = AsyncMock(return_value=response)
    close = AsyncMock()

    class FakeGroq:
        def __init__(self, **kwargs: object) -> None:
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(create=create)
            )

        async def close(self) -> None:
            await close()

    monkeypatch.setattr(llm_client, "AsyncGroq", FakeGroq)

    result = await llm_client.generate_text("system", "question", temperature=0.0)

    assert result.content == "A grounded answer."
    assert result.finish_reason == "stop"
    assert result.prompt_tokens == 100
    assert result.completion_tokens == 20
    assert result.total_tokens == 120
    assert result.estimated_cost_usd == pytest.approx(0.0000135)
    create.assert_awaited_once()
    assert create.await_args.kwargs["stream"] is True
    assert create.await_args.kwargs["extra_body"] == {"stream_options": {"include_usage": True}}
    close.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_text_rejects_empty_provider_answer(monkeypatch: pytest.MonkeyPatch) -> None:
    response = stream_chunks(
        SimpleNamespace(
            choices=[SimpleNamespace(delta=SimpleNamespace(content=None), finish_reason="stop")],
            usage=None,
            model="openai/gpt-oss-20b",
            id="request-123",
        )
    )

    class FakeGroq:
        def __init__(self, **kwargs: object) -> None:
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(create=AsyncMock(return_value=response))
            )

        async def close(self) -> None:
            return None

    monkeypatch.setattr(llm_client, "AsyncGroq", FakeGroq)

    with pytest.raises(llm_client.LLMProviderError, match="empty answer"):
        await llm_client.generate_text("system", "question")
