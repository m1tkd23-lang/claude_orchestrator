# Claude Orchestrator MVP 引き継ぎ資料

## 概要

本ドキュメントは、Claude Code を用いた「手動中継型オーケストレーション」の
MVP実装状況と今後の拡張方針をまとめたものである。

本システムは、APIを使用せず、JSONベースで役割間の作業を中継することで
Claude Code を複数役割（implementer / reviewer / director）として運用する。

---

## 実現したこと（MVP機能）

### 1. プロジェクト初期化

コマンド:


init-project


機能:

- 対象 repo に `.claude_orchestrator/` を生成
- roles / schemas / templates を配置

---

### 2. タスク生成

コマンド:


create-task


機能:

- task.json / state.json を生成
- TASK-XXXX 単位で管理

---

### 3. 次工程プロンプト生成

コマンド:


show-next


機能:

- 現在の state に基づき次の role を決定
- prompt ファイル生成
- 出力 JSON の保存先を提示

---

### 4. レポート検証

コマンド:


validate-report


機能:

- JSON schema による検証
- role / cycle 一致確認
- JSON破損検出

重要ルール:

- JSONの先頭にコメントを書かない
- 相対パスは `_meta.relative_path` に保持

---

### 5. 状態遷移

コマンド:


advance


機能:

- report を元に state.json 更新
- role 遷移制御

遷移パターン:

#### 正常完了

implementer → reviewer → director → completed


#### 修正ループ

implementer → reviewer → director(revise)
→ implementer (cycle+1)


---

### 6. ステータス確認

コマンド:


status


機能:

#### 一覧

TASK-0001 | status=completed | current=director | ...


#### 単体

Task ID : ...
Status : ...
Current : ...
Cycle : ...


---

## 確認済み動作

### 正常フロー（approve）
- 完全に動作確認済み
- status=completed まで遷移

### reviseフロー
- cycle が増加することを確認
- implementer に戻ることを確認
- v2 prompt 生成を確認

---

## システム構造

### 役割

| role | 説明 |
|------|------|
| implementer | 実装担当 |
| reviewer | レビュー担当 |
| director | 意思決定 |

---

### データ構造


.claude_orchestrator/
├─ tasks/
│ ├─ TASK-0001/
│ │ ├─ task.json
│ │ ├─ state.json
│ │ ├─ inbox/
│ │ └─ outbox/


---

### JSON設計

#### 必須ルール
- JSON only（前置き禁止）
- schema準拠
- role固定
- cycle一致

#### 注意点
- JSON先頭にコメントを書かない（重要）
- `_meta.relative_path` を使用

---

## 設計思想

### 1. API非依存
- 課金リスク回避
- CLIベースで運用

### 2. 手動中継
- 人間が control point になる
- 誤作動リスク低減

### 3. 役割分離
- implementer / reviewer / director を明確化
- 思考の混線を防ぐ

### 4. GUI拡張前提
- CLIをコアとする
- 将来的にGUI追加

---

## 現在の課題

### 1. 手動コピー負荷
- prompt コピー
- JSON貼り付け

### 2. エラー可視性
- JSONエラーが分かりにくい

### 3. 運用ルール依存
- JSONフォーマット崩れに弱い

---

## 次に行う作業

### 優先度 高

#### 1. クリップボードコピー機能
- show-next 実行時に prompt をコピー
- 作業効率向上

#### 2. JSON出力ルール強化
- role定義 / promptに明記
- 事故防止

#### 3. エラー表示改善
- JSONDecodeErrorの説明追加
- どこが壊れているか表示

---

### 優先度 中

#### 4. status表示改善
- テーブル表示
- 色分け

#### 5. task削除 / archive
- 不要task整理

#### 6. blocked管理
- reason表示
- 再開制御

---

### 優先度 低（将来）

#### 7. GUI化
- タスク一覧
- コンソール管理
- ログビュー

#### 8. 自動連携
- CLI自動起動
- セッション制御

---

## 今後の方向性

このシステムは以下に進化可能:

- AI作業員の多人数化
- 複数タスク並列管理
- プロジェクト単位の可視化
- 完全GUI化

---

## まとめ

本MVPで実現したこと:

- Claude Code を役割分担で運用する基盤を構築
- JSONベースの安全な中継システムを確立
- ワークフロー（approve / revise）を完全再現

現時点で、
**「人間 + Claude複数人格」で開発を回す基盤」は成立している。**
補足

この状態、かなり面白い地点に来ています。
普通の「AI補助」ではなくて、

AIに役割を持たせて

人間がオーケストレーションする

という構造になっている。

つまりこれはもうツールというより、
“チームの設計”をコード化している状態です。