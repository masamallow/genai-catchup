# Templates

One directory per language, named by its code (`en`, `ja`, ...).  
Everything that depends on the language lives here; the rest of the repository is language-neutral.

| File | Purpose |
| --- | --- |
| `research.md` | Skeleton of the research note: front matter, header, the candidates section, one thick topic, one thin one and the two groups of minor items |
| `report.md` | Skeleton of the Marp deck: the summary slide, one topic slide and one Other topics slide |
| `site.yaml` | Strings of the site chrome: language name, tagline, link labels, empty state |

`content/en/` is always written; other editions are written when a run asks for them (`languages: en, ja`).  
The build discovers `content/<lang>/` on its own and reads `templates/<lang>/site.yaml`; strings that are missing fall back to English.

## Adding a language

1. Copy `en/` to `<code>/` and translate the headings, labels and placeholders.
   Keep the structure, the front-matter keys, the HTML classes and the `lang` directive.
2. Fill in `site.yaml`.
3. Ask for the edition with `languages: en, <code>`.

Typography needs no per-language setup: the theme uses a generic font stack and every page and slide carries its `lang` attribute, so browsers pick the script fallback.  
A language that wants specific fonts can add a `style:` global directive to its `report.md`.

## Section names and labels

The templates are the source of truth; this table lines them up.

| Section | `en` | `ja` |
| --- | --- | --- |
| Research: scored shortlist | Candidates and selection | 候補と選定 |
| Research: per-source bullets | Collected information | 収集した情報 |
| Research: contradictions and open questions | Notes | メモ |
| Research: what the reader might try | Ideas for practice and output | 実践やアウトプットの提案 |
| Research: unit of selection | Topic | トピック |
| Research: feed items of a topic | Feed items in this topic | 候補になったフィード項目 |
| Research: minor dropped items | Other one-off items | その他の単発項目 |
| Research: dropped as out of scope | Out of scope | 対象外 (スコープ外) |
| Research: continuation of an earlier topic | Continued from | 前回からの継続 |
| Report: what happened | Key points | 要点 |
| Report: framing, perspectives, constraints | Perspectives and debates | 見方と論点 |
| Report: identifiers, stack, pricing, specs | Technical details | 技術要素 |
| Report: slide that gathers the thinner topics | Other topics | その他のトピック |
| Labels | Selected, Dropped, Impact, Potential, Importance, Anchor, before the window, Kind, Areas, Background, unverified | 選定、見送り、影響度、将来性、重要度、起点、期間前の出来事、種別、領域、背景、未確認 |

## Tags on the summary cards

A card carries three level tags, one kind tag and one or two area tags.  
The front matter of the research note stores the keys; the cards show the labels of the edition.

| Level tag (class) | `en` | `ja` |
| --- | --- | --- |
| `tag high` (score 2) | Impact high, Potential high, Importance high | 影響 高、将来性 高、重要度 高 |
| `tag mid` (score 1) | Impact mid, Potential mid, Importance mid | 影響 中、将来性 中、重要度 中 |
| `tag low` (score 0) | Impact low, Potential low, Importance low | 影響 低、将来性 低、重要度 低 |

| Kind (`kind`) | `en` | `ja` | Meaning |
| --- | --- | --- | --- |
| `release` | Release | リリース | A new model, product or feature, or new availability |
| `change` | Change | 仕様変更 | A change to pricing, defaults, policies or support, including deprecations |
| `incident` | Incident | インシデント | An incident or its disclosure |
| `research` | Research | 研究・評価 | A paper, benchmark, system card or measurement by a vendor or lab |
| `hands-on` | Hands-on | 検証・実践 | A practitioner's test, build or technique |
| `analysis` | Analysis | 論考 | Commentary, debate or industry analysis |

| Area (`areas`) | `en` | `ja` | Meaning |
| --- | --- | --- | --- |
| `models` | Models | モデル | Model releases, capabilities and pricing |
| `api-cloud` | API and cloud | API・クラウド | Model APIs and the cloud AI platforms (Bedrock, Vertex AI, Foundry) |
| `coding-agents` | Coding agents | コーディングエージェント | Claude Code, Codex, Copilot, Cursor, Gemini CLI, Kiro and their workflows |
| `agent-dev` | Agent building | エージェント開発 | Frameworks, harnesses, MCP, A2A, RAG |
| `security` | Security and safety | セキュリティ・安全性 | Sandboxes, permissions, incidents, safeguards |
| `evals-ops` | Evals and operations | 評価・運用 | Evals, observability, cost |
