# Agent instructions

> **Audience:** any AI coding agent working in this repository - Claude Code, Codex
> CLI, Cursor, or whatever comes next.
> **Read this top to bottom before doing anything.**

This file is the entry point. When you read this file, you are on Gregor's machine. More on that on 3. project context.

## 1. Gates

Gate 1: LESS IS MORE. Write nothing unnecessary. Before adding anything, ask:

* What real behaviour breaks without it?
* Is the scenario observed or invented?
* Does a mechanism already exist?

Never build a defence for an invented scenario; report it in one sentence instead.

Gate 2: FACTS ONLY. Never guess. State causes or mechanisms only after verifying them in code, dependency source, vendor docs, logs, or an actual request. Every factual claim must have a citation.

## 2. Before You Build

Ask first if the answer changes the work. If two interpretations materially change the code, ask one question at a time, with options and a recommendation.

First check whether the answer can be established yourself with the shell, repository, or available tools. Ask only about things the system cannot determine: user intent, preferences, or trade-offs.

Secrets

Never commit keys, tokens, passwords, or connection strings. Never put them in code, config, comments, or logs. If a secret touches version control, burn and replace it; history is permanent.

Verify Everything

Trust nothing until checked:

* Bug reporters describe what they saw, not necessarily why it happened.
* Other agents may overstate or mark inferred claims as verified.
* Your own earlier conclusions may be wrong after reading more files.
* Passing tests do not prove correctness.

Attack negative claims hardest: “not reachable”, “already covered”, and “cannot happen” require especially strong verification.

## 3. Project Context

Read PROJECT_COMPLETE_OVERVIEW.md for what the repository is and PROJECT-STATE.md for its current state.

**I am Gregor. My tasks are defined in:**

* docs/GREGOR-TARGET-LAB.md
* docs/TASK-GREGOR.md

Kwabena, Vlad, and Bogdan are the other contributors. Their task files may be read for context, but this agent works only on Gregor’s tasks.

**How to read those two files.** They define the work for the coming week. The
day-by-day tables in them (`TASK-GREGOR.md` §"Your week", `GREGOR-TARGET-LAB.md` §6)
are a **suggested order, not a schedule**. Several may land in one day and none on
another. Never treat a day number as a deadline, never report work as late or
behind against it, and never reorder or drop a deliverable just because its
suggested day has passed.

The **deliverables themselves are binding**; only their timing is not.

When the work departs from what those files specify — a different approach, a
changed deliverable, something skipped or added — record the deviation in
`GREGOR_WORKLOG.md` with the reason. Do not edit the task files to match.
They are updated only when the plan changes substantially, and that is Gregor's
call, not this agent's.

## 4. File Whitelist

You are allowed to change these files without asking for permission:

GREGOR_WORKLOG.md
AGENTS.md
calibration/**
lab/**

This list can be appendend. Work on other files can interfere with the work of others. Before editing other files think about potential consequences. 

## 5. Worklog

Only write work performed by this agent to **GREGOR_WORKLOG.md**.

Read GREGOR_WORKLOG.md at the start of every session. It must remain a complete, factual summary of everything done so far, so that reading it provides sufficient understanding of the previous work.

Do not write project work to other worklogs.