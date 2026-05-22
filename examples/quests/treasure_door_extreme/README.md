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



## 好友助戰（流程裡的「好友助戰」步驟）



**遊戲內正確順序：**



1. **選職階**（全部／指定職階分頁）  

2. **在列表找目標好友**（看禮裝、從者，或兩者特徵）— 沒有就按 **「更新」** 重整，直到找到或達次數上限  

3. **點該好友**  

4. **開始編隊** — 由 `navigation.yaml` 後續步驟處理（`party_slot_1`、`deploy_confirm` 等）



**GUI 設定（不必手改 profile.yaml）：**

1. **流程設定** → ＋好友 → 儲存  
2. **圖示庫** → **啟用預設好友流程** → 設「更新」次數 → **儲存好友設定**  
3. 依畫面提示 **去預覽存圖**（三張，名稱如下）



| 預覽存圖名稱 | 白話 |

|-------------|------|

| `friend_class_all` | 選職階分頁（例如「全部」） |

| `friend_target` | 要找的好友那一列（框選禮裝或從者特徵） |

| `friend_refresh` | 「更新」按鈕（重整列表） |



## CLI



```bash

fgo-auto run -c examples/run.example.yaml --quest-profile treasure_door_extreme

```



With fixture frame:



```bash

fgo-auto run -c examples/run.example.yaml --quest-profile treasure_door_extreme --fixture tests/fixtures/frames/terminal.png

```



Set `script_version: v2` and `quest_profile: treasure_door_extreme` in run.yaml for GUI runs.

