from __future__ import annotations

import tkinter as tk


class HoverTooltip:
    """Show a small tooltip after the pointer rests on a widget."""

    def __init__(self, widget: tk.Misc, text: str, *, delay_ms: int = 350) -> None:
        self._widget = widget
        self._text = text
        self._delay_ms = delay_ms
        self._tip: tk.Toplevel | None = None
        self._after_id: str | None = None
        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")

    def _on_enter(self, _event: tk.Event | None = None) -> None:
        self._cancel()
        self._after_id = self._widget.after(self._delay_ms, self._show)

    def _on_leave(self, _event: tk.Event | None = None) -> None:
        self._cancel()
        self._hide()

    def _cancel(self) -> None:
        if self._after_id is not None:
            self._widget.after_cancel(self._after_id)
            self._after_id = None

    def _show(self) -> None:
        self._after_id = None
        if self._tip is not None:
            return
        x = self._widget.winfo_rootx() + 24
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 4
        tip = tk.Toplevel(self._widget)
        tip.wm_overrideredirect(True)
        tip.wm_geometry(f"+{x}+{y}")
        lbl = tk.Label(
            tip,
            text=self._text,
            justify="left",
            background="#ffffe0",
            foreground="#111111",
            relief="solid",
            borderwidth=1,
            font=("Microsoft YaHei UI", 9),
            padx=8,
            pady=6,
            wraplength=420,
        )
        lbl.pack()
        self._tip = tip

    def _hide(self) -> None:
        if self._tip is not None:
            self._tip.destroy()
            self._tip = None
