from __future__ import annotations

import json
from tkinter import messagebox

import customtkinter as ctk

from ..models import Scenario
from ..rsx.parser import parse_rsx


class RSXDetailDialog(ctk.CTkToplevel):
    def __init__(self, master: ctk.CTkBaseClass, scenario: Scenario) -> None:
        super().__init__(master)
        self.title(f"Detail RSX — {scenario.source_path.name}")
        self.geometry("820x650")
        self.transient(master)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            self,
            text=scenario.source_path.name,
            font=ctk.CTkFont(size=19, weight="bold"),
        ).grid(row=0, column=0, pady=(16, 8))
        textbox = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=12), wrap="none")
        textbox.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 10))
        try:
            parsed = parse_rsx(scenario.source_path)
            payload = parsed.model_dump(mode="json")
            payload["mapping"] = {
                "target_sheet": scenario.target_sheet,
                "target_row": scenario.target_row,
                "status": scenario.status,
                "notes": scenario.notes,
            }
            textbox.insert("1.0", json.dumps(payload, indent=2, ensure_ascii=False))
        except Exception as exc:
            textbox.insert("1.0", f"Detail tidak dapat dimuat:\n{exc}")
            messagebox.showerror("Gagal membaca RSX", str(exc), parent=self)
        textbox.configure(state="disabled")
        ctk.CTkButton(self, text="Tutup", command=self.destroy, width=100).grid(row=2, column=0, pady=(0, 14))
