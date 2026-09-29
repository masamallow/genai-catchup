---
name: genai-catchup-report
description: Run one cycle of the GenAI catch-up routine - fetch the curated feeds, sort the new items into concrete topics (events and technical write-ups), score and select them, deepen each selected topic with several sources, write the research note and the Marp deck under content/<lang>/ (English always, extra editions on request), lint, build, mark candidates as seen and commit. Use when asked to run the catch-up, make today's GenAI report, or when started by the scheduled task.
argument-hint: "[languages: en, ja]"
---

# GenAI catch-up report

One run turns the last few days of curated feeds into a research note and a slide report.
Follow [AGENTS.md](../../../AGENTS.md) for scope, languages, citations, section contents and density; this file is the procedure.

## Inputs and outputs

- Input: `work/candidates.md` produced by `mise run fetch`, plus web research on the selected topics.
- Output: `content/en/research/<date>.md` (source of truth, template `templates/en/research.md`) and `content/en/reports/<date>.md` (Marp, template `templates/en/report.md`).
- Languages: English is always written.
  When the request names extra languages (`languages: en, ja`), the same two files are also written under `content/<lang>/` from `templates/<lang>/`, following "Languages and editions" in AGENTS.md.
- Reader: an engineer in Japan who leads generative-AI engineering as a tech lead, keeps up with the field to improve their own and their team's practice, and is asked about AI coding tools.
  Headlines are not enough; each topic must carry technical substance.

## Procedure

1. Establish the run date and the languages.
    - `date +%F` gives `<date>`.
      If `content/en/research/<date>.md` already exists, use `<date>-2` for every file of this run.
    - Languages: `en`, plus any named in the request.
      Each one needs `templates/<lang>/research.md` and `templates/<lang>/report.md`; if one is missing, stop and report.
    - `git status --short` must be clean apart from `work/`; if not, stop and report.
2. Fetch candidates.
    - Run `mise run fetch`.
      The window starts at the previous scheduled run from `schedule.yaml`, or at the newest note under `content/*/research/` when that is older, and the header of `work/candidates.md` states it; use `--since` or `--days` only when asked to.
    - Read `work/candidates.md` in full.
      Note the window and the failed sources for the note's header.
    - If there are no new items, print `no candidates` and stop without writing files.
3. Sort into topics, score and select.
    - Drop items outside the scope in AGENTS.md.
    - Sort the items into topics as AGENTS.md defines them: one event or one piece of work with the coverage that continues it.
      A shared keyword, product or vendor does not make two items one topic.
    - Name each topic in one concrete sentence.
    - Check eligibility against `topics` in the front matter of the notes of the last 30 days.
      A topic selected there returns only as a new development, with the continuation section of step 5.
    - An event from before the window is eligible when this run is the first to see it; note the item that surfaced it.
    - Score impact, potential and importance (0–2 each) as defined in AGENTS.md, one topic at a time.
      A single item from a reliability-B practitioner source gets one WebSearch to check momentum before it is scored.
    - Select as AGENTS.md says: every topic with a total of 4 or more, unless its importance is 0, ranked by the total.
    - Record the count of candidates, the selected topics with their anchor dates and scores, and up to 5 notable dropped topics with scores and a one-line reason each.
4. Deepen each selected topic with the web.
    - Fetch the primary source with WebFetch; this is mandatory.
      If WebFetch is refused (403), try the page through the browser tools when they are available, otherwise cite the search result and mark the facts unverified.
    - For a technical write-up the write-up is the primary; add the tool's own page, repository or paper.
    - Use WebSearch to find 1 to 3 independent perspectives: an analysis by a known practitioner or established tech media (B), a perspective in the language of each requested edition when one exists, and community reaction (C) only as supplement.
      Prefer sources already in `sources.yaml`; add others when they are clearly reputable.
    - Extract the technical details: identifiers, stack, platform or service, pricing or limits when stated, specs or protocols.
    - Note what the reader could try or produce; it goes into the note's ideas section, never into the report.
    - Record every URL you actually opened; you will cite only those.
5. Write the research note (the dossier), English edition.
    - Copy `templates/en/research.md` to `content/en/research/<date>.md`.
    - Front matter: `date`, `run` (`scheduled` or `manual`), `generated_by`, `window`, `candidates`, `topics` (the selected ones: id, emoji, title, kind, areas, impact, potential, importance), `sources_used` (ids from `sources.yaml` that contributed a citation).
    - `generated_by` names the agent and model that run this skill as the runtime names them, for example `Claude Opus 5.5` or `Codex GPT-6 Sol`; never guess it.
    - Candidates and selection: the scored index of every topic heading (selected first, then dropped), each with anchor date and scores.
    - One `##` heading per topic in priority order.
    - Selected topics: the feed items the topic gathers, then the collected-information section with one `####` per source read and exhaustive bullets (numbers, names, wording kept), then the notes section (contradictions, unverified claims, open questions) and the ideas section.
    - Dropped topics: feed items, scores and a one-line reason only, grouped as AGENTS.md describes.
    - Do not write the report's sections (key points, perspectives and debates, technical details) in the note; that synthesis happens in the report.
    - When a topic directly continues one from an earlier note, add the continuation section linking `[topic N of YYYY-MM-DD](./YYYY-MM-DD.md#n-...)` and say what changed since.
6. Write the report (the synthesis), English edition.
    - Copy `templates/en/report.md` to `content/en/reports/<date>.md`.
    - The front matter's `footer` is `GenAI Catch-up Report · <date> · 🤖 Generated by <generated_by>`, with the same `generated_by` as the note.
    - The deck opens with summary slides of class `summary`: the date, a lead line linking to `../research/<date>.md` on the first, and one card per selected topic in rank order, laid out as "Slide density" in AGENTS.md says.
      Level tags use the class `high` for 2, `mid` for 1 and `low` for 0.
    - Decide which topics get a slide of their own as AGENTS.md says: every topic with 5 points or more, and a topic with 4 points when its material fills the three sections.
    - One slide per such topic with class `topic`: title with the rank emoji, a one-line lede, left column key points and perspectives and debates, right column technical details (with a Mermaid diagram above it when the mechanism, flow, topology or comparison is clearer drawn), and a `<p class="sources">` line.
    - The other topics go last, on slides of class `others` titled with the edition's label for Other topics: 2 to 4 cards per slide in rank order, each with the rank emoji and title, the facts and technical details as list items, and a `<p class="sources">` line.
    - The report never contains practice guidance or proposals.
    - Continuity links point at the earlier deck as `./YYYY-MM-DD.md#N` where N is the slide number; the build rewrites `.md` to `.html`.
    - Respect the density limits in AGENTS.md.
7. Write the extra editions, one language at a time.
    - Copy `templates/<lang>/research.md` and `templates/<lang>/report.md` to `content/<lang>/research/<date>.md` and `content/<lang>/reports/<date>.md`.
    - Keep the front matter values, the topic order, the scores, the anchor dates, the source sub-headings, the URLs and the diagrams identical to the English edition; translate only the topic titles and the diagram labels.
    - Write the prose in that language from the sources, not from the English sentences: quotes from sources in that language keep their original wording, everything else is restated in the idiom of that language with numbers and names verbatim.
    - The edition must pass the same lint and density rules.
8. Check.
    - `mise run lint` must report 0 problems; fix the Markdown, not the linter.
    - `mise run build` must exit 0.
      The lint's R3 rule keeps the slides inside the frame; if it complains, cut words rather than sections.
9. Mark candidates as seen: `mise run mark-seen`.
10. Commit and stop.
    - `git add content state && git commit -m "docs(content): add <date> catch-up"`.
    - Do not push.
11. Print the completion message: the selected topics with their impact, potential and importance scores and whether each has a slide of its own or sits on an Other topics slide, the dropped topics, the file paths per language, failed sources, and any suggested change to `sources.yaml` (new source found during research, or a source that produced only noise).

## Failure handling

- A source that failed to fetch is listed in the note header and otherwise ignored.
- If WebFetch fails on a primary source, try once more; if it still fails, cite the search result and mark the facts unverified.
- If the run happens late (the machine was asleep), still use the actual current date; the window already reaches back to the previous run, so do not pass `--days`.
- Never pad: when few topics reach the threshold, report only those, and when none does, write the research notes without reports (the site lists them without slides).
