# src\claude_orchestrator\template_assets\project_bundle\.claude_orchestrator\skills\implementer\execute-plan.md
# execute-plan

implementer 用 skill です。

## 目的

整理済みの方針に沿って、小さく安全に実装すること。

## 手順

1. 変更対象を確認する
2. 変更方針から外れないように実装する
3. 不要な横展開をしない
4. 実行したコマンドや確認結果を残す
5. changed_files を正確に記録する
6. 未解決点や懸念を risks / questions に残す

## 期待される効果

- 実装の暴走を防ぐ
- report の再現性を高める
- reviewer が追いやすい変更にする

## GUI起動確認・長時間プロセスに関する注意

- GUI起動確認を行う場合は、起動を確認したら速やかにプロセスを終了すること
- 長時間プロセスを残したまま完了報告をしないこと
- auto-run をブロックしない確認方法（起動後即終了、ログ確認のみ 等）を優先すること
- 確認作業が終わったらバックグラウンドプロセスが残っていないことを確認してから status を done にすること