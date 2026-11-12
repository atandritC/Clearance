class LLMRateLimitError(Exception):
    def __init__(self, retry_after: str | None = None) -> None:
        self.retry_after = retry_after
        super().__init__("The model provider is temporarily rate-limiting requests.")


class LLMProviderError(Exception):
    pass
