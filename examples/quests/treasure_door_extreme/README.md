# 寶物庫之門（極）— Quest profile

Tracer profile for v0.2 navigation + battle scripts.

## 怎麼鎖定要點的關卡？

1. **流程設定** → 從範例複製到本機 → **套用設定**  
2. **預覽** → **擷圖** → 在圖上**滑鼠拖曳**拉出黃框 → 填圖示名稱 → **儲存框選**  
3. 圖檔會存到 `data/profiles/quests/<id>/anchors/<名稱>.png`

畫面上很多 banner 沒關係，比對只看你的小圖。

## 列表要往下拉才看得到？

在「流程設定」用 **往下滑找圖示**，圖示名稱與 anchors 相同；程式會先找，找不到就向下滑動再找。

## Anchor names (navigation.yaml)

| Anchor | Step |
|--------|------|
| `chaldea_gate` | 迦勒底之門（畫面上方，用「點擊」） |
| `daily_quests` | 每日任務 |
| `door_treasure_extreme` | 寶物庫之門（極）（若在下方，改用「往下滑找」） |
| `party_slot_1` | 編隊槽 1 |
| `deploy_confirm` | 出擊確認 |

Friend support subflow (`friend_support` in profile.yaml): `friend_list_open`, `friend_slot_1`, `friend_confirm`.

Place calibrated PNGs under `anchors/` or `data/profiles/quests/treasure_door_extreme/anchors/`.

## CLI

```bash
fgo-auto run -c examples/run.example.yaml --quest-profile treasure_door_extreme
```

With fixture frame:

```bash
fgo-auto run -c examples/run.example.yaml --quest-profile treasure_door_extreme --fixture tests/fixtures/frames/terminal.png
```

Set `script_version: v2` and `quest_profile: treasure_door_extreme` in run.yaml for GUI runs.
