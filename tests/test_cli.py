from local_agent_kit.cli import (
    _agent_config_template,
    _identity_template,
    _resolve_search_choice,
)


def test_resolve_search_choice_defaults_to_duckduckgo():
    assert _resolve_search_choice("") == "duckduckgo"
    assert _resolve_search_choice("1") == "duckduckgo"


def test_resolve_search_choice_offline_on_2():
    assert _resolve_search_choice("2") == "none"
    assert _resolve_search_choice(" 2 ") == "none"


def test_identity_template_includes_agent_name():
    text = _identity_template("my-agent")
    assert "Name: my-agent" in text
    assert "# IDENTITY" in text


def test_agent_config_template_reflects_search_choice():
    online = _agent_config_template("my-agent", "gemma4:e4b", "duckduckgo")
    assert "provider: duckduckgo" in online
    assert "web_search: true" in online

    offline = _agent_config_template("my-agent", "gemma4:e4b", "none")
    assert "provider: none" in offline
    assert "web_search: false" in offline
