from __future__ import annotations

import queue

import customtkinter as ctk


class LogsPage(ctk.CTkFrame):
    def __init__(self, master, log_queue: queue.Queue[str], **kwargs) -> None:
        super().__init__(master, **kwargs)
        self._queue = log_queue
        self._text = ctk.CTkTextbox(self)
        self._text.pack(fill="both", expand=True, padx=12, pady=12)
        ctk.CTkLabel(
            self,
            text="Run pause 時可開啟 logs/pause_screenshot.png",
            anchor="w",
        ).pack(fill="x", padx=12, pady=(0, 8))
        self.after(200, self._poll)

    def _poll(self) -> None:
        while True:
            try:
                line = self._queue.get_nowait()
            except queue.Empty:
                break
            self._text.insert("end", line + "\n")
            self._text.see("end")
        self.after(200, self._poll)
