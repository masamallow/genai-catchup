# AGENTS.md — rules for AI agents in this repository

This repository is one person's public catch-up routine for generative AI:
curated feeds → research note → Marp report → GitHub Pages.
Read this file first, then [.claude/skills/genai-catchup-report/SKILL.md](./.claude/skills/genai-catchup-report/SKILL.md) for the run procedure.

## Non-negotiables

1. This repository is public.
   Never write non-public information: employer, clients, colleagues, internal projects, credentials, personal data.
   If a candidate would need such context to be useful, drop it.
2. No fabricated sources.
   Cite only URLs you fetched in this run, or whose content you confirmed in search results.
   Mark anything else as unverified, in the wording of that edition's templates, instead of guessing.
3. Languages.
   Repository docs, identifiers, file names, front-matter keys, code, comments and commit messages are English.
   Generated content (research notes and reports) is English by default and lives under `content/en/`.
   A run writes extra editions only when asked (`languages: en, ja`); see "Languages and editions" below.
4. Writing rules (checked by `mise run lint`).
   GitHub Flavored Markdown with semantic line breaks: one sentence per line, break right after `.` or `。`.
   A bullet with several sentences keeps the first sentence on the item line and nests the rest one level as flat bullets.
   A prose line that continues on the next prose line ends with two spaces.
5. Commit, do not push.
   Publishing to the site is a human decision (`mise run publish`).
6. During a routine run do not edit `sources.yaml`, `schedule.yaml`, `themes/`, `scripts/` or `templates/`.
   Put suggested changes in the completion summary instead.

## Scope

- In scope: generative AI and LLMs.
    - Track `genai-eng`: building with LLMs — models and their pricing or availability, agents, RAG, evals, LLMOps, serving platforms (Bedrock, Vertex AI, Foundry), protocols (MCP, A2A, Agent Skills), and new model classes that change how LLM applications are built.
    - Track `coding-ai`: AI coding tools and workflows — Claude Code, Codex, Cursor, Copilot, Gemini CLI, Kiro.
- Out of scope: non-generative machine learning, training hardware and infrastructure, consumer devices, general AI policy, and funding news.
  Such an item qualifies only when it changes what a GenAI engineer builds or how coding agents are used, and the note must say how.

## Where things go

| Path | Written by | Content |
| --- | --- | --- |
| `content/<lang>/research/YYYY-MM-DD.md` | agent | The dossier: one heading per topic in priority order, holding everything collected (one sub-heading per source with verbatim-level bullets), the topic's notes and its ideas for practice and output.<br/>Selected topics are thick, dropped ones thin |
| `content/<lang>/reports/YYYY-MM-DD.md` | agent | The synthesis: Marp slides picked from the dossier — one or two summary slides, then one slide per selected topic with key points, perspectives and debates, technical details, and a diagram when it earns its place.<br/>No practice guidance, no proposals |
| `templates/<lang>/` | human | Everything language-specific: the two skeletons and the site strings, see [templates/README.md](./templates/README.md) |
| `state/seen.json` | script | URLs already offered as candidates (180-day TTL) |
| `work/` | script | Per-run scratch, ignored by git |
| `sources.yaml` | human | Curated feeds. The agent proposes edits, the human applies them |
| `schedule.yaml` | human | The canonical schedule (cron): the Desktop scheduled task and the fetch window follow it |
| `dist/` | build | Generated site, one tree per language under `dist/<lang>/`, ignored by git, deployed by GitHub Actions |

## Languages and editions

- `content/en/` is the primary edition and is always written.
- Extra editions are written only when the request names them, for example `languages: en, ja` in the scheduled task's prompt.
  Each extra edition is a full research note and report under `content/<lang>/` with the same file name as the English one.
- Editions share the selection (topics, order, scores, anchor dates), the facts and numbers, the sources and the diagrams; they differ only in language.
- Write each edition from that language's templates as a native technical writer would.
  Do not translate the other edition sentence by sentence: restate the same facts in the idiom of the language.
  A quotation keeps the source's original wording when the source is in that language; otherwise it is paraphrased with numbers and names kept verbatim.
- Section names and labels come from `templates/<lang>/`; [templates/README.md](./templates/README.md) lines them up per language and explains how to add one.

## The two documents

The research note collects; the report picks and summarises.
Nothing is summarised in the note that the report will summarise again.

Research note (`templates/<lang>/research.md`):

- One `##` heading per topic, in priority order, numbered.
  The line under the heading carries the status (selected or dropped), the scores, the anchor date, the kind and the areas (vocabulary in [templates/README.md](./templates/README.md)).
- Under a selected topic: the feed items it gathers, then the collected-information section with one `####` sub-heading per source (`[A|B|C] Publisher — Title (date)` followed by the URL) and bullets that keep the source's numbers, names and wording.
  The bullets are exhaustive for the sources actually read; do not condense them into prose.
- Then the notes section for contradictions between sources, unverified claims and open questions, and the ideas section for what the reader might try or produce — inside the topic, never in a separate section at the end.
- Depth follows priority: a topic that will make the report gets every relevant source read and extracted; a dropped topic gets its feed items, its scores and a one-line reason.
- Dropped topics that came close get a heading each; the other dropped items go under two headings at the end, other one-off items and out of scope.

Report (`templates/<lang>/report.md`):

- One or two summary slides, then one slide per selected topic.
- Each summary card carries level tags for impact, potential and importance, one kind tag and one or two area tags, labelled as in [templates/README.md](./templates/README.md).
- Each topic slide synthesises three sections from the dossier: key points (what happened, with numbers; facts only, opinions belong in the next section), perspectives and debates (how the primary source frames it, independent perspectives, including ones written in the languages of the requested editions when they exist, constraints), technical details (identifiers, stack, platform or service, pricing or limits, specs).
- The report never contains practice guidance or proposals.
- A diagram belongs on a slide when it shows a mechanism, a flow, a topology or a comparison that bullets cannot show as clearly; a diagram that only decorates is left out.
  Write it as a ```` ```mermaid ```` fence (flowchart, sequence, state, class, ER or xychart), keep it to about 8 nodes laid out top to bottom (the column is narrow), and put it in the right column above the technical-details bullets.
  Diagram labels follow the edition's language.

## Topic rules

- A topic is one event or one piece of work, together with the coverage that continues it.
    - Events: a release, an announcement, an incident, a paper, a decision, or a new tool that practitioners have started to adopt.
    - Pieces of work: a technical write-up, such as a hands-on test, a benchmark or a technique, that the reader can learn from or reproduce.
    - A topic is described in one sentence, never as a bare keyword such as "MCP" or "agents".
- Two items belong to the same topic only when one could be folded into the other's write-up as an update, a supplement or a reaction without changing its headline.
  Items that merely share a keyword, a product or a vendor are separate topics, the way a news page lists them as related articles.
- Score and select each topic on its own; dropped topics are grouped only when they are written up.
- The window decides what the fetcher reads, not what may be selected.
    - It runs from the previous scheduled run to now; the fetcher derives it from [schedule.yaml](./schedule.yaml) and prints it.
    - It starts at local midnight of the scheduled day before the latest one on or before today, or of the newest note's date under `content/*/research/` when that is older because a scheduled run left no note: the previous run's day is fetched again in full, and seeing an item twice is better than missing it.
    - Items the previous run already offered are dropped by `state/seen.json`.
- A topic is eligible when no note of the last 30 days selected it.
    - Its anchor date is the date of the event or of the write-up, and the candidates-and-selection section records it for every selected topic.
    - An event from before the window is eligible when it first reaches the feeds in this run, often through news media or practitioners; the note marks its anchor as before the window and names the item that surfaced it.
    - A topic that an earlier note dropped may be selected when it comes back.
    - A topic that an earlier note selected is not selected again; only a new development on it makes a new topic, with the continuation section.
    - An event older than 30 days is background: it may appear in the key points labelled as background with its date, but it cannot anchor a topic.
- Score `impact`, `potential` and `importance`, each 0–2.
    - impact 2: it changes what many practitioners do this month.
      Evidence is any one of: a tier-1 primary source, coverage by two or more independent sources, or momentum (a practitioner-grade source reports sustained discussion, confirmed by one web search that finds two or more further independent write-ups).
    - impact 1: notable inside one ecosystem, or a single credible report without confirmed momentum.
    - impact 0: minor or incremental.
    - potential 2: a standard, protocol or platform-level change, a new model class, or a durable shift in practice.
    - potential 1: likely to matter for a quarter.
    - potential 0: incremental.
    - importance is judged for the reader: a tech lead in Japan who leads generative-AI engineering and is asked about AI coding tools.
      Every candidate is already in scope, so importance does not measure relevance; it asks what the reader would miss.
    - importance 2: missing it would leave the reader wrong-footed within weeks, because it calls for a decision or a change in how a team builds or runs LLM applications or coding agents (a migration, a settings change, a security check, a new look at a tool or model choice), or because a measurement, an incident or a working technique overturns an assumption with concrete evidence.
      Good to know is not enough, and a run rarely has more than a handful of topics at 2.
    - importance 1: useful context for later decisions, with nothing to change yet; most in-scope topics sit here.
    - importance 0: nothing changes for the reader, such as a minor version, availability in one more region or cloud without a new capability, a customer story or marketing.
- Vendor releases and practitioner momentum are both valid signals.
  A single item from a reliability-B practitioner source is never dropped without the momentum check above.
- Select the topics whose scores add up to 5 or more, or to 4 with importance 2, highest first and at most 8, and never pad.
    - Break ties by importance, then by primary-source presence, then by the number of independent sources.
    - A quiet window selects fewer topics, or none.
- Record the scored shortlist in the note's candidates-and-selection section: every selected topic with its anchor date and scores, and up to 5 notable dropped topics with their scores and a one-line reason, so the reader can overrule the selection next time.
- Every topic cites at least two sources including the primary one.
  For a technical write-up the write-up itself is the primary, and the second source can be the tool's own page, repository or paper.
  Reliability grades follow `sources.yaml`: A primary, B reputable independent analysis, C community or opinion, used only as supplement.

## Slide density

The frame is 1280x720 and nothing scrolls, so `mise run lint` enforces these limits (rule R3).

- Summary slides: one or two, each with at most 5 cards; a card has a title, one or two lines of takeaway, and tags.
    - Up to 4 topics: one slide with `<div class="grid">`.
    - 5 topics: one slide with `<div class="grid cols-3">` when the takeaways are short, otherwise two slides.
    - 6 to 8 topics: two slides of 3 or 4 cards with `<div class="grid">`; the second repeats the title without the lead line.
- Topic slide: each column holds at most 8 list items, and each item is at most about 68 em of display width (two lines; full-width characters count 1, others 0.55) after stripping link syntax.
    - Left column: key points (up to 5 items) and perspectives and debates (up to 3 items).
    - Right column: technical details (up to 6 items), or a diagram plus up to 3 items.
- The lede is one sentence and the sources line holds at most 4 links.
- When a slide overflows, cut words, not sections.
