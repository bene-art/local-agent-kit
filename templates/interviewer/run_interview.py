"""Runner for the interviewer template.

Loads schema.yaml into a StateFlow, drives the conversation through the
configured agent (so the model can warm up the question text), and writes
captured answers to a markdown file at completion.

Run from the kit root:

    python -m templates.interviewer.run_interview \
        --agent-dir templates/interviewer \
        --schema  templates/interviewer/schema.yaml \
        --output  ./interview-{timestamp}.md
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import sys
from pathlib import Path

import yaml

from local_agent_kit.agent import Agent
from local_agent_kit.patterns import StateFlow


PHRASING_PROMPT = (
    "Phrase the following interview question warmly, in one sentence. "
    "Do not editorialize on prior answers. Do not add a second question. "
    "Question to phrase: "
)


async def run(agent_dir: Path, schema_path: Path, output_path: Path) -> None:
    data = yaml.safe_load(schema_path.read_text())
    flow = StateFlow.from_yaml(data)

    agent = Agent.from_directory(agent_dir)
    print(f"Starting interview ({len(flow._order)} questions). Ctrl-C to abort.\n")

    try:
        while not flow.is_complete():
            raw = flow.render()
            phrased = await agent.handle(PHRASING_PROMPT + raw)
            print(f"\n{phrased}\n")
            try:
                response = input("> ").strip()
            except EOFError:
                response = ""
            if not response:
                print("(no answer — skipping)")
                response = "(no answer)"
            flow.submit(response)
    finally:
        if agent._session and not agent._session.closed:
            await agent._session.close()

    _write_output(flow.answers, schema_path, output_path)
    print(f"\nDone. Wrote {output_path}")


def _write_output(answers: dict[str, str], schema_path: Path, output_path: Path) -> None:
    ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# Interview — {schema_path.stem}",
        "",
        f"Captured: {ts}",
        "",
    ]
    for key, value in answers.items():
        lines.append(f"## {key}")
        lines.append("")
        lines.append(value)
        lines.append("")
    output_path.write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an interview from a YAML schema.")
    parser.add_argument("--agent-dir", required=True, type=Path, help="Agent directory")
    parser.add_argument("--schema", required=True, type=Path, help="schema.yaml path")
    parser.add_argument(
        "--output",
        default=Path(f"./interview-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.md"),
        type=Path,
        help="Where to write the captured answers (markdown).",
    )
    args = parser.parse_args()
    try:
        asyncio.run(run(args.agent_dir, args.schema, args.output))
    except KeyboardInterrupt:
        print("\nAborted.")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
