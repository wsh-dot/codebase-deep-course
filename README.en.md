# Codebase Deep Course Skill

`codebase-deep-course` helps an AI coding agent turn a real repository into a detailed Chinese course that a reader can use to understand, run, and troubleshoot the system. It grew out of a WeKnora course, but its nine chapter outline, Neo4j, and dual vector stores are examples, not defaults for other repositories.

Install only the [codebase-deep-course/](codebase-deep-course/) folder. The README files at the repository root are GitHub documentation and are not part of the installed skill.

## When to use it

- Learn an unfamiliar codebase from end to end by tracing user actions, entry points, and data flow.
- Deepen an existing tutorial while preserving useful prose and stable section anchors.
- Produce a self contained offline HTML course when requested, with navigation and reading controls that are checked in a browser.
- Build runnable teaching labs, including independent implementations in two languages when requested.

A course should let the reader explain the mechanism, run a minimal path, find where evidence was lost, and interpret what an experiment actually proves. This repository contains the skill and validation tools, not WeKnora source code or a ready made course.

## How it works

1. Record the learner, outcomes, repository commit, working tree changes, environment, and required components.
2. Trace a real route, CLI command, or job from entry point to storage and external services, including branches and failures.
3. Organize chapters by learning dependencies and follow one stable example across boundaries.
4. Explain each key mechanism through cause, data changes, source evidence, an action, expected output, failure diagnosis, and a transfer exercise.
5. Label source facts, teaching simplifications, simulations, and proposed extensions separately from test status.
6. Check teaching quality, source provenance, lab behavior, and the reading interface before delivery.

See [SKILL.md](codebase-deep-course/SKILL.md) for the workflow and its on demand references.

## Installation

### Install from the GitHub subdirectory

If your AI IDE can install a skill from a GitHub subdirectory, use:

```text
https://github.com/wsh-dot/codebase-deep-course/tree/main/codebase-deep-course
```

The installed skill root must directly contain `SKILL.md`, `references/`, `scripts/`, `assets/`, and `agents/`. Point an automatic installer at the subdirectory, since the repository root contains publication documentation.

### Manual Codex installation

Clone the repository:

```text
git clone https://github.com/wsh-dot/codebase-deep-course.git
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills" | Out-Null
Copy-Item -Recurse -Force ".\codebase-deep-course\codebase-deep-course" "$env:USERPROFILE\.codex\skills"
```

macOS / Linux:

```bash
mkdir -p ~/.codex/skills
cp -R ./codebase-deep-course/codebase-deep-course ~/.codex/skills/
```

For another AI IDE, copy the whole skill subdirectory to that IDE's documented skills location.

## Example prompts

Create a course:

```text
Use $codebase-deep-course to create a detailed Chinese course for the current repository.
The reader can program but does not know this system. They should finish able to explain the full execution path, run it, and troubleshoot it.
Follow one example through actual data and source code. Include runnable labs, expected results, failure diagnosis, and exercises.
Deliver Markdown. I will explicitly request offline HTML if needed.
```

Deepen a course:

```text
Use $codebase-deep-course to deepen this existing course. Preserve useful prose and stable anchors. First identify the missing causal explanations, data transitions, source connections, and lab interpretations; then fill those gaps and update navigation and validation.
```

If source code is inaccessible, the agent should say that the source has not been verified and request it or offer a clearly labeled conceptual tutorial. It should not invent functions, line numbers, or test results.

## Source evidence and validation

The evidence tools require Python 3.9+; extracting from a fixed commit also requires Git. The scripts use only the Python standard library. Replace the sample paths and marker below with real values from the target repository.

Extract a contiguous source excerpt from a fixed commit and generate an HTML snippet:

```text
python codebase-deep-course/scripts/extract_source.py --repo <target-repo> --path src/example.py --revision <full-commit> --start-marker "def build_context(" --lines 12 --output evidence/context.json --html-output evidence/context.html
```

The start marker must match exactly once. Use `--end-marker` instead of `--lines` when that makes the range clearer. For uncommitted teaching code, explicitly use `--worktree`; the output records working tree provenance rather than claiming a fixed commit.

Audit a course HTML file:

```text
python codebase-deep-course/scripts/audit_course.py <course.html> --repo <target-repo> --offline --require-revision --output evidence/audit.json
```

A source based course fails the audit when it has no excerpts. `--allow-no-source` is only for an explicitly scoped conceptual tutorial, and the delivery should still report that source was not verified. The static audit cannot prove that explanations are correct, browser interactions work, or live services ran; use the [acceptance guide](codebase-deep-course/references/acceptance.md) for those checks.

## Tests and packaging

Run from the repository root:

```text
python -m unittest discover -s codebase-deep-course/scripts -p "test_*.py" -v
python codebase-deep-course/scripts/package_skill.py codebase-deep-course dist/codebase-deep-course.zip
```

All 14 unit tests in this publication passed. The packager rejects non UTF-8 text, verifies ZIP byte roundtrips, and excludes cache directories. These tests cover tool behavior; they are not an independent model evaluation of course quality on arbitrary repositories.

## Boundaries

- Choose chapters and technology from the target source and user requirements; the WeKnora route is only an example.
- Simulated inputs and fixed outputs demonstrate the teaching implementation, not real model or database quality.
- When Docker, models, or an observability platform are unavailable, finish the documentation and available labs while listing what remains untested.
- Check generated offline HTML with networking disabled, at desktop and narrow widths, with keyboard navigation, and in print mode.
