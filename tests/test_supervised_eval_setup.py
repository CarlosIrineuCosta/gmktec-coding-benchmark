from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from benchmark.supervised_eval.contracts import RunPhase, TerminalClass
from benchmark.supervised_eval.evidence import EvidenceStore
from benchmark.supervised_eval.harness import WorkspaceTools
from benchmark.supervised_eval.gallery_fixture import materialize
from benchmark.supervised_eval.inventory import capture, model_artifact
from benchmark.supervised_eval.lifecycle import DisposableServer, reserve_loopback_port
from benchmark.supervised_eval.pilot import selected_pilot_models
from benchmark.supervised_eval.private_fixture import validate_private_code_review_fixture
from benchmark.supervised_eval.report import render
from benchmark.supervised_eval.session import OpenAICompatibleSession
from benchmark.supervised_eval.supervision import LoopDetector
from benchmark.supervised_eval.harness import TOOL_DEFINITIONS


class SupervisedEvaluationSetupTests(unittest.TestCase):
    def test_evidence_is_append_only_and_i4_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = EvidenceStore(Path(tmp), "mock-run")
            store.write_once("manifest.json", {"run_id": "mock-run", "task_family": "gallery"})
            store.transition(RunPhase.SERVER_STARTING, "mock lifecycle")
            store.transition(RunPhase.READY, "mock health")
            store.transition(RunPhase.AUTONOMOUS, "mock candidate ready")
            with self.assertRaises(ValueError):
                store.intervention("I4_implementation_forbidden", "write solution", "forbidden")
            store.intervention("I1_diagnostic", "return test output", "mock failure")
            store.terminal(TerminalClass.ACCEPTED, "mock acceptance passed")
            store.summary("mock result")
            self.assertEqual(json.loads((store.run_dir / "acceptance.json").read_text())["terminal_class"], "accepted")
            self.assertIn("mock-run", render(store.run_dir))
            with self.assertRaises(FileExistsError):
                EvidenceStore(Path(tmp), "mock-run")

    def test_loop_detector_requires_a_supervisor_decision(self) -> None:
        detector = LoopDetector()
        self.assertEqual(detector.observe("run pytest", "same-diff"), 0)
        self.assertEqual(detector.observe("run pytest", "same-diff"), 1)
        decision = detector.decision(2, False, ["run pytest", "run pytest"])
        self.assertEqual(decision.recommendation, "inspect_for_intervention")
        self.assertEqual(detector.decision(3, True, ["write module.py"]).recommendation, "continue")

    def test_workspace_tools_cannot_escape_and_runs_in_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "work"
            workspace.mkdir()
            tools = WorkspaceTools(workspace)
            self.assertEqual(tools.call("write_file", {"path": "nested/a.txt", "content": "ok"})["written"], "nested/a.txt")
            self.assertEqual(tools.call("read_file", {"path": "nested/a.txt"})["content"], "ok")
            self.assertEqual(tools.call("search_files", {"query": "ok"})["matches"][0]["path"], "nested/a.txt")
            self.assertEqual(tools.call("patch_file", {"path": "nested/a.txt", "old": "ok", "new": "better"})["patched"], "nested/a.txt")
            with self.assertRaises(ValueError):
                tools.call("read_file", {"path": "../outside.txt"})
            result = tools.call("run_command", {"argv": [sys.executable, "-c", "print('bounded')"]})
            self.assertEqual(result["exit_code"], 0)
            self.assertIn("bounded", result["stdout"])

    def test_disposable_dummy_server_stops(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake_process = MagicMock()
            fake_process.pid = 42
            fake_process.poll.side_effect = [None, 0]
            with patch("benchmark.supervised_eval.lifecycle.subprocess.Popen", return_value=fake_process), patch(
                "benchmark.supervised_eval.lifecycle.wait_for_health", return_value=True
            ), patch("benchmark.supervised_eval.lifecycle.socket.socket") as socket_factory:
                socket_factory.return_value.__enter__.return_value.getsockname.return_value = ("127.0.0.1", 19000)
                self.assertEqual(reserve_loopback_port(), 19000)
                server = DisposableServer(["fake-server"], "http://127.0.0.1:19000/health", Path(tmp))
                self.assertEqual(server.start(), 42)
                server.stop()
            fake_process.terminate.assert_called_once()

    def test_inventory_is_read_only_and_private_fixture_is_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            model = Path(tmp) / "example.gguf"
            model.write_bytes(b"mock model")
            artifact = model_artifact(model, hash_file=True)
            self.assertEqual(artifact["bytes"], 10)
            manifest = capture([model], hash_files=False)
            self.assertEqual(manifest["models"][0]["filename"], "example.gguf")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "code-review"
            (root / "fixture").mkdir(parents=True)
            (root / "fixture/service.py").write_text("def f():\n    return 1\n", encoding="utf-8")
            (root / "gold.json").write_text('{"maximum_findings": 8, "defects": [{"id": "mock"}]}', encoding="utf-8")
            self.assertEqual(validate_private_code_review_fixture(root)["gold_defects"], 1)

    def test_fake_model_tool_trajectory_is_logged_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / "workspace"
            workspace.mkdir()
            store = EvidenceStore(root, "fake-model")
            store.write_once("manifest.json", {"run_id": "fake-model", "task_family": "gallery"})

            def fake_post(_: dict[str, object]) -> dict[str, object]:
                return {"choices": [{"message": {"role": "assistant", "tool_calls": [{"id": "call-1", "function": {"name": "write_file", "arguments": '{"path":"result.txt","content":"fake"}'}}]}}]}

            session = OpenAICompatibleSession("http://fake.invalid/v1", "fake", store, WorkspaceTools(workspace), fake_post)
            result = session.one_turn([{"role": "user", "content": "mock"}], TOOL_DEFINITIONS)
            self.assertEqual(result["tool_results"][0]["result"]["written"], "result.txt")
            self.assertEqual((workspace / "result.txt").read_text(), "fake")

    def test_pilot_configuration_refuses_unselected_models(self) -> None:
        config = Path(__file__).resolve().parents[1] / "tasks/local-model-evaluation/pilot.json"
        with self.assertRaises(ValueError):
            selected_pilot_models(config)

    def test_gallery_fixture_plan_has_fixed_public_domain_sources(self) -> None:
        source_path = Path(__file__).resolve().parents[1] / "tasks/local-model-evaluation/gallery/sources.json"
        sources = json.loads(source_path.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            plan = materialize(sources, Path(tmp) / "images", fetch=False)
        self.assertEqual(len(plan), 12)
        self.assertTrue(all(item["license"] == "public-domain" for item in plan))


if __name__ == "__main__":
    unittest.main()
