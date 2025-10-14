"""Integration tests for Phase 11 PR-3: Run history and artifact endpoints."""
from __future__ import annotations

import asyncio
import json
import zipfile
from io import BytesIO
from pathlib import Path

import httpx
import pytest

from backend import app as backend_app

pytestmark = pytest.mark.integration


@pytest.fixture()
def temp_runs_dir(tmp_path, monkeypatch):
    """Provide an isolated runs directory for tests."""
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("MDP_RUNS_DIR", str(runs_dir))
    monkeypatch.setattr(backend_app, "RUNS_BASE_DIR", runs_dir, raising=False)
    yield runs_dir
    backend_app.run_jobs.clear()
    backend_app.processing_jobs.clear()
    backend_app.prepass_jobs.clear()


@pytest.fixture()
def http_client(temp_runs_dir):
    """Return a synchronous helper that issues requests against the FastAPI app."""
    backend_app.RUNS_BASE_DIR.mkdir(parents=True, exist_ok=True)
    transport = httpx.ASGITransport(app=backend_app.app)

    async def _request(method: str, url: str, **kwargs):
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.request(method, url, **kwargs)

    def request(method: str, url: str, **kwargs):
        return asyncio.run(_request(method, url, **kwargs))

    class _Client:
        def get(self, url: str, **kwargs):
            return request("GET", url, **kwargs)

    client = _Client()

    try:
        yield client
    finally:
        asyncio.run(transport.aclose())


def test_list_runs_empty(http_client):
    response = http_client.get("/api/runs")
    assert response.status_code == 200
    assert response.json() == {"runs": []}


def _write_artifact(run_dir: Path, name: str, content: str) -> None:
    target = run_dir / name
    target.write_text(content, encoding="utf-8")


def _touch_binary_artifact(run_dir: Path, name: str, data: bytes) -> None:
    target = run_dir / name
    target.write_bytes(data)


def _setup_run(run_id: str, runs_dir: Path) -> Path:
    run_dir = runs_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def test_run_listing_populates_metadata(http_client, temp_runs_dir):
    run_id = "run-001"
    run_dir = _setup_run(run_id, temp_runs_dir)
    _write_artifact(run_dir, "output.md", "# Output\n\nCorrected text.")
    _write_artifact(run_dir, "report.json", json.dumps({"steps": ["mask"], "statistics": {}}))

    backend_app.update_run_metadata(
        run_id,
        status="completed",
        created_at="2025-10-14T00:00:00Z",
        completed_at="2025-10-14T00:05:00Z",
        steps=["mask", "grammar"],
        models={"detector": "qwen2.5-1.5b", "fixer": "qwen3-4b"},
        exit_code=0,
        input_name="chapter01.md",
        input_size=1280,
    )

    response = http_client.get("/api/runs")
    assert response.status_code == 200
    payload = response.json()
    assert payload["runs"]
    run = payload["runs"][0]
    assert run["run_id"] == run_id
    assert run["status"] == "completed"
    assert run["artifact_count"] >= 2
    assert run["total_size"] >= 10
    assert run["has_rejected"] is False


def test_artifact_listing_and_preview(http_client, temp_runs_dir):
    run_id = "run-002"
    run_dir = _setup_run(run_id, temp_runs_dir)
    preview_text = "Sample artifact text."
    _write_artifact(run_dir, "notes.txt", preview_text)
    _write_artifact(run_dir, "report.json", json.dumps({"hello": "world"}))
    _touch_binary_artifact(run_dir, "audio.bin", b"\x00\x01")

    response = http_client.get(f"/api/runs/{run_id}/artifacts")
    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == run_id
    artifacts = {item["name"]: item for item in payload["artifacts"]}
    assert "notes.txt" in artifacts
    assert artifacts["notes.txt"]["preview"] == preview_text
    assert artifacts["notes.txt"]["is_text"] is True
    assert artifacts["audio.bin"]["media_type"] == "application/octet-stream"
    assert artifacts["audio.bin"]["size_bytes"] == 2


def test_download_specific_artifact(http_client, temp_runs_dir):
    run_id = "run-003"
    run_dir = _setup_run(run_id, temp_runs_dir)
    body = "Markdown body"
    _write_artifact(run_dir, "output.md", body)

    response = http_client.get(f"/api/runs/{run_id}/artifacts/output.md")
    assert response.status_code == 200
    assert response.text == body
    assert response.headers["content-type"].startswith("text/markdown")


def test_archive_download_contains_all_files(http_client, temp_runs_dir):
    run_id = "run-004"
    run_dir = _setup_run(run_id, temp_runs_dir)
    _write_artifact(run_dir, "output.md", "Body")
    _write_artifact(run_dir, "plan.json", json.dumps({}))

    response = http_client.get(f"/api/runs/{run_id}/artifacts/archive")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"

    buffer = BytesIO(response.content)
    with zipfile.ZipFile(buffer) as zip_file:
        names = set(zip_file.namelist())
    assert names == {"output.md", "plan.json"}


def test_path_traversal_is_blocked(http_client, temp_runs_dir):
    run_id = "run-005"
    run_dir = _setup_run(run_id, temp_runs_dir)
    _write_artifact(run_dir, "output.md", "Body")

    response = http_client.get(f"/api/runs/{run_id}/artifacts/../secret.txt")
    assert response.status_code == 404
