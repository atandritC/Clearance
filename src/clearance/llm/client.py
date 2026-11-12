import logging
import time
from dataclasses import dataclass

from groq import APIConnectionError, APIStatusError, AsyncGroq, RateLimitError

from clearance.config import settings
from clearance.llm.errors import LLMProviderError, LLMRateLimitError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class LLMCallResult:
    content: str
    model: str
    request_id: str
    finish_reason: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_seconds: float
    estimated_cost_usd: float
    tool_calls: list[dict[str, object]]


async def generate_text(
    system_prompt: str,
    user_prompt: str,
    temperature: float | None = None,
    response_format: dict[str, object] | None = None,
) -> LLMCallResult:
    return await generate_completion(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        response_format=response_format,
    )


async def generate_completion(
    messages: list[dict[str, object]],
    temperature: float | None = None,
    response_format: dict[str, object] | None = None,
    tools: list[dict[str, object]] | None = None,
) -> LLMCallResult:
    client = AsyncGroq(
        api_key=settings.groq_api_key.get_secret_value(),
        timeout=30.0,
        max_retries=2,
    )
    started_at = time.perf_counter()

    try:
        request_options: dict[str, object] = {
            "model": settings.groq_model,
            "messages": messages,
            "temperature": (
                settings.groq_temperature if temperature is None else temperature
            ),
            "max_completion_tokens": settings.groq_max_completion_tokens,
        }
        if response_format is not None:
            request_options["response_format"] = response_format
        if tools is not None:
            request_options["tools"] = tools
            request_options["tool_choice"] = "auto"

        request_options["stream"] = True
        request_options["extra_body"] = {"stream_options": {"include_usage": True}}
        stream = await client.chat.completions.create(**request_options)
        content_parts: list[str] = []
        tool_call_parts: dict[int, dict[str, object]] = {}
        response_id = ""
        response_model = settings.groq_model
        finish_reason = "unknown"
        usage = None

        async for chunk in stream:
            response_id = getattr(chunk, "id", None) or response_id
            response_model = getattr(chunk, "model", None) or response_model
            if getattr(chunk, "usage", None) is not None:
                usage = chunk.usage
            if not chunk.choices:
                continue

            choice = chunk.choices[0]
            delta = choice.delta
            if delta.content:
                content_parts.append(delta.content)
            if choice.finish_reason:
                finish_reason = choice.finish_reason
            for tool_delta in getattr(delta, "tool_calls", None) or []:
                index = tool_delta.index
                accumulated = tool_call_parts.setdefault(
                    index,
                    {"id": "", "type": "function", "function": {"name": "", "arguments": ""}},
                )
                if tool_delta.id:
                    accumulated["id"] = tool_delta.id
                function = accumulated["function"]
                if tool_delta.function:
                    if tool_delta.function.name:
                        function["name"] = str(function["name"]) + tool_delta.function.name
                    if tool_delta.function.arguments:
                        function["arguments"] = str(function["arguments"]) + tool_delta.function.arguments
    except RateLimitError as error:
        retry_after = error.response.headers.get("retry-after")
        logger.warning("Groq rate limit reached; retry_after=%s", retry_after)
        raise LLMRateLimitError(retry_after) from error
    except (APIConnectionError, APIStatusError) as error:
        logger.error(
            "Groq request failed; status=%s request_id=%s",
            getattr(error, "status_code", None),
            getattr(error, "request_id", None),
        )
        raise LLMProviderError("The model provider could not complete the request.") from error
    finally:
        await client.close()

    content = "".join(content_parts)
    tool_calls = [tool_call_parts[index] for index in sorted(tool_call_parts)]
    if not content and not tool_calls:
        raise LLMProviderError("The model provider returned an empty answer.")

    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0
    total_tokens = usage.total_tokens if usage else prompt_tokens + completion_tokens
    latency_seconds = time.perf_counter() - started_at
    estimated_cost_usd = (
        prompt_tokens * settings.groq_input_cost_per_million_tokens_usd
        + completion_tokens * settings.groq_output_cost_per_million_tokens_usd
    ) / 1_000_000

    result = LLMCallResult(
        content=content,
        model=response_model,
        request_id=response_id,
        finish_reason=finish_reason,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        latency_seconds=latency_seconds,
        estimated_cost_usd=estimated_cost_usd,
        tool_calls=tool_calls,
    )

    logger.info(
        "groq_call request_id=%s model=%s finish_reason=%s prompt_tokens=%d completion_tokens=%d total_tokens=%d latency_seconds=%.3f estimated_cost_usd=%.8f",
        result.request_id,
        result.model,
        result.finish_reason,
        result.prompt_tokens,
        result.completion_tokens,
        result.total_tokens,
        result.latency_seconds,
        result.estimated_cost_usd,
    )
    return result
