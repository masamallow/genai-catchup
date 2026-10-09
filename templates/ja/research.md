---
title: "GenAI catch-up research YYYY-MM-DD"
date: YYYY-MM-DD
run: scheduled            # scheduled | manual
generated_by: "<agent> <model>"   # as the runtime names them, e.g. Claude Opus 5.5 or Codex GPT-6 Sol
window: "YYYY-MM-DD..YYYY-MM-DD"
candidates: 0             # number of items in work/candidates.md
topics:                   # selected topics only, in rank order
  - id: 1
    emoji: "🧭"
    title: "トピック 1 の見出し (1 つの出来事か 1 つの成果物を 1 文で)"
    kind: release         # release | change | incident | research | hands-on | analysis
    areas: [models, api-cloud]   # 1 or 2 of: models, api-cloud, coding-agents, agent-dev, security, evals-ops
    impact: 2             # 0-2, see AGENTS.md
    potential: 2          # 0-2
    attention: 2          # 0-2, discussion in credible venues
sources_used: [claude-code-changelog]   # ids from sources.yaml that contributed a citation
---

# GenAI catch-up 調査ノート YYYY-MM-DD

- 対象期間: YYYY-MM-DD 〜 YYYY-MM-DD (前回の実行日以降、候補 N 件)。
- 取得できなかった情報源: なし。

## 候補と選定

- 選定 (レポートに載せる):
    1. トピック 1 の見出し (起点 MM-DD、影響度 2 / 将来性 2 / 注目度 2)。
    2. トピック 2 の見出し (起点 MM-DD、期間前の出来事で `source-id` で初出、1 / 2 / 2)。
- 見送り (次回の判断材料):
    3. トピック 3 の見出し (起点 MM-DD、1 / 1 / 1) — 何が足りないかを 1 文で。
    4. トピック 4 の見出し (起点 MM-DD、1 / 2 / 0) — 何が足りないかを 1 文で。
    5. その他の単発項目 — 下記に列挙。
    6. 対象外 (スコープ外) — 下記に列挙。

## 1. 🧭 トピック 1 の見出し

- 選定 / 影響度 2 / 将来性 2 / 注目度 2 / 起点 MM-DD / 種別: リリース / 領域: モデル、API・クラウド。
- 候補になったフィード項目:
    - `source-id` MM-DD [項目のタイトル](URL) — はてなブックマーク 120 users (取得時点)
    - `source-id` MM-DD [項目のタイトル](URL)

### 収集した情報

#### [A] 発行元 — タイトル (YYYY-MM-DD)

<URL>

- トピックの土台になる事実を自分の言葉で書き、数値・名称・識別子は正確に残す。
- 一次情報でも 10 項目程度にとどめ、残りは URL 先に任せる。

#### [B] 発行元 — タイトル (YYYY-MM-DD)

<URL>

- この分析が加えるもの (計測、見方、一次情報との差分) を 1〜4 項目で。

#### [C] 発行元 — タイトル (YYYY-MM-DD)

<URL>

- コミュニティの反応を 1〜2 項目で (補足)。

### メモ

- 情報源どうしの食い違い、未確認の主張、次回に持ち越す疑問。

### 実践やアウトプットの提案

- 何を、どの規模で、何を確かめるために試すか。

## 3. 🧪 見送りトピックの見出し

- 見送り / 影響度 1 / 将来性 1 / 注目度 1 / 起点 MM-DD / 種別: 検証・実践 / 領域: コーディングエージェント。
- 候補になったフィード項目:
    - `source-id` MM-DD [項目のタイトル](URL)
- 見送りの理由: 何が足りないかを、目的語を省かずに 1 文で書く (例: 一部のチームにしか関係せず、発表元の外ではまだ誰も論じていない)。

## 5. 📎 その他の単発項目

- 見送り / 1 件ずつ採点し、いずれも閾値から遠い。
- `source-id` MM-DD 項目を短く。

## 6. 🚫 対象外 (スコープ外)

- `source-id` MM-DD 項目を短く。
