改修タスク分解案（Orchestrator改善）
全体方針
既存構造は壊さない
差分は小さく
1タスク＝1改善テーマ
動作確認しながら段階的に強化
フェーズ構成
Phase 1: task_router強化（入口の精度を上げる）
Phase 2: carry-over導入（文脈の持続）
Phase 3: write-plan可視化（判断の透明化）
Phase 4: 未確定情報の分離（誤解防止）
Phase 5: reviewer/director強化（後段の精度）
Phase 1: task_router強化（最優先）
TASK-R1: constraints整合チェック導入
目的

TASK-0003のような矛盾を防ぐ

対象

.claude_orchestrator/roles/task_router.md
.claude_orchestrator/templates/task_router_prompt.txt

変更内容

task_routerに以下の判断を強制追加

チェック項目
constraints同士の矛盾検出
constraintsと完了条件の矛盾
実行可能性チェック
「同時に成立しない条件」がないか
追加ルール（重要）
矛盾があれば status = blocked
skill_selection_reason に理由明記
TASK-R2: task_routerに「不足検出」を追加
目的

曖昧なtaskを止める

追加チェック
必須context不足
仕様未確定なのに実装要求
「判断不能」な状態
挙動

→ blockedにする

Phase 2: carry-over（文脈の持続）
TASK-R3: carry_over構造導入（最重要）
目的

「前タスクの残課題が消える問題」を解消

追加フィールド案（task.json）
"carry_over": {
  "from_task": "TASK-0002",
  "items": [
    "updated_at更新ルール未決定",
    "sequence外部変更制御未定"
  ]
}
ルール
director
remaining_risks → carry_over候補に変換
task_router
新task作成時にcarry_overをcontextに追加
implementer
carry_overを必ず確認
TASK-R4: reviewer / director に carry_over参照義務追加
追加ルール
reviewer:
carry_overが未解決かチェック
director:
carry_overが放置されていないか確認
Phase 3: write-plan可視化
TASK-R5: write-plan保存先固定
目的

「計画がどこにあるか不明問題」解消

保存先
.claude_orchestrator/tasks/TASK-xxxx/plan.md
TASK-R6: implementer_reportにplan参照追加
追加フィールド
"plan_artifacts": [
  ".claude_orchestrator/tasks/TASK-0002/plan.md"
]
Phase 4: 未確定情報の分離
TASK-R7: assumptions / confirmed分離
追加構造（task or doc）
"decisions": {
  "confirmed": [],
  "assumptions": [],
  "needs_confirmation": []
}
効果
仮定が勝手に確定化されるのを防ぐ
reviewerが判断しやすくなる
Phase 5: reviewer / director強化
TASK-R8: reviewerに「前段整合チェック」追加
追加観点
前taskのremaining_risks参照
carry_over確認
why_nowとの整合
TASK-R9: directorに「承認条件チェック」追加
追加観点
未解決リスクが許容範囲か
次タスクに渡すべき事項が明確か
（オプション）TASK-R10: 承認粒度拡張

現状:

approve / revise / stop

将来:

approve
approve_with_notes
revise
stop

※これは後回しでOK

実装順（重要）

この順番でやると安全です

① TASK-R1（constraintsチェック）
② TASK-R3（carry_over導入）
③ TASK-R5（write-plan固定）
④ TASK-R8（reviewer強化）
⑤ TASK-R7（assumptions分離）
最初の1タスク（すぐやるべき）
👉 次にやるべきタスク
「TASK-R1: task_router整合チェック強化」

理由:

ここが一番事故を防ぐ
他の改善の土台になる
影響範囲が小さい
最終まとめ

今の状態は

👉 構造は完成している
👉 運用も成立している
👉 問題は“知能”ではなく“接続ルール”

そして改善の核心はこれです

・矛盾を入口で止める（task_router）
・文脈を途切れさせない（carry_over）
・判断を見える化する（write-plan）