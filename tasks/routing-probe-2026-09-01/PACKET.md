# Synthetic routing probe — 2026-09-01

This is a new, public, disposable patch task. It is not a rerun or a rewrite
of any historical benchmark task.

`retry.py` contains `should_retry(status, attempts)`. Make it return `True`
only when the normalized status is `timeout` or `rate_limited` and fewer than
three attempts have already occurred. Return only a standard unified diff that
changes `retry.py`. Do not use tools, external information, or unstated facts.

The supplied `test_retry.py` is a standard-library `unittest` acceptance test. It is not
shown to the candidate as an editable target and must not be modified.
