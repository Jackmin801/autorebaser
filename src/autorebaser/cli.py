from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import uuid

from .util import RunError, read_json, write_json


def main():
    parser = argparse.ArgumentParser(description="Repair a rebase, test the feature, and watch the explanation.")
    commands = parser.add_subparsers(dest="command", required=True)
    fixture = commands.add_parser("fixture", help="Create the reproducible SQLAlchemy migration repository")
    fixture.add_argument("path", type=Path)
    fixture.add_argument("--variant", action="store_true", help="Use a different importer module name")
    for name in ("demo", "rebase"):
        p = commands.add_parser(name, help="Run the complete demo" if name == "demo" else "Repair a configured Python feature branch")
        if name == "rebase":
            p.add_argument("--repo", required=True)
            p.add_argument("--source", required=True)
            p.add_argument("--onto", required=True)
            p.add_argument("--config", type=Path)
            p.add_argument("--demo-probe", action="store_true", help="Enable the bookmark-specific independent probe/control")
        else:
            p.add_argument("--variant", action="store_true")
        p.add_argument("--output", type=Path)
        p.add_argument("--provider", choices=("auto", "api", "codex"), default="auto")
        p.add_argument("--executor", choices=("local", "docker"), default="local" if name == "demo" else "docker",
                       help="local is only for trusted code and is not an OS sandbox")
        p.add_argument("--max-repairs", type=int, choices=range(1, 7), default=3)
        p.add_argument("--no-video", action="store_true")
    render = commands.add_parser("render", help="Render a frozen evidence/storyboard bundle")
    render.add_argument("run", type=Path)
    publish = commands.add_parser("publish", help="Publish a validated candidate as a draft PR")
    publish.add_argument("run", type=Path)
    publish.add_argument("--repo", required=True, help="GitHub owner/repo")
    publish.add_argument("--base")
    publish.add_argument("--source-ref")
    publish.add_argument("--artifact-url")
    args = parser.parse_args()
    try:
        if args.command == "fixture":
            from .fixture import create_fixture
            print(json.dumps(create_fixture(args.path, variant=args.variant), indent=2))
            return 0
        if args.command == "render":
            from .render import render_video
            from .report import write_report
            directory = args.run.resolve()
            state = read_json(directory / "run.json")
            render_video(directory)
            state["video_status"] = "rendered"
            write_json(directory / "run.json", state)
            write_report(directory)
            print(directory / "video.mp4")
            return 0
        if args.command == "publish":
            from .publish import publish
            print(publish(args.run.resolve(), args.repo, base=args.base, source_ref=args.source_ref, artifact_url=args.artifact_url))
            return 0
        from .core import run_rebase
        run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:4]
        output = (args.output or Path("runs") / run_id).resolve()
        if args.command == "demo":
            from .fixture import create_fixture
            fixture_path = Path(".demo") / run_id
            create_fixture(fixture_path, variant=args.variant)
            repo, source, target = str(fixture_path.resolve()), "feature/bulk-import", "main"
            demo, config = True, None
        else:
            repo = str(Path(args.repo).resolve()) if Path(args.repo).exists() else args.repo
            source, target, demo, config = args.source, args.onto, args.demo_probe, args.config
        print(f"\nAUTOREBASER  ·  GPT-6 Astra\nRun: {output}\nExecutor: {args.executor}\n", flush=True)
        state = run_rebase(repo, source, target, output, provider=args.provider, executor=args.executor,
                           max_repairs=args.max_repairs, render=not args.no_video, demo=demo, config_path=config)
        print(f"\nReview: {output / 'review.html'}", flush=True)
        return 0 if state["code_status"] == "passed" and state["video_status"] in ("rendered", "skipped") else 1
    except (RunError, ValueError, FileNotFoundError) as exc:
        print(f"Autorebaser: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
