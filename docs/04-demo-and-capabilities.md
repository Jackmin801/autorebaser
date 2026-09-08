# Demo and capability map

Status: proposed for review · 2026-09-08

## Recommended headline: “The import succeeded. Where did the records go?”

Use a tiny Python bookmark manager backed by a local, file-based SQLite database. The feature branch adds a bulk-import command. Meanwhile, main moves the database module and upgrades SQLAlchemy from a pinned 1.4 release to a pinned 2.0 release.

This is grounded in a real migration: SQLAlchemy 2.0 removed library-level implicit autocommit. Code that executes writes through a connection may need an explicit transaction/commit. Its migration guide describes `Engine.begin()` and explicit commit patterns. [SQLAlchemy migration guide](https://docs.sqlalchemy.org/en/20/changelog/migration_20.html#library-level-but-not-driver-level-autocommit-removed-from-both-core-and-orm)

The proposed fixture uses that behavior to create an understandable failure. The following branch layout and outcomes are design targets to prove before building the bot.

### Fixture history

```text
           M1 --- M2    main
          /
         B
          \
           F1 --- F2    feature/bulk-import
```

`M1` moves the module; `M2` upgrades the dependency and migrates existing commands. `F1` adds the importer; `F2` adds its persistence tests.

- **Base B:** SQLAlchemy 1.4 in legacy mode, a database module, a single-bookmark command, and list/search commands. All checks pass.
- **Main M:** moves `app/db.py` to `app/storage/db.py`, upgrades the dependency, and adapts its existing commands. Main is independently green.
- **Feature H:** adds `app/importer.py` and CLI registration, importing the old module. Its writes use the old connection idiom. Tests verify that successful imports survive a reconnect. The original feature is green with its own lockfile.
- **Integration:** new importer code can replay cleanly because main did not edit that file. Its old import fails first. After that mechanical repair, the persistence probe exposes the behavior problem.

Keep the core fixture free of forced textual conflicts. A clean Git replay followed by a real failure is itself valuable. If desired, add a separately named variant where both branches modify CLI registration, yielding one conventional conflict before the same behavioral challenge.

### Observable contract

Import three unique bookmarks into a fresh file database, terminate the command, then list bookmarks through a new process. Expect exactly those three URLs and titles; a success message or a query inside the writer's connection is insufficient evidence.

Use already-existing feature tests as the primary oracle. Add an independently maintained fixture check outside the agent's editable checkout that runs the CLI and inspects the persisted result. Include empty input and existing list/search behavior. Do not quietly introduce a new requirement that failed imports must be atomic; if error/partial-write behavior matters, specify and test it separately.

The expected repair updates the import and introduces the appropriate transaction boundary for the feature's writes, while keeping main's new dependency and the bulk-import command. Merely copying main would lose the new feature and fail the CLI contract. Downgrading the package would fail the requested-version gate.

### Establish the demo's validity first

| Control | Required result |
| --- | --- |
| Original feature with old lock | Feature checks pass |
| Main with new lock | Existing application checks pass |
| Replayed feature with only import-path repair | Persistence check fails |
| Human reference repair, kept out of agent inputs | Full fixture checks pass |
| Agent's final candidate | Same external behavior checks pass; dependency remains upgraded |

Choose exact compatible Python and dependency pins during fixture implementation; do not use floating “latest” versions. The 1.4 fixture must avoid opting into the newer transaction behavior in advance. Use fresh file databases and processes for every case. Cache the dependency artifacts and migration excerpt so the live demo needs no application API service.

### Competition format

The supplied rules require a **one-minute submission recording**, then a **three-minute live demo plus two minutes of Q&A** for finalists. Follow the [updated timed scripts and judge preparation](05-hackathon-strategy.md). The longer product explanation is excerpted inside those demos.

The presentation schedule is not a latency claim. If rehearsal shows the repair exceeds the stage window, start it beforehand and disclose that it is already running. Keep a recorded successful run with its real SHAs and logs as a clearly labeled fallback. Do not present prerecorded output or the mechanical control as actions taken by the live agent.

## What commonly breaks?

These are recurring engineering categories, not a measured frequency ranking. The most frequent problems will vary with language, framework, repository structure, and branch age. Import changes are a useful first case, but overlap in ordinary feature edits and configuration is also worth supporting.

| Category | Example | What makes a correct repair harder than replacing text? |
| --- | --- | --- |
| Overlapping edits | Both branches extend one CLI dispatcher | Preserve both additions and their order |
| Files/modules move | Public import path changes | Distinguish moved symbols from deleted behavior |
| Renamed or removed functions | Helper replaced by a new service method | Trace callers and adapt argument/return semantics |
| Signature changes | New required context; positional arguments become keywords | Find the correct value at each caller |
| Return-shape changes | List becomes an envelope or iterator | Preserve all records and error handling |
| Validation/default changes | Nullable field becomes required unless given a default | Preserve intended omitted/null distinctions |
| Dependency/configuration drift | Runtime floor, plugin peer range, lockfile changes | Find a compatible dependency set without broad churn |
| Test and fixture drift | Mock interface changes with a dependency | Adapt setup without weakening assertions |
| Data model changes | Column split; identifier type changes | Preserve relationships and backward compatibility |
| Lifecycle changes | Explicit transactions; sync work becomes async | Place ownership, cleanup, and error boundaries correctly |
| Behavioral changes | Different units, defaults, ordering, or timezone handling | Passing types and imports may conceal wrong results |

For another real package example, Pydantic's migration guide distinguishes required fields from nullable fields and describes changed union handling. That makes a good smaller demo around request compatibility. [Pydantic migration guide](https://pydantic.dev/docs/validation/latest/get-started/migration/)

## Harder demonstrations

The SQLAlchemy fixture is a strong product demo, but a documented migration is not by itself evidence of frontier capability. More compelling capability evidence comes from unfamiliar combinations, nonlocal changes, incomplete tests, and a correct decision when the requirements do not determine an answer.

| Challenge | Concrete failure | Evidence to demand | Demo fit |
| --- | --- | --- | --- |
| Async plus cursor pagination | Export contains only the first page after an API change | More-than-one-page fixture, every expected ID once, empty result, correct async callers | Best stretch case; very visual |
| Retry semantics and idempotency | Timeout causes one user action to create two records | Fault injected after server write but before acknowledgment; one resulting operation | Strong systems reasoning; more infrastructure |
| Units and time boundaries | Seconds interpreted as milliseconds; end date changes inclusion | Boundary values and independent expected outputs | Compact, but easy to make too synthetic |
| Schema split across layers | One field becomes structured data across API, model, and UI | Old/new contract cases and behavior through the full stack | Broad and impressive; larger build scope |
| Transaction ownership | A nested helper commits work the outer operation should own | Injected failure, documented rollback contract, independent persistence check | Harder extension of the main demo |
| Ambiguous intent | New API default conflicts with an undocumented feature assumption | Bot identifies both plausible behaviors and asks for the missing decision | Useful evidence of judgment |

For the stretch fixture, evolve a local fake API from “return all items” to “return one page plus a cursor,” with async calls. A branch adds an export containing filtering and totals. Require every matching record across three pages exactly once, including empty results. The agent must adapt the call chain while preserving the export's external behavior. Label the API as a purpose-built fixture; do not imply that a real vendor made this exact migration.

## How to show capability credibly

Use one visible rehearsal case and two variants whose fixes are not supplied to the agent. Vary module layout, a wrapper around the changed API, and fixture data. Keep the external evaluator read-only to the repair loop; it can return failures, but never the reference patch.

Compare the bot with plain Git replay and a documented mechanical repair. Record final contract pass/fail, lost feature behavior, test weakening, changed files, repair iterations, elapsed time, and model cost if available. Check video claims against recorded evidence and let a reviewer try to identify the cause using the video alone.

Before the presentation, aim for three consecutive successful fresh runs on the primary fixture, with a readable video and valid PR links. This is a rehearsal gate, not a statistical claim about general reliability. A future benchmark should evaluate more repositories and reserve cases that were not used for tuning.
