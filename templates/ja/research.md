---
title: "GenAI catch-up research YYYY-MM-DD"
date: YYYY-MM-DD
run: scheduled            # scheduled | manual
window: "YYYY-MM-DD..YYYY-MM-DD"
candidates: 0             # number of items in work/candidates.md
themes:                   # selected themes only, in rank order
  - id: 1
    emoji: "🧭"
    title: "テーマ 1 の見出し (具体的な出来事を 1 文で)"
    track: genai-eng      # genai-eng | coding-ai | both
    impact: 2             # 0-2, see AGENTS.md
    potential: 2          # 0-2
sources_used: [claude-code-changelog]   # ids from sources.yaml that contributed a citation
---

# GenAI catch-up 調査ノート YYYY-MM-DD

- 対象期間: YYYY-MM-DD 〜 YYYY-MM-DD (前回の実行日以降、候補 N 件)。
- 取得できなかった情報源: なし。

## 候補と選定

- 選定 (レポートに載せる):
    1. テーマ 1 の見出し (起点 MM-DD、影響度 2 / 将来性 2)。
    2. テーマ 2 の見出し (起点 MM-DD、2 / 1)。
- 見送り (次回の判断材料):
    3. テーマ 3 の見出し (起点 MM-DD、1 / 1) — 理由を 1 文で。
    4. テーマ 4 の見出し (期間外 MM-DD の再掲、1 / 2) — 理由を 1 文で。

## 1. 🧭 テーマ 1 の見出し

- 選定 / 影響度 2 / 将来性 2 / 起点 MM-DD / トラック: 生成AIエンジニアリング。
- 候補になったフィード項目:
    - `source-id` MM-DD [項目のタイトル](URL)
    - `source-id` MM-DD [項目のタイトル](URL)

### 収集した情報

#### [A] 発行元 — タイトル (YYYY-MM-DD)

<URL>

- 一次情報の事実を、数値・名称・表現をそのまま残して箇条書きにする。
- 1 項目 1 文で、まとめない。

#### [B] 発行元 — タイトル (YYYY-MM-DD)

<URL>

- 独立した分析の主張と、一次情報との差分。

#### [C] 発行元 — タイトル (YYYY-MM-DD)

<URL>

- コミュニティの反応 (補足)。

### メモ

- 情報源どうしの食い違い、未確認の主張、次回に持ち越す疑問。

### 実践やアウトプットの提案

- 何を、どの規模で、何を確かめるために試すか。

## 3. 🧪 見送りテーマの見出し

- 見送り / 影響度 1 / 将来性 1 / 起点 MM-DD / トラック: コーディングAI。
- 候補になったフィード項目:
    - `source-id` MM-DD [項目のタイトル](URL)
- 見送りの理由を 1 文で。
