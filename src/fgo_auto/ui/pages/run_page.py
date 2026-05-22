from __future__ import annotations

import customtkinter as ctk

from fgo_auto.run.controller import RunOutcome


class RunPage(ctk.CTkFrame):
    def __init__(self, master, on_start, on_stop, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self._on_start = on_start
        self._on_stop = on_stop

        ctk.CTkLabel(self, text="Run 控制", font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", padx=12, pady=(12, 8)
        )
        row = ctk.CTkFrame(self)
        row.pack(fill="x", padx=12, pady=8)
        ctk.CTkButton(row, text="Start Run", command=self._start).pack(side="left", padx=(0, 8))
        ctk.CTkButton(row, text="Manual stop", fg_color="#8b3a3a", command=self._on_stop).pack(
            side="left"
        )

        self._state_lbl = ctk.CTkLabel(self, text="Screen state: —", anchor="w")
        self._state_lbl.pack(fill="x", padx=12, pady=4)
        self._loops_lbl = ctk.CTkLabel(self, text="Loops: 0", anchor="w")
        self._loops_lbl.pack(fill="x", padx=12, pady=4)
        self._outcome_lbl = ctk.CTkLabel(self, text="Outcome: —", anchor="w")
        self._outcome_lbl.pack(fill="x", padx=12, pady=4)
        self._hint = ctk.CTkLabel(self, text="", anchor="w", wraplength=700)
        self._hint.pack(fill="x", padx=12, pady=12)

    def _start(self) -> None:
        msg = self._on_start()
        if msg:
            self._hint.configure(text=msg)

    def update_status(
        self,
        *,
        screen_state: str = "",
        loops: int | None = None,
        outcome: RunOutcome | None = None,
        message: str = "",
    ) -> None:
        if screen_state:
            self._state_lbl.configure(text=f"Screen state: {screen_state}")
        if loops is not None:
            self._loops_lbl.configure(text=f"Loops: {loops}")
        if outcome is not None:
            label = {
                RunOutcome.NORMAL_END: "Normal Run end",
                RunOutcome.PAUSED: "Run pause",
                RunOutcome.RUNNING: "Running",
            }.get(outcome, outcome.value)
            self._outcome_lbl.configure(text=f"Outcome: {label}")
        if message:
            self._hint.configure(text=message)
