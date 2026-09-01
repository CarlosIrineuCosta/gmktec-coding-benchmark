from retry import should_retry


def test_normalized_retryable_status_before_limit():
    assert should_retry(" TIMEOUT ", 2) is True
    assert should_retry("rate_limited", 2) is True


def test_attempt_limit_is_exclusive():
    assert should_retry("timeout", 3) is False


def test_non_retryable_status_is_false():
    assert should_retry("invalid_request", 0) is False
