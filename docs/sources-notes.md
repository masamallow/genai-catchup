# Source notes

What a naive feed list gets wrong as of 2026-09-18, and how to review sources.

## No machine-readable feed

- Anthropic News, Engineering and claude.com/blog have no official feed.
  `sources.yaml` uses a community-generated feed (Olshansk/rss-feeds); verify on anthropic.com before citing.
- OpenAI API changelog: fetch `https://developers.openai.com/api/docs/changelog.md` and diff.
- Gemini API changelog: fetch `https://ai.google.dev/gemini-api/docs/changelog.md.txt` and diff.
- Thoughtworks Technology Radar: e-mail only; the insights feed is the whole blog (3 MB).
- Benchmarks (SWE-bench, SWE-bench Pro, Terminal-Bench, Arena, Artificial Analysis, OpenRouter): no feeds, monthly manual look.
  METR has `https://metr.org/feed.xml`.
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

## Momentum coverage

- Practitioner momentum (a tool everyone starts trying) shows up first on X, Zenn and Hacker News, not in vendor feeds.
  A first draft of the sample missed TypeSafe's Jev (launched 2026-09-15) for that reason: with a 4-day window the only feed item was one laiso post, hnrss was down, and X has no feed.
- Mitigations in place: `zenn-trending`, `hatena-llm`, `hn-llm` (reliability C, evidence only), the LangChain blog enabled, and the momentum check in AGENTS.md before a single-source item is dropped.
- Still uncovered: X itself.
  AINews summarises X daily, and the momentum check (one WebSearch) is the fallback.

## Operational caveats

- Large feeds: learn.chatgpt.com changelog (about 1 MB), Latent Space (about 0.9 MB).
- `hnrss.org` answers 502 intermittently; a failure there is expected noise.
- GitHub `releases.atom` feeds sometimes answer 504; retry on the next run.
- `https://github.com/anthropics/claude-code/releases.atom` answered 504 twice on 2026-09-18; the official changelog RSS is enough.
- Zenn topic feeds return the newest 20 items with no popularity signal; keep them disabled unless a downstream filter exists.

## Monthly review

1. `mise run stats` — sources that are enabled but never cited are demotion candidates.
2. Sources that keep appearing in web research but are not listed are promotion candidates; add them with a tier and reliability grade.
3. Re-check one tier-3 source per month by enabling it for a single run (`uv run scripts/fetch_feeds.py fetch --source <id>`).
4. Record what changed in the commit message; `sources.yaml` history is the log.
