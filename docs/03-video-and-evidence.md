# Video and evidence design

Status: proposed for review · 2026-09-08

## What the video should teach

The video should explain causality, not scroll through a diff. A developer should be able to identify the upstream change, the feature behavior at risk, the necessary adaptation, and the evidence for the result in about a minute.

Use three consistent labels and visual styles: **Upstream** in blue, **Your feature** in purple, and **Repair** in amber. Use icons and text as well as color. Reserve pass/fail markers for observed check outcomes.

Keep a full written explanation beside the video. Developers who prefer text should receive the same facts and source links.

The product's 60–90 second explanation is distinct from the hackathon's one-minute submission video. Use about 15 seconds of the explanation inside the submission and 20–25 seconds on stage; show the running product for the rest. See [the timed scripts](05-hackathon-strategy.md).

## Evidence before animation

Both the PR summary and the video are generated from one validated evidence bundle. The agent writes a structured storyboard; a fixed renderer turns it into a Manim scene. It does not generate arbitrary Python animation programs for each run.

Each claim stores:

| Field | Meaning |
| --- | --- |
| `id`, `kind` | Stable claim ID; upstream change, feature intent, repair, or check |
| `statement` | Short human-readable claim |
| `source_refs` | Exact commit, path, line/hunk or migration-document excerpt |
| `related_claims` | The causal links this claim relies on |
| `repair_refs` | Candidate commit and changed code, if applicable |
| `check_refs` | Recorded commands, exit codes, test/probe IDs, and observations |
| `support` | Observed, inferred from code/docs, or unresolved |

The controller validates references and copies actual snippets from the pinned Git objects. It supplies counts and statuses directly from recorded check results. This verifies provenance, not every causal interpretation: inferred explanations remain labeled, and unsupported claims are omitted or flagged for review.

An allowed statement is “the reconnect test passes on this candidate.” “All behavior is preserved” overstates the evidence. Do not invent a failed intermediate run, exact test counts, or performance numbers to improve the story.

## Reusable scene vocabulary

| Scene | What it shows | Appropriate use |
| --- | --- | --- |
| Commit timeline | Base, main evolution, original feature, adapted feature | Establish what came from whom |
| Code comparison | Small before/after snippets with highlighted tokens | Imports, signatures, local repairs |
| Data-flow diagram | Values or records moving between caller and dependency | Response schemas, units, pagination |
| State transition | Before/after state across a lifecycle boundary | Transactions, retries, resource cleanup |
| Evidence card | Test name, actual result, candidate SHA | Show what was verified |

A storyboard selects scenes, claim IDs, labels, timings, and visual parameters from this vocabulary. Stable claim IDs give the same concepts consistent positions across scenes. If a repair needs an unfamiliar animation, fall back to a code comparison and plain explanation.

## Example 75-second storyboard

This is a proposed script for the fixture in [the demo design](04-demo-and-capabilities.md), conditional on the run actually producing the described evidence.

| Time | Picture | Message |
| --- | --- | --- |
| 0–10 s | Branch graph: main moves ahead; feature adds bulk import | “Your feature imports bookmarks. Main changed the storage module and dependency.” |
| 10–22 s | Old import path connects to its replacement | “The importer needs to follow the new module layout.” |
| 22–40 s | Records enter a connection, then a fresh connection sees an empty database | “The recorded persistence check found that the imported records were missing.” |
| 40–58 s | Highlight the transaction boundary; records remain after closing | Explain the repair using its actual code and the supporting migration reference. |
| 58–75 s | Commit mapping, persistence result, suite result, tested SHA | “The feature is still present. These checks passed on this candidate.” |

If the agent repaired the transaction before any failing check was recorded, replace the middle scene with a labeled explanation of the old assumption and show only observed final evidence.

## Rendering and quality checks

Use Manim Community with a pinned Python/rendering environment, installed fonts, and a fixed palette. Target 720p at 30 fps for the first version; make resolution configurable. Use text and geometric shapes so LaTeX is unnecessary. Manim supports rendering selected scenes, and its installation guide permits skipping LaTeX when only plain text is needed. [Manim configuration](https://docs.manim.community/en/stable/guides/configuration.html), [installation guide](https://docs.manim.community/en/stable/installation/uv.html)

Limit a code panel to roughly eight short lines. Split scenes when text would need to shrink. Build captions into the scene and export a transcript; narration is optional later. Keep filenames and short SHAs visible, with detailed links in the HTML report rather than tiny URLs in the video.

Validate storyboard shape, allowed scene types, existing references, duration, and text bounds before rendering. After rendering, check that the MP4 decodes and has plausible dimensions/duration, then inspect representative frames for clipping and readability. Store the storyboard, renderer version, bundle hash, and video together.

Treat source snippets as escaped text. The renderer gets only the selected evidence, no repository credentials or executable source imports. A render-only retry uses the frozen bundle and never reruns code repair. A failed render leaves the written report available and visibly marks video generation incomplete.

## Optional Astra visual review

After the core workflow is reliable, send representative rendered frames and the referenced claims to Astra as image/text inputs. Ask it to identify unreadable labels, clipping, reversed arrows, or disagreement between a pictured status and recorded evidence. Allow one bounded storyboard revision using the existing scene vocabulary, then render again and retain both versions. This is visual quality review; it cannot establish program correctness or validate every moment of a video from sampled frames. [Astra image-input support](https://developers.openai.com/api/docs/models/gpt-6-astra)
