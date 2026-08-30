"""Guard against starting a pilot before the Owner chooses exactly two models."""
from __future__ import annotations

import json
from pathlib import Path


def selected_pilot_models(config_path: Path) -> tuple[str, str]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    models = config.get("pilot_models")
    if not isinstance(models, list) or len(models) != 2 or not all(isinstance(model, str) and model.strip() for model in models):
        raise ValueError("pilot is intentionally blocked until the Owner names exactly two models")
    return models[0], models[1]
