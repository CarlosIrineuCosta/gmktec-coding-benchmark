def trigger_unboundlocal() -> None:
    # This mirrors the class of regression that invalidated the first Qwen run.
    action = action()  # noqa: F821  # deliberately evaluated at runtime
