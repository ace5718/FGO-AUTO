# Desktop UI 手動測試清單（Phase 1 MVP）

前置：BlueStacks 5、1920×1080、台服 FGO 已開啟。

```powershell
cd D:\FGO-AUTO
.\venv\Scripts\Activate.ps1
pip install -e ".[dev,windows,gui]"
.\scripts\init-local-profile.ps1
fgo-auto-gui
```

## 設定

- [ ] 啟動後載入 `data/profiles/default/run.yaml`（或 init 腳本建立的 profile）
- [ ] 修改 `loop_limit`、`window_title_rule` → **儲存** → 重開 GUI 仍保留
- [ ] **驗證** 顯示 summary JSON，無錯誤

## 視窗

- [ ] 輸入 `window_title_rule`（例：`BlueStacks`）→ **重新整理** 列出候選
- [ ] 選一個 handle，Run 分頁狀態可辨識已綁定

## 預覽

- [ ] 綁定視窗後 **擷圖** 顯示縮圖
- [ ] `logs/frame.png` 存在且為 1920×1080（或設定之 Display preset）
- [ ] 「框選 Anchor（Phase 2）」為 disabled 或提示尚未實作

## Run

- [ ] **Start Run** 後 Screen state 文字會更新
- [ ] **Manual stop** 後顯示 Normal Run end
- [ ] Recognition 失敗時 Outcome 為 Run pause，並提示 `logs/pause_screenshot.png`

## 日誌

- [ ] 日誌分頁出現 structlog 輸出
- [ ] Run 期間無 Tk 跨執行緒錯誤（主視窗不凍結太久）

## Catalog（Phase 2 stub）

- [ ] Catalog 分頁「列出 Screen state」顯示 NotImplemented 或占位說明
