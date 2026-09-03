from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import pytest

_SYNTHETIC_COMMIT = "0123456789abcdef0123456789abcdef01234567"


class _GithubRunHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/repos/fraware/ai-adoption-us/actions/runs/12345":
            self.send_response(404)
            self.end_headers()
            return
        payload: dict[str, Any] = {
            "id": 12345,
            "name": "Release candidate CI",
            "path": ".github/workflows/ci.yml",
            "event": "push",
            "head_branch": "main",
            "head_sha": _SYNTHETIC_COMMIT,
            "status": "completed",
            "conclusion": "success",
            "run_attempt": 1,
            "repository": {"full_name": "fraware/ai-adoption-us"},
        }
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


@pytest.fixture(autouse=True)
def _release_engine_github_api(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch):
    """Give subprocess promotion tests a deterministic GitHub API boundary.

    Only ``test_release_engine.py`` receives these variables. Production code has
    no test-mode switch; the subprocess executes the same live-verification path
    used by a real promotion.
    """

    if request.node.path.name != "test_release_engine.py":
        yield
        return

    server = ThreadingHTTPServer(("127.0.0.1", 0), _GithubRunHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        monkeypatch.setenv("GITHUB_TOKEN", "synthetic-token")
        monkeypatch.setenv("GITHUB_REPOSITORY", "fraware/ai-adoption-us")
        monkeypatch.setenv("GITHUB_API_URL", f"http://{host}:{port}")
        yield
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
