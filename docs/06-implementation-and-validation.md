# Implementation and validation record

The prototype performs a real Git rebase, asks GPT-6 Astra for a source repair, tests a fresh checkout of the committed candidate, and generates a Manim explanation. The demo repository and controller are separate histories in the same GitHub repository: controller on `main`, migration on `demo/main`, original feature on `demo/feature`, and repaired feature on `codex/autorebase/astra-demo`.

## Measured runs — September 8, 2026

| Run | Actual model proposals | Final suite | Independent persistence probe | Total time |
| --- | --- | --- | --- | --- |
| First end-to-end run | 1 | 8 executions, including duplicate discovery | 5 of 5 records | 65.18s |
| Renamed importer module | 1 | 6 tests | 5 of 5 records | 65.02s |
| Published demo bundle | 1 | 6 tests | 5 of 5 records | 75.31s |

These are three rehearsals of one constructed migration scenario, not a general benchmark. The renamed module tests that the repair is not tied to the original importer filename. Each run used `gpt-6-astra` through an authenticated Codex CLI session, with medium reasoning effort. No canned patch was supplied to the repair model. The import-only comparison is a separate, explicitly scripted control.

The selected run's [model-call record](../showcase/astra-demo/model-calls.json) reports 10.801 seconds for the repair proposal and 21.471 seconds for the storyboard. Total runtime also includes environment preparation, Git operations, validation, rendering, and video decoding. The resulting [Manim video](../showcase/astra-demo/video.mp4) is 58.71 seconds at 1280×720, 24 fps. It has captions and no audio narration.

## What the selected run establishes

- Original feature and upstream target pass in separate SQLAlchemy 1.4.54 and 2.0.36 dependency environments.
- Git replays the two feature commits without a text conflict. Execution then fails on the moved module.
- Changing only the import lets the command report five imports, but an external probe sees zero rows after the process exits.
- Astra changes the import and replaces `engine.connect()` with `engine.begin()` in one proposal.
- The final six-test suite and independent five-record probe pass on commit `b77334b5cca513cdd61f4493a3883dfa2e9e7bab`, checked from a fresh worktree.
- The controller preserves tests, dependency pins, and configuration. The run includes original/rebased commit mappings and a range-diff.

Read the [repair diff](../showcase/astra-demo/patches/repair.diff), [final probe](../showcase/astra-demo/checks/final-persistence.json), and [full evidence](../showcase/astra-demo/evidence.json). Download the repository and open `showcase/astra-demo/review.html` for the local review UI.

## Development iterations

The human direction was a manually triggered repair bot, a developer explanation video, and a compelling real behavior regression. This Codex development session produced the architecture documents, CLI controller, fixture, model adapters, tests, report, and renderer, then used actual commands and decoded frames to verify them.

Three concrete iterations are visible in the work:

1. The first real model response included a statement that the inference process had not run tests. The controller had run them. The prompt now asks for a code-change summary, and the report uses per-file repair reasons. The explanation attributes checks to the controller.
2. The first fixture discovered base tests twice. Importing the test module instead of its class removed duplicate discovery. Subsequent runs execute six tests.
3. The first video showed outcome cards. The final renderer animates the exact removed and added source lines before transitioning to persisted-row counts. The storyboard receives complete upstream, feature, and repair diffs alongside the checks.

The local controller suite passes 18 tests covering fixture replay, baseline failure, protected edits, atomic patch validation, path/symlink escapes, credential environment filtering, stale publication, and evidence references. [GitHub CI passed all 19 tests](https://github.com/Jackmin801/autorebaser/actions/runs/34268860339), including the Docker integration test, in 34.03 seconds. Locally that test is skipped because the daemon is stopped. Representative rendered frames and the report's navigation were visually inspected.

The bot's own `publish` command opened [draft PR #1](https://github.com/Jackmin801/autorebaser/pull/1) after checking remote source and target SHAs. A second invocation reused the same PR and posted a successful verification status to the exact candidate commit. The draft is open and unmerged.

## Boundaries

Local rehearsals use trusted fixture code, not an OS sandbox. The Docker executor uses read-only source mounts and network-disabled tests; its integration check passed in CI. The Responses API adapter and manual Actions workflow require an `OPENAI_API_KEY` repository secret for an actual model run and have not been exercised end to end. The authenticated Codex provider and GitHub CLI publisher have been exercised locally.

The prototype supports configured Python repositories, linear feature histories, exact registry dependency pins, and a bounded source repair loop. It does not yet discover arbitrary dependency migrations, handle arbitrary languages, generate independent tests for arbitrary projects, narrate audio, or establish broad semantic equivalence. The external persistence probe is specific to the bookmark demo. Conflicts outside editable source roots stop for review. Passing these checks supports this recorded behavior on these inputs.

## Demo delivery

Use the CLI to start a fresh run, then show the evidence table and the import-only control's `5 imported / 0 persisted` output. Open the repaired source and final `5 persisted` proof. Play the source-change segment of the Manim video and open the actual draft PR. A one-minute hackathon submission should record those working surfaces; the generated explanation video is an artifact of the product, not a substitute for demonstrating the product.

For the three-minute stage slot, start the run immediately, explain the clean rebase and silent regression while it executes, then open the new report. Keep the completed bundle available as a labeled rehearsal if the network is slow. Do not present cached results as a new live run.
