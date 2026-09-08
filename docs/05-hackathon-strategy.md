# Judges, Astra, and hackathon strategy

Status: design recommendations for review · researched 2026-09-08 · no implementation yet

## Recommended positioning

**“Autorebaser keeps your feature working when main changes, then shows you the evidence for the repair.”**

Keep the SQLAlchemy bulk-import fixture. Its missing records make the risk understandable to investors, while the isolated baselines, transaction diagnosis, commit mapping, and persistence check give engineers something substantive to inspect. The Manim explanation makes an invisible lifecycle change visible.

The user-supplied rubric gives 25% each to Astra in development, Astra in the product, live demo, and technical implementation. OpenAI reviewers select the five finalists first; the named judges matter most for stage and Q&A preparation. Make the one-minute submission independently demonstrate the rubric instead of assuming its viewers have read the design docs.

## Judge backgrounds and relevant emphasis

Background statements below come from public professional sources. Suggested connections and questions are our inferences, not claims about private preferences or promises about how anyone will score the project.

### Urvashi Barooah — enterprise applications and operational automation

Redpoint lists Urvashi as an early-stage partner focused on enterprise applications. Previously she advised companies at BCG and EY on strategy, M&A, and pricing. Her listed investments include Boon, Champ AI, Gradient Labs, and Maxima, spanning operational workflows and agents. [Redpoint biography and investments](https://www.redpoint.com/our-people/urvashi-barooah/)

Her contributions to Redpoint's 2026 outlook discuss agents taking over work in procurement, insurance, and accounting. [Redpoint outlook](https://www.redpoint.com/content-hub/written/2026-outlook/)

**Connection:** emphasize a complete recurring engineering task: detect the integration failure, repair it, run the checks, and deliver a reviewable PR. Define the initial user as an engineer maintaining a long-lived branch and the likely organizational buyer as an engineering/platform lead; these are customer hypotheses to validate.

**Show:** one completed work item, human interventions, measured runtime/cost, and a reviewer-ready handoff. Say that the video is intended to reduce review effort; do not claim a measured reduction until someone has tested that.

**Prepare for:** “How often does this happen, who adopts it, and what work does it eliminate?” Use actual team experience or measured trials. Do not invent a market-size or time-savings statistic.

### Pranav Reddy — AI systems and engineering

Pranav's own site identifies him as a partner at Conviction. He previously engineered indexing, retrieval, and language-modeling systems at Neeva, and before that researched neuroscience. [Personal biography](https://pgreddy.com/)

**Connection:** make the technical value of Astra observable. Show it combining the upstream change, the feature's intent, and a failing behavioral check to propose a nontrivial repair. Give it a fixture variant whose reference fix was never supplied to the runtime agent.

**Show:** the failure, relevant source evidence, patch, and independent check. Keep a record of model calls, repair attempts, and failures so there is a concrete answer about the system's reliability.

**Prepare for:** “How much is a scripted migration, and how much is model-driven?” Be explicit that orchestration, validation policy, and scene templates are deterministic, while diagnosis, code adaptation, and explanatory content are generated from each run. This question is our preparation suggestion, not an attributed quotation.

### Romain Huet — developer platforms and usable model capabilities

Romain leads Developer Experience at OpenAI. His background includes developer-platform work at Stripe and Twitter and co-founding Jolicloud. His public work covers APIs, coding tools, and multimodal developer experiences. [AI Engineer biography](https://ai.engineer/speakers/romain-huet)

In a Stripe Sessions discussion, he describes working with developers on model tradeoffs and taking API-backed applications through to production. [Stripe Sessions transcript](https://stripe.com/nl/sessions/2024/how-can-we-help-everyone-become-a-10x-engineer)

**Connection:** present a clean path from task input to useful artifact. The manual trigger is sufficient; the result should open easily, explain itself, and link to real code/tests. Show the precise roles of Astra, Git, the test runner, and Manim.

**Show:** a real model-backed run, actual PR, readable explanation, and clear failure handling. If time permits, add Astra's visual inspection of rendered frames as a purposeful use of image input.

**Prepare for:** “Which Astra capabilities are you using, and where does your engineering add value?” Answer with specific observed actions and artifacts.

### Shawn “swyx” Wang — coding agents, developer tools, and agent engineering

swyx co-founded AI Engineer and Latent Space and has worked in developer tools and developer experience. [AI Engineer biography](https://ai.engineer/speakers/swyx)

His own September 2025 essay announced joining Cognition while continuing AI Engineer and Latent Space independently. It argues for the importance of coding-agent integration details and discusses asynchronous delegation. [His Cognition essay](https://swyx.io/cognition)

**Connection:** expect familiarity with coding-agent demos. Make the contribution concrete: before/after execution under different dependencies, preservation of the feature's behavior, explicit commit lineage, and an explanation linked to evidence. The video should teach the semantics of the repair.

**Show:** a change that replays cleanly yet fails a behavior check; a valid repair; a small variant; and the boundaries of the evidence. Have a technical answer to “Why not just ask Codex or Devin?” rather than claiming general agents cannot perform rebases.

**Prepare for:** questions about the execution harness, evaluation cases, nondeterminism, and how the product improves on an ordinary coding-agent session. These are inferred preparation topics.

### Lan Xuezhao — AI-driven work and rigorous experimentation

Lan founded Basis Set. Her background includes brain research, a brain-training company, McKinsey, and building Dropbox's Corporate Development Strategy team. She holds an M.A. in Statistics and a Ph.D. in Psychology. [Basis Set biography](https://www.basisset.com/team-members/dr-lan-xuezhao)

Basis Set's portfolio explicitly spans automated workflows, collaboration, infrastructure, and autonomy. [Portfolio](https://www.basisset.com/portfolio)

**Connection:** explain how this changes engineering work: the agent performs integration and prepares evidence; the engineer reviews intent and the remaining uncertainty. Show whether the complete workflow succeeds repeatedly, and how much intervention it needs.

**Show:** an honest rehearsal record, one useful result, and a narrow initial adoption path. A later product could learn repository-specific constraints from accepted repairs, but that is roadmap work, not an implemented moat.

**Prepare for:** “Can this become a repeatable workflow, and does it save enough effort after review?” Measure the cost of both repair and review rather than only generation speed.

## Make Astra's role specific

The launch post highlights software engineering, computer use, visual judgment, structured artifact creation, and improved preservation of intent. It also reports 63.9% on OpenAI's internal database-migration evaluation versus 42.7% for GPT-5.6 Sol. Those are vendor-reported benchmark results, not expected Autorebaser performance. They support the choice of a database-related integration demo. [Astra launch post](https://openai.com/index/gpt-6-astra/)

The API documentation lists function calling, structured outputs, image input, and a large context window for `gpt-6-astra`; output is text. Astra can author the storyboard and inspect frame images while Manim renders the actual video. [Astra model documentation](https://developers.openai.com/api/docs/models/gpt-6-astra)

| Project use | Evidence to show |
| --- | --- |
| Diagnose and adapt across code, Git history, tests, and migration notes | Real tool actions, relevant input references, and resulting patch |
| Preserve feature intent through the change | Original behavior checks and external evaluator results |
| Produce a concise visual explanation | Structured storyboard, rendered scene, and claim-to-evidence links |
| Optionally review its own rendered frames | Actual frame inputs and a recorded useful revision, if one was needed |

The launch's experimental cross-context notes/search concern the Codex harness. Do not claim a custom API runner automatically inherits them. Use that feature during development only if actually enabled and useful; no need to inflate context or force a long run to demonstrate it. [Launch coding section](https://openai.com/index/gpt-6-astra/)

One competitive caution: the launch already discusses Cognition's improved testing videos and reports. Our proposed distinction is a causal animation connected to the upstream change, adapted commits, and checks. Treat novelty as a hypothesis to demonstrate, not a claim that no other agent can explain code. [Launch example](https://openai.com/index/gpt-6-astra/)

## Features to prioritize against the rubric

| Priority | Feature or evidence | Why it earns its place |
| --- | --- | --- |
| Required | Astra repair loop, independent behavior checks, and actual draft PR | Establishes the product works and Astra does consequential work |
| Required | Compact evidence panel in the existing review artifact | Makes correctness and engineering decisions inspectable |
| Required | Generated Manim explanation with source-linked claims | Memorable, useful output tied to this run |
| Required | Record how Astra helped build the project | Directly addresses the separate development score |
| Next | One fixture variant with no reference fix given to the agent | Tests whether the workflow extends beyond rehearsal |
| Stretch | Astra reviews rendered frame images | Adds relevant multimodal use after core reliability |

Keep automatic triggers, voice narration, arbitrary-language support, a large dashboard, and a second complex demo out of the critical path. Use the existing planned review HTML for the evidence panel rather than building a separate frontend product.

For development evidence, maintain a short log of real tasks: problem, human direction, Astra's contribution, an actual correction or iteration, and the verified result. Link commits, test outputs, or before/after frames. Select two or three examples for submission/Q&A. See the [implementation and validation record](06-implementation-and-validation.md) for the working prototype and measured results.

## One-minute submission video

Record the working product. Aim to finish at 58–60 seconds. Use readable screen capture and captions; show a short excerpt of the generated video inside the recording.

| Time | Screen and narration purpose |
| --- | --- |
| 0–6 s | Hook: original feature has three saved bookmarks; the mechanical integration loses them |
| 6–15 s | Source/main refs, manual trigger, and Astra's actual run progress |
| 15–29 s | Observed failure, agent repair, and fresh-process persistence result |
| 29–44 s | Fifteen seconds of the generated causal explanation |
| 44–53 s | Real draft PR, tested commit, preserved dependency version, and evidence links |
| 53–60 s | One authentic development example and a concise statement of Astra's runtime role |

Edit waiting time, with elapsed run time visible or disclosed. If the live agent never produced a particular intermediate failure, label any comparison as the separate mechanical-control run. All candidate results and video excerpts must belong to the identified run.

Possible narration, to adapt to actual results: “Our feature worked until main upgraded the database library. After the obvious import fix, the command still reported success—but its records were missing. We asked Autorebaser to bring the branch forward. Astra inspected both histories, found the behavioral break, and adapted the feature. A new process confirms that the records persist. The draft PR includes the repair and this generated explanation of why it was needed. Every claim links to code or a recorded check. We also used Astra during development for [specific verified contribution].”

## Three-minute stage demo

| Time | Live action |
| --- | --- |
| 0:00–0:15 | Show the feature and the three-record contract |
| 0:15–0:30 | Trigger the bot, or disclose that a fresh run was started before stage |
| 0:30–1:05 | Show the main update and execute the labeled mechanical-control check |
| 1:05–1:45 | Inspect the completed candidate and execute its persistence check in a new process |
| 1:45–2:10 | Play 20–25 seconds of its generated explanation |
| 2:10–2:30 | Open the PR/evidence links and show one development example |
| 2:30–2:50 | Change the input data and rerun the candidate's importer live |
| 2:50–3:00 | State the demonstrated scope and who the product is for |

Changing input data verifies the working application; it is not evidence of generalization to a new migration. Keep the separate migration-variant evaluation available for Q&A. Rehearsal determines whether a whole fresh repair fits on stage. Use a clearly identified prior run if infrastructure fails, and still operate the working candidate live where possible.

## Two-minute Q&A preparation

- **Why not just use a coding agent?** The model supplies coding ability; this product packages repeatable baselines, preserved feature contracts, Git/PR bookkeeping, and an inspectable explanation into one task. Compare on the actual workflow, not a claim of exclusive model capability.
- **Can the agent cheat the tests?** Trusted checks live outside its editable checkout; track original tests and dependency pins. Passing these checks supports a bounded claim, not universal correctness.
- **Is the demo hardcoded?** The fixture is engineered and documented. The runtime receives code, requirements, and failures, not the reference patch or prewritten explanatory text. Disclose fixed orchestration and scene templates.
- **Why a video?** Transactions and data flow are temporal; animation can explain the cause quickly. Text and code remain available. Reviewer time savings still need measurement.
- **What did Astra actually do?** Show model-tagged repair/storyboard calls and real development artifacts. Distinguish generated content from the deterministic runner and renderer.
- **What happens on an uncertain repair?** Stop success publication and deliver diagnostics. Show an actual example only if tested; otherwise describe it as designed behavior.

## Submission discipline

The supplied deadlines are 5:30 PM submission and 6:45 PM finalist demos. The date and timezone were not specified in the brief; treat these as event-local times rather than creating an automated schedule.

Suggested checkpoints: freeze features by 4:30 PM, complete a cold rehearsal by 4:45, record/export by 5:00, upload by 5:15, and verify playback plus receipt by 5:25. Check the CV platform's access and format requirements before upload. Keep the final video, repository links, team details, and model-development explanation together. These are planning recommendations; nothing has been submitted or scheduled.
