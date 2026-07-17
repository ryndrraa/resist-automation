from __future__ import annotations

from collections import Counter

import customtkinter as ctk

from ..models import ProjectSession


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(tuple(range(6)), weight=1)
        self._values: dict[str, ctk.CTkLabel] = {}
        cards = (
            ("total", "Total", "#2563EB"),
            ("Lengkap", "Lengkap", "#16A34A"),
            ("Sebagian", "Sebagian", "#CA8A04"),
            ("Siap diisi", "Siap Diisi", "#64748B"),
            ("Belum dipetakan", "Belum Dipetakan", "#475569"),
            ("Error", "Error", "#DC2626"),
        )
        for column, (key, title, color) in enumerate(cards):
            card = ctk.CTkFrame(self, corner_radius=10, border_width=1, border_color="#D8DEE9")
            card.grid(row=0, column=column, padx=4, pady=2, sticky="nsew")
            ctk.CTkLabel(card, text=title, text_color="#64748B", font=ctk.CTkFont(size=12)).pack(
                pady=(8, 0)
            )
            value = ctk.CTkLabel(
                card,
                text="0",
                text_color=color,
                font=ctk.CTkFont(size=23, weight="bold"),
            )
            value.pack(pady=(0, 8))
            self._values[key] = value

    def update_project(self, project: ProjectSession | None) -> None:
        counts = Counter(scenario.status for scenario in project.scenarios) if project else Counter()
        self._values["total"].configure(text=str(len(project.scenarios) if project else 0))
        for key in ("Lengkap", "Sebagian", "Siap diisi", "Belum dipetakan", "Error"):
            value = counts[key]
            if key == "Lengkap":
                value += counts["Sudah diekspor"]
            self._values[key].configure(text=str(value))
