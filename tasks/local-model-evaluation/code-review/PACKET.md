# Held-out code-review task contract

Review the supplied disposable fixture. Return no more than eight findings.
Each finding must include the file/location, severity, defect, consequence,
recommended correction, and confidence.

Score only externally observable review quality: true-defect recall, precision,
false positives, severity/location quality, and explanatory usefulness. Do not
reward speculative warning volume. The candidate is a reviewer, not an
implementer.

The fixture's defect inventory and gold annotation remain under `data/private/`
and are never supplied to the candidate or committed to this public repository.
