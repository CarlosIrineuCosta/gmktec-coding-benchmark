from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "runs"
RESULTS = ROOT / "results"
TASKS = ROOT / "tasks"
TIMEOUT_SECONDS = 30 * 60
MAIN_CONTEXT = 65_536
CONTEXT_LADDER = [32_768, 65_536, 98_304, 131_072]

SYSTEMS = [
    {"id": "gmktec-qwen3-coder-30b", "harness": "ollama", "model": "qwen3-coder:30b"},
    {"id": "gmktec-qwen3-coder-next", "harness": "ollama", "model": "qwen3-coder-next"},
    {"id": "gmktec-gpt-oss-120b", "harness": "ollama", "model": "gpt-oss:120b"},
    {"id": "gmktec-gemma4-26b", "harness": "ollama", "model": "gemma4:26b-a4b-it-qat"},
    {"id": "gmktec-glm-4.6v-flash-9b", "harness": "ollama", "model": "MedAIBase/GLM-4.6V-Flash:9b"},
    {"id": "zai-glm-5.3-claude", "harness": "claude", "model": "glm-5.3[1m]"},
    {"id": "kimi-k3", "harness": "kimi", "model": "kimi-code/k3"},
    {"id": "codex-terra-high", "harness": "codex", "model": "gpt-5.6-terra"},
    {"id": "codex-sol-high", "harness": "codex", "model": "gpt-5.6-sol"},
]

TASK_IDS = ["historical", "research", "daily_ops"]
