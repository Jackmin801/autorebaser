# Autorebaser

Manually trigger a bot to adapt a branch to an upstream change, test the result, open a draft PR, and generate a short Manim video explaining the repair.

**Python prototype. GPT-6 Astra repairs the source and writes the storyboard; Git, tests, and Manim produce the evidence and video.**

[Watch a real run's explanation](showcase/astra-demo/video.mp4) · [Inspect the repair and evidence](showcase/README.md) · [Validation record](docs/06-implementation-and-validation.md)

## Try the demo

Use Python 3.11+ and [uv](https://docs.astral.sh/uv/). For Manim on macOS, install `cairo` and `pkgconf` with Homebrew. Linux needs Cairo/Pango development packages and pkg-config.

```sh
uv venv --python 3.12
uv sync --frozen --extra video --extra dev
.venv/bin/autorebaser demo --provider codex --executor local --output runs/my-demo
```

Activate `.venv` first or invoke `.venv/bin/autorebaser`. The Codex provider uses an existing `codex login` session with model `gpt-6-astra`. It requests a structured proposal in a read-only, ephemeral session. The controller applies and tests that proposal. Alternatively, set `OPENAI_API_KEY` in your shell and use `--provider api` for Responses API function calls. Never put credentials in a run configuration or Git.

Open `runs/my-demo/review.html`. It contains the Manim player, source changes, check results, exact dependency environments, and run activity. The run directory must be new. Add `--variant` for a different importer module, `--no-video` for a faster code-only run, or `--executor docker` for containerized checks when Docker is running. **Local execution is for trusted repositories only; it is not an OS sandbox.**

The fixture uses a real SQLAlchemy 1.4 → 2.0 upgrade. The original feature and target each pass their own checks. The separately labeled import-only control reports success but persists zero records. Astra must adapt the feature, and a trusted probe checks the database from outside the writing process.

## Bring a configured branch forward

```sh
autorebaser rebase --repo /path/to/repository \
  --source feature/example --onto main --executor docker --output runs/example
```

The target branch must contain `autorebaser.json`, or supply `--config /path/to/trusted-config.json`:

```json
{
  "requirements": "requirements.lock",
  "test_command": ["{python}", "-m", "unittest", "discover", "-s", "tests", "-v"],
  "editable_roots": ["app/"],
  "intent": "Preserve the feature's documented behavior."
}
```

Requirements must be exact registry pins (`package==version`). Test commands are argument arrays. The MVP edits Python source under the configured roots, never tests, dependencies, hidden files, or files outside the clone. Feature branches must be linear, with one merge base. Conflicts outside editable roots, baseline failures, unsupported inputs, or an exhausted repair budget produce a diagnostic report.

## Publish a reviewed run

```sh
autorebaser publish runs/example --repo Jackmin801/autorebaser \
  --artifact-url https://github.com/Jackmin801/autorebaser/actions/runs/RUN_ID
```

Set `GH_TOKEN`/`GITHUB_TOKEN` or authenticate `gh`. The bot checks that remote source and target heads still match the tested inputs, pushes a new branch, and creates a draft PR. It never force-pushes or merges. Publishing is retriable, with existing PR detection. `--base` and `--source-ref` map local fixture refs to corresponding remote demo refs; their SHAs must match.

The **Run Autorebaser** Actions workflow is a manual trigger. Configure an `OPENAI_API_KEY` repository secret, allow Actions to create PRs, and provide `demo/main` and `demo/feature` branches containing the fixture history. It runs the trusted controller from `main`, uses Docker for checks, and uploads a review bundle with 14-day retention. No scheduled automation is enabled.

## Verify and render

```sh
python -m pytest -q
autorebaser render runs/my-demo
```

The video renderer uses fixed Manim scene types, escapes text, and decodes the resulting MP4 with PyAV. It exports representative frames for visual inspection. Video failure is recorded separately from code validation; generated explanations are interpretations linked to evidence, not a proof of universal correctness. A deterministic transcript is clearly labeled if storyboard generation fails.

## Review order

1. [Product and scope](docs/01-product.md) — developer workflow, MVP boundary, and decisions.
2. [Technical design](docs/02-technical-design.md) — Git handling, repair loop, validation, and publishing.
3. [Video and evidence design](docs/03-video-and-evidence.md) — how the explanation stays grounded in the actual run.
4. [Demo and capability map](docs/04-demo-and-capabilities.md) — recommended demo, common breakages, harder challenges, and evaluation.
5. [Judges, Astra, and hackathon strategy](docs/05-hackathon-strategy.md) — sourced judge backgrounds, feature priorities, the one-minute submission, and three-minute stage script.

The fifth document incorporates the supplied judging rubric and supersedes the original presentation timing. Start there for the competition strategy.

**Recommendation:** lead with a real SQLAlchemy migration that makes a new bulk-import feature appear to succeed while its records fail to persist. Show the bot preserve the feature, produce a tested repair, and animate the cause. Use import-path changes as the opening beat.

The design documents describe the intended product and broader roadmap. The CLI behavior and limits above describe this prototype. Standalone package-update mode, automatic discovery, narration, and automatic visual self-review remain follow-on work.
