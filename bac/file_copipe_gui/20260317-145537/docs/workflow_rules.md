# docs\workflow_rules.md

# claude_orchestrator ワークフロールール

## 1. 目的

本書は、claude_orchestrator におけるタスク処理の状態遷移、
各役割の出力フラグ、および遷移条件を定義する。

Python（親アプリ）は本ルールに従って state を更新し、
次に実行すべき role を決定する。

Claude は本ルールに従った JSON report を出力する。


## 2. 基本構造

1つの task は以下のサイクルで処理される。
