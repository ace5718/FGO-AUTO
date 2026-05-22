# v0.2.0 手動測試清單（草案）

待 #17、#21、#22 完成後執行。前置：BlueStacks 視窗尺寸與 `display_preset` 一致。

## Quest profile：treasure_door_extreme

- [ ] 從主畫面自動點迦勒底之門 → 每日 → 寶物庫之門（極）
- [ ] 好友支援子流程可完成
- [ ] 編隊與出擊確認

## Battle script

- [ ] 第 1 回合：從者技能、禮裝技能、指令卡、寶具依 YAML 執行
- [ ] 第 2 回合：指令卡順序正確
- [ ] 戰鬥結束進入結果畫面

## 解析度

- [ ] 非 1920×1080 時使用對應 `data/catalog/<WxH>/` 仍可辨識與點擊

## Run 控制

- [ ] Loop limit、Manual stop、Run pause 行為與 v0.1 一致
