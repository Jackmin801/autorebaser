# Product and scope

Status: proposed for review · 2026-09-08

## Product promise

“Bring my branch forward, keep my feature working, and show me why the changes are necessary.”

The reviewer should receive a draft PR containing the adapted feature, reproducible test evidence, and a 60–90 second Manim explanation. The explanation answers three questions: what changed upstream, which assumptions in the feature became invalid, and what the bot changed to preserve its behavior.

For this hackathon, use GPT-6 Astra in both development and the running product, and retain evidence of each. The competition submission is a separate one-minute recording of the working product, including a short excerpt of its generated explanation. See [hackathon strategy](05-hackathon-strategy.md) for the supplied rubric and three-minute stage plan.

Git rebase replays commits on a new base. Import moves and renamed functions are examples of changes that can break that integration; they are not themselves the reason developers rebase. A successful replay is only the beginning of validation. [Git rebase documentation](https://git-scm.com/docs/git-rebase)

## Developer workflow

1. Select a repository, source branch, and target branch. Start a run manually.
2. See progress: checking baselines → replaying commits → repairing → testing → explaining → publishing.
3. Open the resulting draft PR. Read the short summary or watch the video, then inspect the linked code and test evidence.
4. Review and merge through the normal repository process.

The hackathon entry point is a CLI, followed by a thin manually dispatched GitHub Actions wrapper using that same CLI. No webhook service, scheduler, or custom dashboard is required. GitHub supports manual workflow dispatch from its UI and CLI. [Manual workflow documentation](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow)

## One repair engine, two inputs

| Mode | Input | Candidate construction | PR destination |
| --- | --- | --- | --- |
| Rebase | Source feature branch and target main branch | Replay the feature onto a pinned target commit; adapt it | New replacement PR targeting main |
| Package/API upgrade | Source branch and explicit package version or API contract | Apply the requested update, then adapt callers | New PR targeting the source branch |

**Build rebase mode first.** The main demo already includes a package/API migration on main, so it exercises those repairs without requiring a dependency-discovery product. Standalone package upgrade is the next increment. An external API update must supply an explicit contract, migration guide, or test fixture; the bot cannot infer a remote change from Git alone.

Dependabot already creates dependency-update PRs and supports rebasing them. Our proposed differentiator is adapting application behavior and explaining the resulting repair with evidence. This is a product direction, not a claim that existing tools never edit application code. [Dependabot PR documentation](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/manage-your-dependency-security/manage-dependabot-prs)

## MVP boundary

Include one trusted GitHub repository, Python projects, a linear feature branch, declared install/test commands, a single tool-using coding agent, isolated execution, a bounded repair loop, draft PR creation, and a templated Manim renderer.

Defer automatic update discovery, arbitrary languages, fork PRs, merge-heavy histories, automatic merging, production database migrations, broad deployment validation, custom animation code, and voice narration.

Use a **new bot branch and replacement PR** for rebases. This makes the result reviewable without rewriting the developer's branch. Link the original PR if one exists, but leave closing or replacing it to the developer. Updating the existing PR in place is a later, explicitly enabled option because it requires rewriting branch history.

## Definition of a successful run

- Original feature and target baselines pass in their own pinned environments.
- The final candidate passes the target checks and the feature's behavior checks.
- Requested dependency versions and upstream behavior remain intact.
- Every original feature commit is accounted for, including any adaptations or already-upstream changes.
- The draft PR points to the exact tested candidate and includes readable evidence.
- The video renders and describes only supported claims about that candidate.

Code, video, and publishing have separate statuses. A successful repair with a failed video render is a useful partial result, but it is not a fully successful product run. Missing tests or an ambiguous behavioral requirement produce “needs review,” not a claim of correctness.

## Decisions to review

| Decision | Recommended default | Tradeoff |
| --- | --- | --- |
| First language | Python | Shares tooling with Manim; narrower repository coverage |
| Coding and explanation model | GPT-6 Astra | Makes the required model central to the product; measure actual latency and cost |
| Main demo | SQLAlchemy migration plus feature rebase | Recognizable dependency and visible behavior failure |
| Publishing | New draft replacement PR | Preserves the source branch; creates a second review thread |
| Animation | Structured storyboard plus fixed scene templates | Reliable rendering; less artistic freedom |
| Trigger | CLI, then manual Actions dispatch | Minimal UI work; setup remains visible |
| Validation | Existing tests plus behavior probes grounded in feature intent | Stronger evidence; no universal correctness guarantee |

## Build sequence after review

1. Prove the demo fixture: both original branches pass; mechanical integration fails; a reference repair passes.
2. Build the CLI's clone, baseline, replay, repair, and evidence pipeline.
3. Render a video from one real evidence bundle and check legibility.
4. Add manual Actions execution, artifact upload, and draft PR publication.
5. Rehearse fresh runs and test the harder variant if time remains.

If time is tight, cut standalone upgrade mode and visual polish first. Keep the behavior test, actual PR, and evidence-backed video: those are the product.
