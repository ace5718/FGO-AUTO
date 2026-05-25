from fgo_auto.services.flow_library import LibraryLayout, list_library_layout


def test_layout_has_no_uncategorized_folder_header(monkeypatch) -> None:
    from fgo_auto.services import flow_library as lib
    from fgo_auto.services.quest_flow_service import QuestProfileEntry
    from pathlib import Path

    entry = QuestProfileEntry(
        quest_id="test",
        display_name="Test",
        directory=Path("."),
        is_user_copy=True,
    )

    monkeypatch.setattr(lib, "load_library", lambda: lib.FlowLibrary())
    monkeypatch.setattr(lib, "list_user_quest_profiles", lambda: [entry])

    layout = list_library_layout()
    assert isinstance(layout, LibraryLayout)
    assert len(layout.unassigned) == 1
    assert layout.folders == ()
    flat = lib.list_library_tree()
    assert all(item.item_id != "__root__" for item in flat)
    assert all("未分類" not in item.label for item in flat if item.kind == "folder")
