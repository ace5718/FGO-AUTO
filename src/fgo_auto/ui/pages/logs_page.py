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
            text="執行中的畫面狀態與錯誤會顯示於此；暫停時另開 logs/pause_screenshot.png",
            anchor="w",
            wraplength=900,
        ).pack(fill="x", padx=12, pady=(0, 8))
        self.after(200, self._poll)

    def append_line(self, line: str) -> None:
        self._text.insert("end", line + "\n")
        self._text.see("end")

    def _poll(self) -> None:
        while True:
            try:
                line = self._queue.get_nowait()
            except queue.Empty:
                break
            self.append_line(line)
        self.after(200, self._poll)
