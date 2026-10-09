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
- Scratch: `work/pages/`, the page cache through which every agent of the run reads web pages (`mise run page`), and `work/sections/`, the topic sections the researchers write; `mise run fetch` empties both.
- Reader: an engineer in Japan who leads generative-AI engineering as a tech lead, follows the field to know what changed and what it means for their team's decisions, and is asked about AI coding tools.
  Headlines are not enough; each topic must carry technical substance.

## Agents

The agent that runs this skill orchestrates the run; subagents with fresh contexts, defined in `.claude/agents/`, do the reading and the long writing:

- `catchup-researcher` deepens a group of selected topics and writes each topic's section to `work/sections/<slug>.md` (step 4).
- `catchup-writer` writes one document from the files the run already wrote: the English report (step 6), or an extra edition's research note or report (step 7).

Hand subagents paths, not contents, and keep the documents out of your own context: never read a section, a note or a deck whole, and work from the subagents' final messages, `grep` and the lint output.  
When the runtime cannot start these subagents, do their work yourself in the same order, following their definitions, one group or one document at a time.

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
      The fetch also empties `work/pages/` and `work/sections/`.
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
    - Score impact, potential and attention (0–2 each) as defined in AGENTS.md, one topic at a time.
      A single item from a reliability-B practitioner source gets one WebSearch for further independent write-ups before it is scored.
    - Look up the engagement behind attention when the candidates do not show it, and keep the figures for the feed-item lines.
        - Hacker News points are in the item's summary.
        - Hatena Bookmark users: `curl -s 'https://bookmark.hatenaapis.com/count/entry?url=<url-encoded URL>'`.
        - Zenn likes: `liked_count` in `curl -s https://zenn.dev/api/articles/<slug>`.
    - Select as AGENTS.md says: every topic with a total of 4 or more, ranked by the total.
    - Record the count of candidates, the selected topics with their anchor dates and scores, and up to 5 notable dropped topics with scores and a one-line reason each.
4. Deepen the selected topics with researchers.
    - Prime the page cache with the feed-item URLs of the selected topics: `mise run page -- <url> ...`.
      For a URL it reports as `failed` or `thin`, read the page with the browser tools when they are available and save its text with the Write tool as `work/pages/<name>.md`, under the header the fetcher writes, with `method: browser`.
    - Group the topics so that each page is read by as few researchers as possible: topics announced at the same event or on the same page go to one researcher, or to two for a large event, and the other topics go one or two to a researcher.
    - Start one `catchup-researcher` per group, all in parallel.
      Give each the run date, the window, the edition languages, and for each of its topics: a slug for the file name, the one-sentence title, the kind and areas, the scores with a one-line reason each, the feed items, and the earlier topic it continues as `[topic N of YYYY-MM-DD](./YYYY-MM-DD.md#n-...)`, if any.  
      The definition holds the research method: primary source first, one to three independent perspectives, grades from `sources.yaml`, citations only of pages opened in this run.
    - Work from their final messages.
      Re-score a topic when a message gives a reason, and re-rank.  
      For a URL under "Needs the browser" that a topic depends on, read the page with the browser, save it to `work/pages/` as above and resume that researcher (SendMessage) to finish the topic.
    - Check every section without reading it: the file exists, and `grep -c '^#### \['` counts at least two sources.
5. Assemble the research note, English edition.
    - Copy `templates/en/research.md` to `content/en/research/<date>.md`.
    - Front matter: `date`, `run` (`scheduled` or `manual`), `generated_by`, `window`, `candidates`, `topics` (the selected ones: id, emoji, title, kind, areas, impact, potential, attention), `sources_used` (ids from `sources.yaml` that contributed a citation: those of the selected topics' feed items and those the researchers report).
    - `generated_by` names the agent and model that run this skill as the runtime names them, for example `Claude Opus 5.5` or `Codex GPT-6 Sol`; never guess it.
    - Candidates and selection: the scored index of every topic heading (selected first, then dropped), each with anchor date and scores.
    - One `##` heading per topic in priority order.
    - Selected topics: write the heading, the status line and the feed items with their engagement figures, then append the topic's section after a blank line: `cat work/sections/<slug>.md >> content/en/research/<date>.md`.
      The section holds the rest of the topic: the continuation section when it continues an earlier one, the collected-information section with one `####` per source read and short bullets of what it adds, the notes section and the ideas section.
    - Dropped topics: feed items, scores and a one-line reason only, grouped as AGENTS.md describes; write them yourself.
    - Do not write the report's sections (key points, perspectives and debates, technical details) in the note; that synthesis happens in the report.
    - When a topic directly continues one from an earlier note, its continuation section links `[topic N of YYYY-MM-DD](./YYYY-MM-DD.md#n-...)` and says what changed since.
    - `uv run scripts/lint_md.py content/en/research/<date>.md` must report 0 problems; fix a problem at the line it names (`sed -n`) without reading the rest.
6. Write the report (the synthesis), English edition.
    - Start a `catchup-writer` for the English report, with the run date and the path of the note, once the note passes lint.
      It reads the note and the rest itself, and writes the deck by the rules below.
    - Copy `templates/en/report.md` to `content/en/reports/<date>.md`.
    - The front matter's `footer` is `GenAI Catch-up Report · <date> · 🤖 Generated by <generated_by>`, with the same `generated_by` as the note.
    - The deck opens with summary slides of class `summary`: the date, a lead line linking to `../research/<date>.md` on the first, and one card per selected topic in rank order, laid out as "Slide density" in AGENTS.md says.
      Level tags use the class `high` for 2, `mid` for 1 and `low` for 0.
    - Decide which topics get a slide of their own as AGENTS.md says: by whether the material fills the three sections, not by the score.
    - One slide per such topic with class `topic`: title with the rank emoji, a one-line lede, left column key points and perspectives and debates, right column technical details (with a Mermaid diagram above it when the mechanism, flow, topology or comparison is clearer drawn), and a `<p class="sources">` line.
    - The other topics go last, on slides of class `others` titled with the edition's label for Other topics: 2 to 4 cards per slide in rank order, each with the rank emoji and title, the facts and technical details as list items, and a `<p class="sources">` line.
    - The report never contains practice guidance or proposals.
    - Continuity links point at the earlier deck as `./YYYY-MM-DD.md#N` where N is the slide number; the build rewrites `.md` to `.html`.
    - Respect the density limits in AGENTS.md.
    - The writer's final message lists the slides; keep it for the completion message.
7. Write the extra editions.
    - For each extra language, start a `catchup-writer` for that edition's research note once the English note passes lint, alongside the English report's writer, and another for that edition's report once the English report and that edition's note exist.
    - Copy `templates/<lang>/research.md` and `templates/<lang>/report.md` to `content/<lang>/research/<date>.md` and `content/<lang>/reports/<date>.md`.
    - Keep the front matter values, the topic order, the scores, the anchor dates, the source sub-headings, the URLs and the diagrams identical to the English edition; translate only the topic titles and the diagram labels.
    - Write the prose in that language from the sources, not from the English sentences: quotes from sources in that language keep their original wording, taken from their saved text in `work/pages/`, and everything else is restated in the idiom of that language with numbers and names verbatim.
    - The edition must pass the same lint and density rules.
8. Check.
    - `mise run lint` must report 0 problems; fix the Markdown, not the linter.
      Fix a problem at the line it names, or resume the writer of that file (SendMessage) when the fix needs its context.
    - `mise run build` must exit 0.
      The lint's R3 rule keeps the slides inside the frame; if it complains, cut words rather than sections.
9. Mark candidates as seen: `mise run mark-seen`.
10. Commit and stop.
    - `git add content state && git commit -m "docs(content): add <date> catch-up"`.
    - Do not push.
11. Print the completion message: the selected topics with their impact, potential and attention scores and whether each has a slide of its own or sits on an Other topics slide, the dropped topics, the file paths per language, failed sources, and any suggested change to `sources.yaml` (new source found during research, or a source that produced only noise).

## Failure handling

- A source that failed to fetch is listed in the note header and otherwise ignored.
- If a primary source cannot be read through the page cache, WebFetch or the browser, cite the search result and mark the facts unverified.
- If a subagent stops before its files are complete, resume it once (SendMessage); if it stops again, do its work yourself following its definition.
- If the run happens late (the machine was asleep), still use the actual current date; the window already reaches back to the previous run, so do not pass `--days`.
- Never pad: when few topics reach the threshold, report only those, and when none does, write the research notes without reports (the site lists them without slides).
