import os

from benchmark.operational_v1.prompts import prompt
from benchmark.operational_v1.patch_eval import evaluate
from benchmark.operational_v1.run import OUTPUT_LIMITS, output_limit
from benchmark.operational_v1.score import score
from benchmark.operational_v1.telemetry import TelemetrySampler, revalidate_drm_totals, summarize
from benchmark.operational_v1.routing_probe import evaluate as evaluate_routing_probe
from benchmark.operational_v1.qualification_gate import parse_adapter_action, tool_result


def test_prompts_are_synthetic_and_tool_free():
    value = prompt("classification")
    assert "Do not use tools" in value
    assert "Gmail" not in value


def test_classification_score_accepts_complete_gold_contract():
    labels = [("task_action", False), ("decision", False), ("blocker", False), ("factual_reference", False), ("request", False), ("note", False), ("discard", False), ("ambiguous", True), ("factual_reference", False), ("ambiguous", True)]
    rows = ",".join('{"id":"cls-%02d","primary_label":"%s","secondary_label":null,"confidence":1,"needs_review":%s,"reason":"gold"}' % (index, label, str(review).lower()) for index, (label, review) in enumerate(labels, 1))
    result = score("classification", "{\"items\":[" + rows + "]}")
    assert result["schema_valid"] is True and result["correctness"] == 1.0


def test_report_requires_all_headings():
    answer = "\n".join(f"## {value}" for value in ("Completed", "Failed", "Unknown", "Safety concerns", "Routing", "Next action")) + "\nalpha 0.9 serving"
    assert score("report", answer)["schema_valid"] is True


def test_patch_score_accepts_standard_fenced_unified_diff():
    answer = "```diff\n--- a/queue.py\n+++ b/queue.py\n@@ -1 +1 @@\n-def route(priority): return priority\n+def route(priority): return priority.strip()\n```"
    assert score("patch", answer)["schema_valid"] is True


def test_patch_evaluator_applies_a_fenced_diff(tmp_path):
    answer = tmp_path / "answer.diff"; output = tmp_path / "result.json"
    answer.write_text("```diff\n--- a/queue.py\n+++ b/queue.py\n@@ -2,4 +2,4 @@\n \n \n def route(priority: str) -> str:\n-    return \"fast\" if priority == \"urgent\" else \"normal\"\n+    return \"fast\" if is_urgent(priority) else \"normal\"\n```\n", encoding="utf-8")
    assert evaluate(answer, output)["passed"] is True


def test_output_limits_are_task_appropriate_and_bounded():
    assert output_limit("classification") < output_limit("extraction")
    assert output_limit("report") <= 1500
    assert set(OUTPUT_LIMITS) == {"classification", "extraction", "docs_qa", "report", "patch"}


def test_telemetry_summary_reports_observed_memory_and_missing_gpu():
    summary = summarize(
        [
            {"system_memory_kib": {"MemAvailable": 100, "MemUsed": 900}, "llama_server": {"rss_kib": 20}, "amd_gpu": {"status": "unavailable"}},
            {"system_memory_kib": {"MemAvailable": 80, "MemUsed": 920}, "llama_server": {"rss_kib": 25}, "amd_gpu": {"status": "unavailable"}},
        ],
        [],
    )
    assert summary["system_memory_kib"] == {"minimum_available": 80, "peak_used": 920}
    assert summary["llama_server"] == {"peak_rss_kib": 25, "pid_observed": True}
    assert summary["amd_gpu"]["status"] == "unavailable"
    assert summary["amd_gpu"]["peak_llama_server_vram_bytes"] is None


def test_telemetry_sampler_writes_json_evidence(tmp_path):
    sampler = TelemetrySampler(os.getpid(), interval_seconds=0.01)
    sampler.start()
    summary = sampler.stop()
    output = tmp_path / "telemetry.json"
    sampler.write(output, summary)
    assert output.exists()
    assert summary["sample_count"] >= 2
    assert summary["llama_server"]["peak_rss_kib"] is not None


def test_telemetry_write_creates_nested_evidence_directory(tmp_path):
    sampler = TelemetrySampler(os.getpid(), interval_seconds=0.01)
    sampler.start()
    summary = sampler.stop()
    output = tmp_path / "nested" / "telemetry.json"
    sampler.write(output, summary)
    assert output.exists()


def test_telemetry_revalidation_deduplicates_drm_client_ids():
    payload = {
        "summary": {"amd_gpu": {"counter_paths": [{"card": "card0"}]}},
        "samples": [{
            "system_memory_kib": {"MemAvailable": 10, "MemUsed": 90},
            "llama_server": {"rss_kib": 12},
            "amd_gpu": {"status": "available", "process_memory": {"entries": [
                {"fd": "4", "driver": "amdgpu", "client_id": "9", "vram_bytes": 100, "gtt_bytes": 200},
                {"fd": "5", "driver": "amdgpu", "client_id": "9", "vram_bytes": 100, "gtt_bytes": 200},
            ]}},
        }],
    }
    corrected = revalidate_drm_totals(payload)
    memory = corrected["samples"][0]["amd_gpu"]["process_memory"]
    assert memory["vram_bytes"] == 100 and memory["gtt_bytes"] == 200
    assert corrected["summary"]["amd_gpu"]["peak_llama_server_gtt_bytes"] == 200


def test_routing_probe_applies_and_accepts_the_required_patch():
    answer = """--- a/retry.py
+++ b/retry.py
@@ -1,2 +1,2 @@
 def should_retry(status: str, attempts: int) -> bool:
-    return status in {\"timeout\", \"rate_limited\"} and attempts <= 3
+    return status.strip().lower() in {\"timeout\", \"rate_limited\"} and attempts < 3
"""
    assert evaluate_routing_probe(answer)["accepted"] is True


def test_routing_probe_accepts_a_standard_no_prefix_diff():
    answer = """--- retry.py
+++ retry.py
@@ -1,2 +1,3 @@
 def should_retry(status: str, attempts: int) -> bool:
-    return status in {\"timeout\", \"rate_limited\"} and attempts <= 3
+    normalized_status = status.strip().lower()
+    return normalized_status in {\"timeout\", \"rate_limited\"} and attempts < 3
"""
    assert evaluate_routing_probe(answer)["accepted"] is True


def test_qualification_gate_parses_native_and_structured_tool_actions():
    native = {"choices": [{"message": {"tool_calls": [{"function": {"name": "read_fixture", "arguments": '{"path":"canary.txt"}'}}]}}]}
    assert tool_result(native, "native_openai")["bounded_action_succeeded"] is True
    assert parse_adapter_action('<TOOLCALL>[{"name":"read_fixture","arguments":{"path":"canary.txt"}}]</TOOLCALL>') == {"name": "read_fixture", "arguments": {"path": "canary.txt"}}
    assert parse_adapter_action('<TOOLCALL>[read_fixture(path="canary.txt")]</TOOLCALL>') == {"name": "read_fixture", "arguments": {"path": "canary.txt"}}
    assert parse_adapter_action('<tool_call><function=read_fixture><parameter=path>canary.txt</parameter></function></tool_call>') == {"name": "read_fixture", "arguments": {"path": "canary.txt"}}
