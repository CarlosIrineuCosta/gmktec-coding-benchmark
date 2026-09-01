import unittest

from retry import should_retry


class RetryTests(unittest.TestCase):
    def test_normalized_retryable_status_before_limit(self):
        self.assertTrue(should_retry(" TIMEOUT ", 2))
        self.assertTrue(should_retry("rate_limited", 2))

    def test_attempt_limit_is_exclusive(self):
        self.assertFalse(should_retry("timeout", 3))

    def test_non_retryable_status_is_false(self):
        self.assertFalse(should_retry("invalid_request", 0))
