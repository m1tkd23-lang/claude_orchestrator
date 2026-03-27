# feature_inventory

## 目的

この文書は、repo 内の主要機能を棚卸しし、現在の状態を整理するための一覧である。  
planner / plan_director は、この文書を参照して以下を判断する。

- 既実装か
- GUI 未接続か
- 未実装か
- 対象外か
- 重複 proposal になっていないか
- 次にどの層を前進させるべきか

---

## 状態ラベル

- `implemented`
  - 実装済み
- `gui_unconnected`
  - 内部実装はあるが GUI など主要導線が未接続
- `partial`
  - 一部完了
- `not_implemented`
  - 未実装
- `out_of_scope`
  - 現時点では対象外

---

## 記載ルール

各機能は最低限、以下を意識して整理する。

- 機能名
- 層
  - domain
  - usecase
  - infrastructure
  - gui
  - cli
  - docs
  - tests
- 状態
- 関連ファイル
- 備考

---

## 例

以下は記入例。repo ごとに更新して使う。

### 主要データの新規作成
- layer: usecase / gui
- status: partial
- related_files:
  - apps/gui_main.py
  - src/.../main_window.py
  - src/.../usecase/...
- notes:
  - usecase はあるが GUI 導線が簡易

### JSON 保存・読込
- layer: usecase / infrastructure / gui
- status: implemented
- related_files:
  - src/.../json_repository.py
  - src/.../usecase/...
- notes:
  - 正本形式として利用

### CSV import/export
- layer: usecase / gui
- status: partial
- related_files:
  - src/.../usecase/...
  - src/.../main_window.py
- notes:
  - 一部導線あり。仕様固定要確認

### Excel import/export
- layer: usecase / gui
- status: not_implemented
- related_files: []
- notes:
  - 今後対応予定

### validation
- layer: usecase / gui / tests
- status: partial
- related_files:
  - src/.../usecase/...
- notes:
  - 基本チェックあり。拡張余地あり

### diff / merge
- layer: usecase
- status: gui_unconnected
- related_files:
  - src/.../usecase/...
- notes:
  - usecase はあるが GUI 導線未接続

---

## planner / plan_director 用ルール

### planner
- `implemented` を未実装として提案しない
- `gui_unconnected` は、新規機能ではなく導線補完として扱う
- `partial` は不足箇所を具体化して proposal に落とす
- `out_of_scope` は mainline で優先しない

### plan_director
- `implemented` の proposal は重複として減点または不採択
- `gui_unconnected` は導線補完として評価する
- `partial` は completion_definition との接続が強い場合に評価する
- `not_implemented` は完成条件への寄与が明確な場合に評価する

---

## 更新ルール

- task 完了後に必要なら更新候補として扱う
- 実装済み / 未接続 / 未実装の判断を曖昧にしない
- completion_definition と矛盾しないように保つ
- 同じ機能を別名で重複記載しない