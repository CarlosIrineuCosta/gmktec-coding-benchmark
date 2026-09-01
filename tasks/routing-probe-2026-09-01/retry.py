def should_retry(status: str, attempts: int) -> bool:
    return status in {"timeout", "rate_limited"} and attempts <= 3
