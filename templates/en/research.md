---
title: "GenAI catch-up research note YYYY-MM-DD"
date: YYYY-MM-DD
run: scheduled            # scheduled | manual
generated_by: "<agent> <model>"   # as the runtime names them, e.g. Claude Opus 5.5 or Codex GPT-6 Sol
window: "YYYY-MM-DD..YYYY-MM-DD"
candidates: 0             # number of items in work/candidates.md
topics:                   # selected topics only, in rank order
  - id: 1
    emoji: "🧭"
    title: "Topic 1 heading (one event or one piece of work, in one sentence)"
    kind: release         # release | change | incident | research | hands-on | analysis
    areas: [models, api-cloud]   # 1 or 2 of: models, api-cloud, coding-agents, agent-dev, security, evals-ops
    impact: 2             # 0-2, see AGENTS.md
    potential: 2          # 0-2
    importance: 2         # 0-2, for the reader
sources_used: [claude-code-changelog]   # ids from sources.yaml that contributed a citation
---

# GenAI catch-up research note YYYY-MM-DD

- Window: YYYY-MM-DD to YYYY-MM-DD (since the previous run, N candidates).
- Sources that failed to fetch: none.

## Candidates and selection

- Selected (go into the report):
    1. Topic 1 heading (anchor MM-DD, impact 2 / potential 2 / importance 2).
    2. Topic 2 heading (anchor MM-DD, before the window, surfaced by `source-id`, 1 / 2 / 2).
- Dropped (input for the next run's judgement):
    3. Topic 3 heading (anchor MM-DD, 1 / 2 / 1) — reason in one sentence.
    4. Topic 4 heading (anchor MM-DD, 2 / 1 / 0) — reason in one sentence.
    5. Other one-off items — listed below.
    6. Out of scope — listed below.

## 1. 🧭 Topic 1 heading

- Selected / impact 2 / potential 2 / importance 2 / anchor MM-DD / kind: release / areas: models, API and cloud.
- Feed items in this topic:
    - `source-id` MM-DD [item title](URL)
    - `source-id` MM-DD [item title](URL)

### Collected information

#### [A] Publisher — Title (YYYY-MM-DD)

<URL>

- Facts from the primary source, keeping its numbers, names and wording.
- One fact per bullet; do not condense.

#### [B] Publisher — Title (YYYY-MM-DD)

<URL>

- Claims of the independent analysis, and where they differ from the primary source.

#### [C] Publisher — Title (YYYY-MM-DD)

<URL>

- Community reaction (supplementary).

### Notes

- Contradictions between sources, unverified claims, questions to carry into the next run.

### Ideas for practice and output

- What to try, at what scale, and what it would verify.

## 3. 🧪 Dropped topic heading

- Dropped / impact 1 / potential 2 / importance 1 / anchor MM-DD / kind: hands-on / areas: coding agents.
- Feed items in this topic:
    - `source-id` MM-DD [item title](URL)
- Reason for dropping it: one sentence.

## 5. 📎 Other one-off items

- Dropped / each scored on its own, none close to the threshold.
- `source-id` MM-DD the item in a few words.

## 6. 🚫 Out of scope

- `source-id` MM-DD the item in a few words.
