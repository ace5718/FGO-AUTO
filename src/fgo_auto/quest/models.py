"""Pydantic models for Quest profiles, navigation steps, and battle scripts."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field


class FriendSupportConfig(BaseModel):
    """Friend support picker: class tab → find friend (CE/servant) → refresh until found → tap."""

    mode: Literal["anchor_sequence"] = "anchor_sequence"
    max_refresh_attempts: int = Field(default=20, ge=1, le=60)
    steps: list[dict[str, str | int | float]] = Field(default_factory=list)


class QuestProfile(BaseModel):
    quest_id: str
    display_name: str = ""
    navigation_script: str
    battle_script: str
    party_slot: int = Field(default=1, ge=1, le=3)
    friend_support: FriendSupportConfig | None = None


class TapAnchorStep(BaseModel):
    action: Literal["tap_anchor"] = "tap_anchor"
    name: str


class TapCoordinateStep(BaseModel):
    action: Literal["tap_coordinate"] = "tap_coordinate"
    x: int = Field(ge=0)
    y: int = Field(ge=0)


class ScrollUntilAnchorStep(BaseModel):
    """Swipe the quest list down until anchor template is found, then tap."""

    action: Literal["scroll_until_anchor"] = "scroll_until_anchor"
    name: str
    max_attempts: int = Field(default=8, ge=1, le=30)


class WaitScreenStep(BaseModel):
    action: Literal["wait_screen"] = "wait_screen"
    state: str
    timeout_s: float = 30.0


class DelayStep(BaseModel):
    action: Literal["delay"] = "delay"
    seconds: float = 0.5


class RefreshUntilAnchorStep(BaseModel):
    """Tap refresh until anchor appears (e.g. friend list)."""

    action: Literal["refresh_until_anchor"] = "refresh_until_anchor"
    name: str
    max_attempts: int = Field(default=20, ge=1, le=60)
    refresh_anchor: str = "friend_refresh"


class RunSubflowStep(BaseModel):
    action: Literal["run_subflow"] = "run_subflow"
    ref: str
    repeat: int = Field(default=1, ge=1, le=99)
    interval_s: float = Field(default=0.5, ge=0)


NavigationStep = Annotated[
    TapAnchorStep
    | TapCoordinateStep
    | ScrollUntilAnchorStep
    | RefreshUntilAnchorStep
    | WaitScreenStep
    | DelayStep
    | RunSubflowStep,
    Field(discriminator="action"),
]


class NavigationScript(BaseModel):
    steps: list[NavigationStep]


class ServantSkillAction(BaseModel):
    type: Literal["servant_skill"] = "servant_skill"
    slot: int = Field(ge=1, le=3)
    skill: int = Field(ge=1, le=3)


class CraftSkillAction(BaseModel):
    type: Literal["craft_skill"] = "craft_skill"
    skill: int = Field(ge=1, le=3)


class SelectCardsAction(BaseModel):
    type: Literal["select_cards"] = "select_cards"
    cards: list[int] = Field(min_length=1, max_length=3)


class NoblePhantasmAction(BaseModel):
    type: Literal["noble_phantasm"] = "noble_phantasm"
    slot: int = Field(ge=1, le=3)


BattleAction = Annotated[
    ServantSkillAction | CraftSkillAction | SelectCardsAction | NoblePhantasmAction,
    Field(discriminator="type"),
]


class BattleTurn(BaseModel):
    """One battle turn: ordered list of actions."""

    actions: list[BattleAction]


class BattleContent(BaseModel):
    """Root ``battle:`` block in battle.yaml."""

    turns: list[BattleTurn] = Field(default_factory=list)


class BattleScript(BaseModel):
    """Parsed battle.yaml (``battle.turns``) with convenience access to turns."""

    battle: BattleContent = Field(default_factory=BattleContent)

    @property
    def turns(self) -> list[BattleTurn]:
        """Turn list from the nested ``battle`` block."""
        return self.battle.turns
