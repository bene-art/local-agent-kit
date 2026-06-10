"""Smoke tests for the promptfoo eval harness (scaffold + provider)."""
from __future__ import annotations

from pathlib import Path

from local_agent_kit.eval import scaffold_eval
from local_agent_kit.eval import provider


def _make_agent_dir(tmp_path: Path) -> Path:
    agent_dir = tmp_path / "my-agent"
    agent_dir.mkdir()
    (agent_dir / "agent.yaml").write_text(
        "name: Scout\n"
        "model: gemma3:4b\n"
        "channel: cli\n"
    )
    return agent_dir


def test_scaffold_writes_provider_and_config(tmp_path: Path):
    agent_dir = _make_agent_dir(tmp_path)
    config_path = scaffold_eval(agent_dir)

    assert config_path == agent_dir / "eval" / "promptfooconfig.yaml"
    assert config_path.exists()
    assert (agent_dir / "eval" / "provider.py").exists()


def test_scaffold_config_embeds_agent_name_and_model(tmp_path: Path):
    agent_dir = _make_agent_dir(tmp_path)
    config_path = scaffold_eval(agent_dir)
    text = config_path.read_text()

    assert "Scout" in text
    assert "ollama:chat:gemma3:4b" in text
    assert "file://provider.py" in text
    # nunjucks var must survive the templating
    assert "{{question}}" in text


def test_scaffold_no_overwrite_preserves_edits(tmp_path: Path):
    agent_dir = _make_agent_dir(tmp_path)
    config_path = scaffold_eval(agent_dir)
    config_path.write_text("# my custom edits\n")

    scaffold_eval(agent_dir, overwrite=False)
    assert config_path.read_text() == "# my custom edits\n"


def test_provider_call_api_returns_output(tmp_path: Path, monkeypatch):
    class FakeAgent:
        _session = None

        async def handle(self, text: str) -> str:
            return f"echo: {text}"

    monkeypatch.setattr(provider, "_build_agent", lambda options: FakeAgent())

    result = provider.call_api("hello", {"config": {}}, {})
    assert result == {"output": "echo: hello"}


def test_provider_call_api_reports_errors(monkeypatch):
    def boom(options):
        raise RuntimeError("ollama down")

    monkeypatch.setattr(provider, "_build_agent", boom)

    result = provider.call_api("hi", {}, {})
    assert "error" in result
    assert "ollama down" in result["error"]


def test_provider_resolves_agent_dir_from_env(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("LAK_AGENT_DIR", str(tmp_path))
    resolved = provider._resolve_agent_dir({})
    assert resolved == tmp_path.resolve()
