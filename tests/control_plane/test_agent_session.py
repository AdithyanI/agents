from contextlib import redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("agent_session", ROOT / "scripts/agent_session.py")
SESSION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SESSION)

FAKE = r'''
import json, os, signal, subprocess, sys, time
from pathlib import Path
args = sys.argv[1:]
client = os.environ['AGENT_TEST_CLIENT']
auth = 'status' in args
capture = {'args': args, 'cwd': os.getcwd(), 'auth': auth,
           'keys': {key: value for key, value in os.environ.items()
                    if key in json.loads(os.environ['AGENT_TEST_KEYS'])}}
with open(os.environ['AGENT_TEST_CAPTURE'], 'a') as stream:
    stream.write(json.dumps(capture) + '\n')
if auth:
    if client == 'codex':
        print('Logged in using API key' if os.environ.get('AGENT_TEST_AUTH') == 'api' else 'Logged in using ChatGPT', file=sys.stderr)
    else:
        print(json.dumps({'loggedIn': True, 'authMethod': 'api_key' if os.environ.get('AGENT_TEST_AUTH') == 'api' else 'claude.ai',
                          'apiProvider': 'firstParty', 'subscriptionType': os.environ.get('AGENT_TEST_SUBSCRIPTION', 'team')}))
    sys.exit(0)
prompt = sys.stdin.read()
Path(os.environ['AGENT_TEST_PROMPT']).write_text(prompt)
mode = os.environ.get('AGENT_TEST_MODE', 'success')
if client == 'codex':
    print(json.dumps({'type': 'thread.started', 'thread_id': 'session-123'}), flush=True)
else:
    print(json.dumps({'type': 'system', 'subtype': 'init', 'session_id': 'session-123'}), flush=True)
if mode == 'timeout':
    child = subprocess.Popen([sys.executable, '-c',
        'import signal,time; from pathlib import Path; '
        'signal.signal(signal.SIGTERM, signal.SIG_IGN); '
        "p=Path(__import__('os').environ['AGENT_TEST_HEARTBEAT']); "
        "exec('while True:\\n p.write_text(str(time.time()))\\n time.sleep(.05)')"], start_new_session=True)
    Path(os.environ['AGENT_TEST_PID']).write_text(str(child.pid))
    while True:
        time.sleep(1)
if mode == 'missing':
    sys.exit(0)
if client == 'codex':
    print(json.dumps({'type': 'turn.failed' if mode == 'failed' else 'turn.completed'}), flush=True)
else:
    print(json.dumps({'type': 'result', 'subtype': 'error_during_execution' if mode == 'failed' else 'success',
                      'is_error': mode == 'failed', 'session_id': 'session-123'}), flush=True)
print('retained fake diagnostic', file=sys.stderr)
sys.exit(9 if mode == 'exit' else 0)
'''


class AgentSessionTests(unittest.TestCase):
    def setUp(self):
        (ROOT / "tmp").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "tmp")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.cwd = self.directory / "owning repo"
        self.cwd.mkdir()
        self.prompt = self.directory / "prompt.txt"
        self.prompt.write_text("Inspect the synthetic fixture only.\n")
        self.client = self.directory / "fake-client"
        self.client.write_text(f"#!{sys.executable}\n" + FAKE)
        self.client.chmod(0o700)
        self.transcript = self.directory / "attempt.jsonl"
        self.result = self.directory / "attempt.result.json"
        self.capture = self.directory / "capture.jsonl"
        self.env = {"CODEX_BIN": str(self.client), "AGENTS_CLAUDE_BIN": str(self.client),
                    "AGENT_TEST_CLIENT": "codex", "AGENT_TEST_CAPTURE": str(self.capture),
                    "AGENT_TEST_KEYS": json.dumps(list(SESSION.INFERENCE_OVERRIDES)),
                    "AGENT_TEST_PROMPT": str(self.directory / "received.txt"),
                    "AGENT_TEST_PID": str(self.directory / "child.pid"),
                    "AGENT_TEST_HEARTBEAT": str(self.directory / "heartbeat")}

    def args(self, client="codex", *more):
        return ["--client", client, "--cwd", str(self.cwd), "--prompt-file", str(self.prompt),
                "--transcript", str(self.transcript), "--result-file", str(self.result),
                "--timeout-minutes", "0.2", "--no-input", *more]

    def run_session(self, client="codex", *more, updates=None):
        env = {**self.env, "AGENT_TEST_CLIENT": client, **(updates or {})}
        output = io.StringIO()
        with patch.dict(os.environ, env), redirect_stdout(output):
            code = SESSION.main(self.args(client, *more))
        text = output.getvalue()
        return code, text if "--plain" in more else json.loads(text)

    def captures(self):
        return [json.loads(line) for line in self.capture.read_text().splitlines()]

    def test_codex_success_inherits_model_and_records_completion_without_business_report(self):
        code, receipt = self.run_session()
        self.assertEqual(code, 0)
        self.assertEqual(set(receipt), {"schema_version", "command", "status", "data", "error", "meta"})
        self.assertEqual(receipt["status"], "ok")
        self.assertEqual(receipt, json.loads(self.result.read_text()))
        data = receipt["data"]
        self.assertTrue(data["completed"])
        self.assertEqual(data["session_id"], "session-123")
        self.assertEqual(data["thread_id"], "session-123")
        auth, model = self.captures()
        self.assertEqual(model["cwd"], str(self.cwd))
        self.assertEqual((self.directory / "received.txt").read_text(), self.prompt.read_text())
        self.assertNotIn("--model", model["args"])
        self.assertIn('model_provider="openai"', model["args"])
        self.assertIn('forced_login_method="chatgpt"', model["args"])
        self.assertNotIn('forced_login_method="chatgpt"', auth["args"])
        self.assertIn('approval_policy="never"', model["args"])
        self.assertIn("read-only", model["args"])
        self.assertIn("retained fake diagnostic", Path(data["stderr_log"]).read_text())
        for path in (self.transcript, self.result, Path(data["stderr_log"])):
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_trusted_codex_passes_explicit_model_and_effort(self):
        code, _ = self.run_session("codex", "--trusted", "--model", "chosen-model", "--effort", "high")
        self.assertEqual(code, 0)
        command = self.captures()[-1]["args"]
        self.assertIn("danger-full-access", command)
        self.assertIn("chosen-model", command)
        self.assertIn('model_reasoning_effort="high"', command)

    def test_claude_subscription_and_conservative_permissions(self):
        code, receipt = self.run_session("claude")
        self.assertEqual(code, 0)
        self.assertEqual(receipt["data"]["session_id"], "session-123")
        self.assertIsNone(receipt["data"]["thread_id"])
        command = self.captures()[-1]["args"]
        self.assertIn("plan", command)
        self.assertIn("none", command)
        self.assertNotIn("--dangerously-skip-permissions", command)
        settings = json.loads(command[command.index("--settings") + 1])
        self.assertEqual(settings["forceLoginMethod"], "claudeai")
        self.assertEqual(settings["apiKeyHelper"], "")

    def test_claude_trusted_and_optional_model_effort(self):
        code, _ = self.run_session("claude", "--trusted", "--model", "chosen", "--effort", "high")
        self.assertEqual(code, 0)
        command = self.captures()[-1]["args"]
        self.assertIn("--dangerously-skip-permissions", command)
        self.assertIn("chosen", command)
        self.assertIn("--effort", command)

    def test_api_key_login_is_rejected_before_model_launch(self):
        code, receipt = self.run_session(updates={"AGENT_TEST_AUTH": "api"})
        self.assertEqual(code, 3)
        self.assertEqual(receipt["error"]["code"], "E_SUBSCRIPTION_REQUIRED")
        self.assertEqual(len(self.captures()), 1)
        self.assertFalse(receipt["data"]["completed"])

    def test_claude_api_account_is_rejected_before_model_launch(self):
        code, _ = self.run_session("claude", updates={"AGENT_TEST_AUTH": "api"})
        self.assertEqual(code, 3)
        self.assertEqual(len(self.captures()), 1)

    def test_claude_without_known_subscription_is_rejected(self):
        code, _ = self.run_session("claude", updates={"AGENT_TEST_SUBSCRIPTION": "free"})
        self.assertEqual(code, 3)
        self.assertEqual(len(self.captures()), 1)

    def test_inference_environment_is_stripped_without_mutating_parent(self):
        injected = {key: "synthetic-inference-override" for key in SESSION.INFERENCE_OVERRIDES}
        with patch.dict(os.environ, injected):
            code, _ = self.run_session()
            self.assertEqual(code, 0)
            for key in injected:
                self.assertEqual(os.environ[key], "synthetic-inference-override")
        self.assertTrue(all(not call["keys"] for call in self.captures()))

    def test_existing_evidence_is_never_replaced(self):
        self.result.write_text("Existing result")
        code, receipt = self.run_session()
        self.assertEqual(code, 2)
        self.assertEqual(receipt["error"]["code"], "E_OUTPUT")
        self.assertEqual(self.result.read_text(), "Existing result")
        self.assertFalse(self.transcript.exists())
        self.assertFalse(self.capture.exists())

    def test_failure_and_missing_completion_keep_session_evidence(self):
        for client in ("codex", "claude"):
            for mode in ("failed", "missing", "exit"):
                with self.subTest(client=client, mode=mode):
                    self.transcript = self.directory / f"{client}-{mode}.jsonl"
                    self.result = self.directory / f"{client}-{mode}.result.json"
                    code, receipt = self.run_session(client, updates={"AGENT_TEST_MODE": mode})
                    self.assertEqual(code, 4)
                    self.assertEqual(receipt["error"]["code"], "E_INCOMPLETE")
                    self.assertEqual(receipt["data"]["session_id"], "session-123")
                    self.assertFalse(receipt["data"]["completed"])
                    self.assertTrue(self.transcript.read_text())

    def test_timeout_stops_detached_child_and_retains_identity(self):
        code, receipt = self.run_session("codex", "--timeout-minutes", "0.03", updates={"AGENT_TEST_MODE": "timeout"})
        self.assertEqual(code, 5)
        self.assertTrue(receipt["data"]["timed_out"])
        self.assertEqual(receipt["data"]["thread_id"], "session-123")
        pid = int((self.directory / "child.pid").read_text())
        state = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True).stdout.strip()
        self.assertTrue(not state or state.startswith("Z"), state)
        heartbeat = self.directory / "heartbeat"
        self.assertTrue(heartbeat.is_file())
        finished = heartbeat.read_text()
        time.sleep(0.15)
        self.assertEqual(heartbeat.read_text(), finished)

    def test_validation_json_and_plain_output(self):
        output = io.StringIO()
        with redirect_stdout(output):
            code = SESSION.main([])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(output.getvalue())["error"]["code"], "E_USAGE")
        code, plain = self.run_session("codex", "--plain")
        self.assertEqual(code, 0)
        self.assertEqual(plain.strip(), "codex: ok")

    def test_sigterm_stops_session_and_preserves_interruption_receipt(self):
        environ = {**os.environ, **self.env, "AGENT_TEST_MODE": "timeout"}
        proc = subprocess.Popen([sys.executable, str(ROOT / "scripts/run-agent-session.py"), *self.args()],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=environ)
        pid_path = self.directory / "child.pid"
        try:
            deadline = time.monotonic() + 5
            while not pid_path.exists() and time.monotonic() < deadline:
                time.sleep(0.05)
            self.assertTrue(pid_path.exists())
            proc.terminate()
            output, _ = proc.communicate(timeout=6)
            self.assertEqual(proc.returncode, 5)
            receipt = json.loads(output)
            self.assertEqual(receipt["error"]["code"], "E_INTERRUPTED")
            self.assertEqual(receipt["data"]["thread_id"], "session-123")
            self.assertEqual(receipt, json.loads(self.result.read_text()))
            pid = int(pid_path.read_text())
            state = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True).stdout.strip()
            self.assertTrue(not state or state.startswith("Z"), state)
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.communicate(timeout=3)
            if pid_path.exists():
                try:
                    os.kill(int(pid_path.read_text()), signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def test_unavailable_selected_client_does_not_fall_back(self):
        code, receipt = self.run_session(updates={"CODEX_BIN": str(self.directory / "missing")})
        self.assertEqual(code, 4)
        self.assertEqual(receipt["error"]["code"], "E_CLIENT")
        self.assertFalse(self.capture.exists())


if __name__ == "__main__":
    unittest.main()
