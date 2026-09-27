---
name: genai-catchup-report
description: Run one cycle of the GenAI catch-up routine - fetch the curated feeds, cluster the new items into concrete news themes, deepen each theme with several sources, write the research note and the Marp deck under content/<lang>/ (English always, extra editions on request), lint, build, mark candidates as seen and commit. Use when asked to run the catch-up, make today's GenAI report, or when started by the scheduled task.
argument-hint: "[languages: en, ja]"
---

# GenAI catch-up report

One run turns the last few days of curated feeds into a research note and a slide report.
Follow [AGENTS.md](../../../AGENTS.md) for scope, languages, citations, section contents and density; this file is the procedure.

## Inputs and outputs

- Input: `work/candidates.md` produced by `mise run fetch`, plus web research on the selected themes.
- Output: `content/en/research/<date>.md` (source of truth, template `templates/en/research.md`) and `content/en/reports/<date>.md` (Marp, template `templates/en/report.md`).
- Languages: English is always written.
  When the request names extra languages (`languages: en, ja`), the same two files are also written under `content/<lang>/` from `templates/<lang>/`, following "Languages and editions" in AGENTS.md.
- Reader: an engineering manager and tech lead in Japan who leads generative-AI engineering and is asked about AI coding tools.
  Headlines are not enough; each theme must carry technical substance.

## Procedure

1. Establish the run date and the languages.
    - `date +%F` gives `<date>`.
      If `content/en/research/<date>.md` already exists, use `<date>-2` for every file of this run.
    - Languages: `en`, plus any named in the request.
      Each one needs `templates/<lang>/research.md` and `templates/<lang>/report.md`; if one is missing, stop and report.
    - `git status --short` must be clean apart from `work/`; if not, stop and report.
2. Fetch candidates.
    - Run `mise run fetch`.
      The window starts at the date of the newest note under `content/*/research/` (the previous run) and the header of `work/candidates.md` states it; use `--since` or `--days` only when asked to.
    - Read `work/candidates.md` in full.
      Note the window and the failed sources for the note's header.
    - If there are no new items, print `no candidates` and stop without writing files.
3. Cluster and rank.
    - Drop items outside the scope in AGENTS.md.
    - Group items that describe the same event into one theme.
      Name each theme as one concrete sentence, and check that the anchoring event happened inside the window; an in-window recap of an older event only qualifies if the in-window development stands on its own.
    - Score impact and potential (0–2 each) as defined in AGENTS.md.
      A single item from a reliability-B practitioner source gets one WebSearch to check momentum before it is scored.
    - Sort by the sum, then by primary-source presence, then by the number of independent sources.
      Keep 3 to 5 themes.
    - Record the count of candidates, the selected themes with their anchor dates and scores, and up to 5 notable dropped candidates with scores and a one-line reason each.
4. Deepen each theme with the web.
    - Fetch the primary source with WebFetch; this is mandatory.
      If WebFetch is refused (403), try the page through the browser tools when they are available, otherwise cite the search result and mark the facts unverified.
    - Use WebSearch to find 1 to 3 independent perspectives: an analysis by a known practitioner or established tech media (B), a perspective in the language of each requested edition when one exists, and community reaction (C) only as supplement.
      Prefer sources already in `sources.yaml`; add others when they are clearly reputable.
    - Extract the technical details: identifiers, stack, platform or service, pricing or limits when stated, specs or protocols.
    - Note what the reader could try or produce; it goes into the note's ideas section, never into the report.
    - Record every URL you actually opened; you will cite only those.
5. Write the research note (the dossier), English edition.
    - Copy `templates/en/research.md` to `content/en/research/<date>.md`.
    - Front matter: `date`, `run` (`scheduled` or `manual`), `window`, `candidates`, `themes` (the selected ones: id, emoji, title, track, impact, potential), `sources_used` (ids from `sources.yaml` that contributed a citation).
    - Candidates and selection: the scored index of every theme heading (selected first, then dropped), each with anchor date and scores.
    - One `##` heading per clustered theme in priority order.
      Selected themes: the feed items that formed the cluster, then the collected-information section with one `####` per source read and exhaustive bullets (numbers, names, wording kept), then the notes section (contradictions, unverified claims, open questions) and the ideas section.
      Dropped themes: feed items, scores and a one-line reason only.
    - Do not write the report's sections (key points, perspectives and debates, technical details) in the note; that synthesis happens in the report.
    - When a theme directly continues one from an earlier note, add the continuation section linking `[theme N of YYYY-MM-DD](./YYYY-MM-DD.md#n-...)` and say what changed since.
6. Write the report (the synthesis), English edition.
    - Copy `templates/en/report.md` to `content/en/reports/<date>.md`.
    - Slide 1 has class `summary`: the date, a lead line linking to `../research/<date>.md`, and one card per selected theme in rank order.
      Use `<div class="grid">` for 3 or 4 themes and `<div class="grid cols-3">` for 5.
    - One slide per theme with class `theme`: title with the rank emoji, a one-line lede, left column key points and perspectives and debates, right column technical details (with a Mermaid diagram above it when the mechanism, flow, topology or comparison is clearer drawn), and a `<p class="sources">` line.
    - The report never contains practice guidance or proposals.
    - Continuity links point at the earlier deck as `./YYYY-MM-DD.md#N` where N is the slide number; the build rewrites `.md` to `.html`.
    - Respect the density limits in AGENTS.md.
7. Write the extra editions, one language at a time.
    - Copy `templates/<lang>/research.md` and `templates/<lang>/report.md` to `content/<lang>/research/<date>.md` and `content/<lang>/reports/<date>.md`.
    - Keep the front matter values, the theme order, the scores, the anchor dates, the source sub-headings, the URLs and the diagrams identical to the English edition; translate only the diagram labels.
    - Write the prose in that language from the sources, not from the English sentences: quotes from sources in that language keep their original wording, everything else is restated in the idiom of that language with numbers and names verbatim.
    - The edition must pass the same lint and density rules.
8. Check.
    - `mise run lint` must report 0 problems; fix the Markdown, not the linter.
    - `mise run build` must exit 0.
      The lint's R3 rule keeps theme slides inside the frame; if it complains, cut words rather than sections.
9. Mark candidates as seen: `mise run mark-seen`.
10. Commit and stop.
    - `git add content state && git commit -m "docs(content): add <date> catch-up"`.
    - Do not push.
11. Print the completion message: the selected themes with their impact and potential scores, the dropped candidates, the file paths per language, failed sources, and any suggested change to `sources.yaml` (new source found during research, or a source that produced only noise).

## Failure handling

- A source that failed to fetch is listed in the note header and otherwise ignored.
- If WebFetch fails on a primary source, try once more; if it still fails, cite the search result and mark the facts unverified.
- If the run happens as a late catch-up (the machine was asleep), still use the actual current date and widen `--days` to cover the gap.
- If fewer than 3 themes have real substance, write the report with the themes that do; never pad with weak items.
