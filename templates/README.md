# Templates

One directory per language, named by its code (`en`, `ja`, ...).  
Everything that depends on the language lives here; the rest of the repository is language-neutral.

| File | Purpose |
| --- | --- |
| `research.md` | Skeleton of the research note: front matter, header, the candidates section, one thick theme and one thin one |
| `report.md` | Skeleton of the Marp deck: the summary slide and one theme slide |
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
| Research: continuation of an earlier theme | Continued from | 前回からの継続 |
| Report: what happened | Key points | 要点 |
| Report: framing, perspectives, constraints | Perspectives and debates | 見方と論点 |
| Report: identifiers, stack, pricing, specs | Technical details | 技術要素 |
| Labels | Selected, Dropped, Impact, Potential, Anchor, Track, Background, unverified | 選定、見送り、影響度、将来性、起点、トラック、背景、未確認 |
