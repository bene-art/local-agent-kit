"""Runner for the study_buddy template.

Two modes in one session:

  - Explain (default): the user asks questions about the supplied source
    material; the runner injects the source as [SYSTEM DATA] on every
    turn and the agent explains from it.
  - Quiz: triggered by typing `quiz`. The runner loads a YAML schema
    into a StateFlow and walks the user through questions one at a time.
    After each answer the agent grades it (one short phrase). At the
    end, captured answers + grades are written to a markdown transcript.

The source material is loaded once at startup and kept in memory — no
disk hit per turn. The quiz schema is loaded when quiz mode starts.

Run from the kit root:

    python -m templates.study_buddy.run_study \
        --agent-dir templates/study_buddy \
        --source   templates/study_buddy/sources/photosynthesis.md \
        --quiz     templates/study_buddy/quizzes/photosynthesis.yaml
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import sys
from pathlib import Path

import yaml

from local_agent_kit.agent import Agent
from local_agent_kit.memory import QuizProgress
from local_agent_kit.patterns import StateFlow, Step
from local_agent_kit.patterns.narrate_only import envelope


GRADE_PROMPT = (
    "Grade the following answer in one short phrase. Say 'Correct.' or "
    "'Not quite' or similar. If the answer is wrong, state the correct "
    "answer in ONE additional sentence. Do not lecture.\n"
    "\nQuestion: {question}\nAnswer: {answer}"
)


async def explain_turn(agent: Agent, user_input: str, source: str) -> str:
    prompt = user_input + envelope("source material", source)
    return await agent.handle(prompt)


def _is_correct(grade: str) -> bool:
    """Heuristic: does the agent's grade text indicate a correct answer?

    The IDENTITY contract says the grade starts with "Correct." or
    "Not quite" or similar. We check for a positive token AND no
    negative token — both are required because a model might say
    "Not quite — the correct answer is X" and we should NOT count that
    as correct.
    """
    g = grade.lower()
    negative = any(kw in g for kw in ("not quite", "incorrect", "wrong", "no,", "not exactly", "actually,"))
    if negative:
        return False
    return any(kw in g for kw in ("correct", "right", "yes,", "exactly", "spot on"))


async def quiz_loop(
    agent: Agent,
    flow: StateFlow,
    progress: QuizProgress | None = None,
    quiz_id: str = "",
) -> dict[str, dict[str, str]]:
    """Walk the user through every step in the flow.

    Returns a mapping of step_id -> {"question", "answer", "grade"}.
    If `progress` is supplied, records each grading result so future
    sessions can prioritize weak spots.
    """
    transcript: dict[str, dict[str, str]] = {}

    while not flow.is_complete():
        question_text = flow.render()
        step_id = flow.current.id
        print(f"\n{question_text}\n")
        try:
            answer = input("> ").strip()
        except EOFError:
            print()
            break
        if not answer:
            answer = "(no answer)"

        grade = await agent.handle(GRADE_PROMPT.format(question=question_text, answer=answer))
        print(f"\n{grade}\n")
        transcript[step_id] = {
            "question": question_text,
            "answer": answer,
            "grade": grade,
        }
        if progress is not None and quiz_id:
            progress.record(quiz_id, step_id, correct=_is_correct(grade))
        flow.submit(answer)

    return transcript


def _write_transcript(transcript: dict[str, dict[str, str]], output_path: Path, quiz_path: Path) -> None:
    ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"# Quiz — {quiz_path.stem}", "", f"Taken: {ts}", ""]
    for step_id, row in transcript.items():
        lines.append(f"## {step_id}")
        lines.append("")
        lines.append(f"**Q:** {row['question']}")
        lines.append("")
        lines.append(f"**A:** {row['answer']}")
        lines.append("")
        lines.append(f"**Grade:** {row['grade']}")
        lines.append("")
    output_path.write_text("\n".join(lines))


def _reorder_flow(data: dict, progress: QuizProgress, quiz_id: str) -> StateFlow:
    """Build a StateFlow whose step order prioritizes never-seen and
    wrong-recently questions for the given quiz."""
    raw_steps = data.get("steps") or []
    by_id = {str(s["id"]): s for s in raw_steps if isinstance(s, dict) and "id" in s}
    step_ids = list(by_id.keys())
    ordered_ids = progress.order_steps(quiz_id, step_ids)

    ordered_steps = [
        Step(
            id=str(by_id[sid]["id"]),
            prompt=str(by_id[sid]["prompt"]),
            capture=bool(by_id[sid].get("capture", True)),
            follow_up=by_id[sid].get("follow_up"),
            next=by_id[sid].get("next"),
        )
        for sid in ordered_ids
    ]
    return StateFlow(ordered_steps)


async def run(
    agent_dir: Path,
    source_path: Path,
    quiz_path: Path | None,
    output_dir: Path,
    progress_db: Path | None,
) -> None:
    source_text = source_path.read_text()
    agent = Agent.from_directory(agent_dir)
    progress = QuizProgress(progress_db) if progress_db else None

    print(f"Loaded source material from {source_path.name} ({len(source_text)} chars).")
    if quiz_path:
        print("Quiz available — type `quiz` to start.")
    if progress:
        print(f"Tracking cross-session progress in {progress_db}.")
    print("Type your question (or `quit` to exit).\n")

    try:
        while True:
            try:
                user_input = input("> ").strip()
            except EOFError:
                print()
                break
            if not user_input:
                continue
            if user_input.lower() in {"quit", "exit"}:
                break

            if user_input.lower() == "quiz" and quiz_path:
                data = yaml.safe_load(quiz_path.read_text())
                quiz_id = quiz_path.stem
                if progress:
                    flow = _reorder_flow(data, progress, quiz_id)
                else:
                    flow = StateFlow.from_yaml(data)
                transcript = await quiz_loop(agent, flow, progress=progress, quiz_id=quiz_id)
                if transcript:
                    output_path = output_dir / f"quiz-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
                    _write_transcript(transcript, output_path, quiz_path)
                    print(f"\nTranscript written: {output_path}\n")
                    if progress:
                        stats = progress.stats(quiz_id)
                        score = sum(s["correct_count"] for s in stats.values())
                        total = sum(s["correct_count"] + s["wrong_count"] for s in stats.values())
                        print(f"Lifetime score: {score}/{total} across all sessions of this quiz.\n")
                continue

            response = await explain_turn(agent, user_input, source_text)
            print(f"\n{response}\n")
    finally:
        if agent._session and not agent._session.closed:
            await agent._session.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the study_buddy template.")
    parser.add_argument("--agent-dir", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path, help="Source material file (markdown or text).")
    parser.add_argument("--quiz", type=Path, default=None, help="Optional quiz schema YAML.")
    parser.add_argument("--output-dir", type=Path, default=Path("."), help="Where to write quiz transcripts.")
    parser.add_argument(
        "--progress-db",
        type=Path,
        default=Path("./study_progress.db"),
        help="SQLite file for cross-session quiz progress. Pass '' to disable.",
    )
    args = parser.parse_args()
    progress_db = args.progress_db if str(args.progress_db) else None
    try:
        asyncio.run(run(args.agent_dir, args.source, args.quiz, args.output_dir, progress_db))
    except KeyboardInterrupt:
        print("\nClosed.")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
