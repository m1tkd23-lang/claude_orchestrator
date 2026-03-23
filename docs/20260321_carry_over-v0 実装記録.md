# carry_over-v0 実装記録

**作成日**: 2026-03-21  
**対象 task**: TASK-0012 ～ TASK-0014  
**ステータス**: 実装完了・動作確認済み  

---

## 1. 概要

carry_over-v0 は、前 task の `director_report.remaining_risks` を次 task の `initial_execution_notes` に引き継ぐ仕組みである。

本バージョンでは Python 実装や schema を変更せず、  
**prompt と運用ルールのみで実現する最小構成（v0）** として導入した。

---

## 2. 実装内容

### 2-1. task_router_prompt.txt への追記

以下のセクションを新規追加：

carry_over 処理ルール

内容：

- `context_files` に `director_report_vN.json` が含まれる場合
- `remaining_risks` を読み取り
- `initial_execution_notes` の先頭へ転記

フォーマット：


"[carry_over from TASK-XXXX] {remaining_risks の内容}"


---

### 2-2. 運用ガイドの追加

作成ファイル：


.claude_orchestrator/docs/operations/carry_over_guide.md


内容：

- carry_over 対象
- 手順
- フォーマット規則
- 未定義事項（v1対応予定）

---

### 2-3. prompt_renderer の修正（重要）

従来：

```python
template.format(**kwargs)

問題：

{N} など説明用プレースホルダで KeyError 発生

修正後：

既知キーのみ置換
未知 {...} はそのまま保持

これにより：

JSON例
パス表記（{N}）
carry_over説明文

が安全に扱えるようになった

3. 動作確認（TASK-0014）
確認結果
項目	結果
remaining_risks 件数	一致（4件）
内容一致	OK
順序一致	OK
プレフィックス付与	OK
initial_execution_notes 先頭配置	OK
結論

carry_over-v0 は正常動作

4. 効果
Before
task 間で未解決事項が断絶
改善の連続性が弱い
reviewer / director の知見が活かされない
After
未解決リスクが次 task に強制的に流入
改善ラインが自然に継続
Orchestrator の「学習性」が向上
5. 残課題（v1以降）
5-1. 累積問題
TASK-N → N+1 → N+2 → ...
carry_over が増え続ける
可読性低下

→ v1で対応

5-2. nice_to_have の扱い

現状：

人判断

課題：

判断基準が未定義
5-3. 「自動転記」表現の曖昧さ

実態：

LLM prompt による挙動

誤解リスク：

プログラム処理と混同される
5-4. task_router の処理順明示

現状：

整合チェック → 判断 → carry_over → 出力

だが明文化されていない

6. 今後の発展（ロードマップ）
v1（次段階）
carry_over 上限管理
フィルタリング
nice_to_have 基準明文化
v2（中期）
schema 対応
自動マージ
優先度制御
v3（理想）
Orchestrator が自律的に改善継続
改善ラインと主線の統合制御
7. 結論

carry_over-v0 は：

最小変更で導入可能
実動確認済み
Orchestrator の改善能力を明確に向上させる