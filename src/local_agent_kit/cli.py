"""lak — Local Agent Kit CLI.

Commands:
    lak init          Interactive setup wizard
    lak doctor        Preflight health check
    lak bot <dir>     Run the agent
    lak hardware      Show hardware detection
"""
from __future__ import annotations

import argparse
import asyncio
import os
import shutil
import subprocess
import sys
from pathlib import Path


def cmd_init(args):
    """Interactive setup wizard."""
    from local_agent_kit.hardware import detect_hardware, format_hardware_report, recommend_model

    print()
    print("=" * 50)
    print("  Local Agent Kit — Setup")
    print("=" * 50)
    print()

    # 1. Hardware
    print("Detecting hardware...")
    hw = detect_hardware()
    rec = recommend_model(hw)
    print(format_hardware_report(hw, rec))
    print()

    # 2. Agent name
    agent_name = input("Agent name [my-agent]: ").strip() or "my-agent"
    agent_dir = Path(args.dir if args.dir else f"./{agent_name}")

    # 3. Ollama
    ollama_ok = shutil.which("ollama") is not None
    print(f"\n  {'✓' if ollama_ok else '✗'} Ollama {'found' if ollama_ok else 'not found — install from https://ollama.com'}")
    if not ollama_ok:
        return 1

    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
        if rec.model in result.stdout:
            print(f"  ✓ {rec.model} already pulled")
        else:
            pull = input(f"  Pull {rec.model} ({rec.size_gb} GB)? [Y/n]: ").strip().lower()
            if pull != "n":
                subprocess.run(["ollama", "pull", rec.model], timeout=600)
    except Exception:
        pass

    # 4. Channel
    print("\n  Communication channel:")
    print("    1. CLI (terminal — zero setup, great for testing)")
    print("    2. Telegram (requires bot token)")
    channel_choice = input("  Choose [1]: ").strip() or "1"
    channel = "cli" if channel_choice == "1" else "telegram"

    tg_token = ""
    tg_chat_id = ""
    if channel == "telegram":
        tg_token = input("  Telegram Bot Token: ").strip()
        tg_chat_id = input("  Telegram Chat ID: ").strip()

    # 5. Search
    print("\n  Web search provider:")
    print("    1. DuckDuckGo (no API key needed)")
    print("    2. Gemini Search Grounding (requires API key, better quality)")
    print("    3. None (local only)")
    search_choice = input("  Choose [1]: ").strip() or "1"
    search_map = {"1": "duckduckgo", "2": "gemini", "3": "none"}
    search = search_map.get(search_choice, "duckduckgo")

    gemini_key = ""
    if search == "gemini":
        gemini_key = input("  Gemini API Key: ").strip()

    # 6. Scaffold
    print(f"\n  Creating {agent_dir}/")
    agent_dir.mkdir(parents=True, exist_ok=True)
    identity_dir = agent_dir / "identity"
    identity_dir.mkdir(exist_ok=True)

    # IDENTITY.md template
    identity_path = identity_dir / "IDENTITY.md"
    if not identity_path.exists():
        identity_path.write_text(f"""# IDENTITY

Name: {agent_name}
Role: Your AI assistant
Reports to: You

Core function: Answer questions, search the web, help with tasks.

## Your Tools

You have tools that run automatically:

- **Web search** — when you're asked about current events, news, or anything external, your system searches the web and gives you results as [SYSTEM DATA]. Use this data confidently.

When you see [SYSTEM DATA] in the conversation, USE IT. That data was fetched specifically for this question.

## What You Cannot Do

- You cannot fabricate data. If no [SYSTEM DATA] is present and you don't know, say so.
- When corrected, acknowledge and stay on topic.
""")
        print(f"    ✓ identity/IDENTITY.md")

    # agent.yaml
    config_path = agent_dir / "agent.yaml"
    if not config_path.exists():
        config_path.write_text(f"""name: {agent_name}
model: {rec.model}
channel: {channel}

search:
  provider: {search}

conversation_memory:
  enabled: true
  max_history: 20

tools:
  web_search: {'true' if search != 'none' else 'false'}
""")
        print(f"    ✓ agent.yaml")

    # .env
    env_path = agent_dir / ".env"
    if not env_path.exists():
        lines = []
        if gemini_key:
            lines.append(f"GEMINI_API_KEY={gemini_key}")
        if tg_token:
            lines.append(f"PAT_TG_BOT_TOKEN={tg_token}")
        if tg_chat_id:
            lines.append(f"PAT_TG_CHAT_ID={tg_chat_id}")
        env_path.write_text("\n".join(lines) + "\n" if lines else "# Add API keys here\n")
        print(f"    ✓ .env")

    print(f"""
  Done! Next steps:
    1. Edit {identity_dir}/IDENTITY.md — make the agent yours
    2. lak doctor --agent {agent_dir}
    3. lak bot {agent_dir}
""")
    return 0


def cmd_doctor(args):
    """Preflight health check."""
    from local_agent_kit.hardware import detect_hardware, recommend_model

    print("\n  Local Agent Kit — Doctor")
    print("  " + "=" * 40)

    issues = 0
    hw = detect_hardware()
    rec = recommend_model(hw)

    print(f"  {'✓' if hw.ram_gb >= 8 else '✗'} RAM: {hw.ram_gb} GB")
    print(f"  {'✓' if hw.chip != 'unknown' else '✗'} Chip: {hw.chip}")

    ollama_ok = shutil.which("ollama") is not None
    print(f"  {'✓' if ollama_ok else '✗'} Ollama installed")
    if not ollama_ok:
        issues += 1

    if ollama_ok:
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
            if rec.model in result.stdout:
                print(f"  ✓ {rec.model} available")
            else:
                print(f"  ✗ {rec.model} not pulled")
                issues += 1
        except Exception:
            print(f"  ✗ Ollama not responding")
            issues += 1

    if args.agent:
        agent_dir = Path(args.agent)
        identity = agent_dir / "identity" / "IDENTITY.md"
        config = agent_dir / "agent.yaml"
        print(f"  {'✓' if identity.exists() else '✗'} IDENTITY.md")
        print(f"  {'✓' if config.exists() else '✗'} agent.yaml")
        if not identity.exists() or not config.exists():
            issues += 1

    print(f"\n  {'All checks passed.' if issues == 0 else f'{issues} issue(s) found.'}")
    return issues


def cmd_bot(args):
    """Run the agent."""
    from local_agent_kit.agent import Agent

    agent_dir = Path(args.agent)
    if not agent_dir.exists():
        print(f"Agent directory not found: {agent_dir}")
        print("Run `lak init` first.")
        return 1

    agent = Agent.from_directory(agent_dir)
    print(f"Starting {agent.config.name} ({agent.config.model})...")

    try:
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        print("\nShutting down.")
    return 0


def cmd_hardware(args):
    """Show hardware detection."""
    from local_agent_kit.hardware import detect_hardware, format_hardware_report, recommend_model

    hw = detect_hardware()
    rec = recommend_model(hw)
    print(f"\n{format_hardware_report(hw, rec)}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="lak",
        description="Local Agent Kit — build local-first AI agents on consumer hardware",
    )
    sub = parser.add_subparsers(dest="command")

    p_init = sub.add_parser("init", help="Interactive setup wizard")
    p_init.add_argument("--dir", help="Agent directory to create")

    p_doc = sub.add_parser("doctor", help="Preflight health check")
    p_doc.add_argument("--agent", help="Agent directory to check")

    p_bot = sub.add_parser("bot", help="Run the agent")
    p_bot.add_argument("agent", help="Agent directory")

    sub.add_parser("hardware", help="Show hardware detection")

    args = parser.parse_args()

    commands = {
        "init": cmd_init,
        "doctor": cmd_doctor,
        "bot": cmd_bot,
        "hardware": cmd_hardware,
    }

    if args.command in commands:
        sys.exit(commands[args.command](args))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
