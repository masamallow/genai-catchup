# Source notes

What a naive feed list gets wrong as of 2026-09-18, and how to review sources.

## No machine-readable feed

- Anthropic News, Engineering and claude.com (`/resources/articles`, where claude.com/blog redirects) have no official feed.
  `sources.yaml` uses community-generated feeds (Olshansk/rss-feeds); verify on anthropic.com or claude.com before citing.
- claude.dev, the Claude Code team's blog, has an official feed at `https://claude.dev/rss.xml` (`claude-dev-blog`, found 2026-10-27).
- OpenAI API changelog: fetch `https://developers.openai.com/api/docs/changelog.md` and diff.
- Gemini API changelog: fetch `https://ai.google.dev/gemini-api/docs/changelog.md.txt` and diff.
- Thoughtworks Technology Radar: e-mail only; the insights feed is the whole blog (3 MB).
- Benchmarks (SWE-bench, SWE-bench Pro, Terminal-Bench, Arena, Artificial Analysis, OpenRouter): no feeds, monthly manual look.
  METR has `https://metr.org/feed.xml`.
    - Artificial Analysis still had no feed on 2026-10-27; its measurements are cited through web search, as five runs of October 2026 did.
- The Batch and Every: e-mail only.

## Moved or renamed

- Codex changelog moved to `https://learn.chatgpt.com/docs/changelog` (RSS at `/rss.xml`).
- OpenAI platform changelog moved to `https://developers.openai.com/api/docs/changelog`.
- LangChain blog feed moved to `https://www.langchain.com/blog/rss.xml`; LangSmith changelog lives under docs.langchain.com.
- Windsurf became Devin Desktop; changelog at `https://docs.devin.ai/desktop/changelog/rss.xml`.
- Azure AI Foundry became Microsoft Foundry; blog feed `https://devblogs.microsoft.com/foundry/feed/`.
- lmarena.ai became arena.ai; WebDev board at `/leaderboard/code/webdev`.
- Google Cloud release-note feeds: `vertex-ai-release-notes.xml` stopped 2026-03, `generative-ai-on-vertex-ai-release-notes.xml` stopped 2026-05.
  Use the product-group feeds listed in `sources.yaml`.
- Renamed repositories: strands-agents/sdk-python → harness-sdk, sst/opencode → anomalyco/opencode, openai/agents.md → agentsmd/agents.md.

## Stopped or stale

- Aider polyglot leaderboard: last update 2025-11.
- news.smol.ai RSS lags; AINews now lives in the Latent Space section feed.
- Weekly AI Agents News (SpeakerDeck): stopped 2025-03; successor is the `masamasa59/ai-agent-papers` repository.
- Chip Huyen's blog: last post 2025-01.

## Not added

- Unite.AI and hyper.ai rewrite the primary source with AI, as three runs (Unite.AI) and one run (hyper.ai) of October 2026 found; cite the primary instead.
- GIGAZINE posts about 45 items a day and its feed holds 30, under a day, so a 2–3 day window cannot be fetched.
    - Its articles reach the runs through Hatena Bookmark.

## Momentum coverage

- Practitioner momentum (a tool everyone starts trying) shows up first on X, Zenn and Hacker News, not in vendor feeds.
  A first draft of the sample missed TypeSafe's Jev (launched 2026-09-15) for that reason: with a 4-day window the only feed item was one laiso post, hnrss was down, and X has no feed.
- Mitigations in place: the aggregators `zenn-trending`, `hatena-llm` and `hn-llm` (reliability C), the LangChain blog enabled, and the momentum check in [AGENTS.md](../AGENTS.md) before a single-source item is dropped.
    - The aggregators also bring practitioner write-ups that can become topics of their own, so a filter that drops an in-scope post loses a topic, not just evidence (see [Keyword filters](#keyword-filters)).
- Still uncovered: X itself.
  AINews summarises X daily, and the momentum check (one WebSearch) is the fallback.

## Keyword filters

- `filter.any` and `filter.category` in [sources.yaml](../sources.yaml) keep a feed to the scope in [AGENTS.md](../AGENTS.md); they do not find what is new.
    - What is new and popular comes from the aggregators' own ranking (Zenn trending, Hatena Bookmark 30 users+, Hacker News 100 points+) and from the momentum check.
- How a feed is narrowed depends on whether category terms or the vendor's own product names can describe what it should keep.

| Feed | Narrowed by | Sources |
| --- | --- | --- |
| Category terms or the vendor's own product names describe what to keep | `filter.any` | `aws-whats-new`, `aws-jp-weekly-genai`, `google-developers-blog`, `publickey` |
| The feed tags its items with categories, and the noise is untagged or tagged apart | `filter.category` | `openai-news` |
| The site offers a search feed or API | A category term in the query (`LLM`) | `hatena-llm`, `hn-llm` |
| Posts name tools and techniques rather than categories, and the feed is small | Nothing; the run drops what is out of scope ([SKILL.md](../.claude/skills/genai-catchup-report/SKILL.md) step 3) | `zenn-trending` (20 items) |

- Keywords are category terms or long-lived names: platforms and tools the scope names, major model vendors and their models, or a vendor's own products in its own feed.
    - Adding a vendor's new product to that vendor's feed is upkeep of a closed list.
- Never add a product to catch one missed item.
    - A list of names cannot know the next new one, and routine runs do not edit `sources.yaml`, so an added name outlives its topic.
    - Fix the class of the miss instead: a category term that did not match, a missing source, or a feed that should not be filtered.
- Keywords match as case-insensitive substrings of the title and the summary, so a short keyword such as `AI` also matches `available` or `email`.
    - On an AI-only feed a bare `AI` keeps everything (ITmedia AI+: 19 of 20), so the Japanese media feeds share a list of scope terms instead (`&ja-media-scope`).
- `openai-news` cannot be narrowed by `filter.any`, since its customer stories use the same words as its announcements.
    - The feed tags announcements with a category (Product, Engineering, Research, Publication, Security, Safety, Company) and leaves customer stories untagged or tagged Startup, so `filter.category` keeps the announcements.

## Operational caveats

- Large feeds: learn.chatgpt.com changelog (about 1 MB), Latent Space (about 0.9 MB), gihyo.jp (about 0.5 MB, a year of entries).
- The Hacker News sources are searches on the HN Search API (`hn.algolia.com`, `search_by_date` with `tags=story` and `numericFilters=points>=100`), which the fetcher narrows to the window.
    - `hnrss.org`, a wrapper of the same API, answered 502 or timed out in 8 of the 12 scheduled runs of October 2026 and is no longer used.
    - Each search sets `typoTolerance=false`, since the index applies typo tolerance to three-letter words: `MCP` matched Map and MPs, and `LLM` matched unrelated URLs.
- The fetcher tries every request once more after 10 seconds when it times out or gets a 429 or 5xx, the way GitHub `releases.atom` feeds answer 504 at times.
    - A source that fails twice is listed under Failed sources in `work/candidates.md` and fetched again on the next run.
- `https://github.com/anthropics/claude-code/releases.atom` answered 504 twice on 2026-09-18; the official changelog RSS is enough.
- Zenn topic feeds return the newest 20 items with no popularity signal; keep them disabled unless a downstream popularity filter exists.

## Monthly review

1. `mise run stats` — sources that are enabled but never cited are demotion candidates.
2. Sources that keep appearing in web research but are not listed are promotion candidates; add them with a tier and reliability grade.
3. Re-check one tier-3 source per month by enabling it for a single run (`uv run scripts/fetch_feeds.py fetch --source <id>`).
4. Record what changed in the commit message; `sources.yaml` history is the log.
