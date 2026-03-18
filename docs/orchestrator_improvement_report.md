# docs\orchestrator_improvement_report.md

## 1. 概要

本ドキュメントは、Mini Task Board を用いた実地開発テスト（TASK-0001〜TASK-0028）を通じて得られた  
`claude_orchestrator` 本体の改善観点を整理したものである。

今回の検証により、以下が確認できた。

- workflow（task_router → implementer → reviewer → director）は安定して動作する
- revise サイクルも実運用レベルで成立している
- planner は一定の有効性を持つ
- skill ベース設計は有効だが、整合性管理に課題がある
- GUI auto-run は有用だが、GUI起動系タスクに弱点がある
- docs / research 系レビューの精度に改善余地がある

本レポートでは、これらを踏まえた改善点を優先度別に整理する。

---

## 2. 優先度：高

### 2-1. 存在しない skill が割り当てられる問題

#### 発生事象
- `debug-fix.md` や `migration-safety-check.md` が未作成にも関わらず割り当てられた
- 実行時に `FileNotFoundError` が発生し、プロセスが停止した

#### 原因
- task_router が実在する skill ファイルを厳密に参照していない

#### 改善案
- task_router は **存在する skill のみを割り当てることを保証する**
- 未存在 skill は即付与せず、report で「提案」に留める
- Python / GUI 側で `role_skill_plan` の存在チェックを事前実行する

#### 効果
- 実行時エラーの根絶
- skill 設計と実体のズレ防止

---

### 2-2. GUI起動確認タスクでの timeout 問題

#### 発生事象
- GUIアプリ起動タスクで 300秒 timeout が発生
- report は出ているがプロセスが終了せず進行不能

#### 原因
- auto-run がプロセス終了待ち前提のため、GUI常駐で詰まる

#### 改善案
- implementer のルールとして以下を明示
  - GUI確認後は即終了する
  - 常駐プロセスを残さない
- task_router が GUIタスク検知時に注意文を付与
- 将来的に
  - 手動進行フラグ
  - role別 timeout 設定
  を導入

#### 効果
- auto-run 安定化
- GUI系タスクの実用性向上

---

### 2-3. docs / research タスクのレビュー精度不足

#### 発生事象
- `workflow_rules.md` に整合性ミスが残ったまま approve されかけた

#### 原因
- code-review skill がコード寄りで、文書全体整合を見ない

#### 改善案
- docs専用 reviewer skill を導入
  - 例: `doc-consistency-review.md`
- docs task 時は reviewer skill を切り替える
- review観点に以下を追加
  - 文書内整合性
  - 用語統一
  - 前後矛盾
  - 既存仕様との一致

#### 効果
- docs品質向上
- director の負担軽減

---

## 3. 優先度：中

### 3-1. 実行モニタログの冗長性

#### 現象
- `advanced to next role` などが重複表示
- 状態把握はできるが視認性が低い

#### 改善案
- monitor と log を分離
- monitor は簡潔表示
- log は詳細表示

---

### 3-2. stdout 表示の不統一

#### 現象
- report があるのに stdout に JSON が出ない場合あり

#### 改善案
- stdout は参考扱いにする
- report ファイルを UI で直接要約表示する

---

### 3-3. planner の優先順位のズレ

#### 現象
- 実装優先になりがちで、検証優先とズレる場合あり

#### 改善案
- planner に以下を強化
  - director の next_actions を優先
  - 検証順も考慮
- proposal に補助情報追加
  - why_now
  - depends_on

---

### 3-4. skill設計の三者整合問題

#### 現象
- skill_design.md / route-task.md / 実ファイルがズレる

#### 改善案
- 正の情報源を定義
  - skill_design.md = 設計
  - route-task.md = 運用
- skill一覧の明示管理を導入

---

## 4. 優先度：低〜中

### 4-1. lightweight docs の必要性

#### 観察
- test repo では軽量 docs の方が扱いやすい

#### 改善案
- 本家 / 軽量版 docs の使い分けを定義

---

### 4-2. docs/report の根拠記述強化

#### 観察
- implementer report に根拠が不足するケースあり

#### 改善案
- docs/report テンプレ強化
  - 参照ファイル
  - 差分
  - 確定事項 / 未確定事項

---

## 5. 確認できた強み

- workflow が安定して回る
- revise ループが機能する
- planner は実用レベル
- skill設計は有効
- GUI運用は視認性が高い

---

## 6. 改善優先順位

1. skill 存在チェックの導入  
2. GUIタスクの timeout 対策  
3. docsレビュー強化  
4. planner 精度向上  
5. モニタ表示改善  

---

## 7. 結論

claude_orchestrator は実地テストにより、

**「小規模アプリ開発を段階的に前進させる基盤として成立している」**

ことが確認できた。

一方で、以下の改善によりさらに実運用レベルへ近づく。

- skill整合性の保証
- GUIタスク対応強化
- docsレビュー品質向上
- planner判断精度改善
- UIログの整理

これらを段階的に改善していくことで、  
より安定かつ信頼できる開発基盤になると考えられる。