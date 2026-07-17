from __future__ import annotations

from collections.abc import Callable
from tkinter import messagebox, ttk

import customtkinter as ctk

from ..models import MappingEntry, Scenario


class MappingDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        scenario: Scenario,
        entries: list[MappingEntry],
        on_apply: Callable[[MappingEntry], None],
    ) -> None:
        super().__init__(master)
        self.title(f"Ubah Mapping — {scenario.source_path.name}")
        self.geometry("650x460")
        self.transient(master)
        self.grab_set()
        self._on_apply = on_apply
        self._entries = [entry for entry in entries if abs(entry.pga - scenario.pga) < 0.0001]
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text="Pilih Mapping Workbook",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, pady=(20, 5))
        ctk.CTkLabel(
            self,
            text=f"PGA XML: {scenario.pga:g} • Mapping dibaca langsung dari kode C:E dan H:J",
            text_color="#64748B",
        ).grid(row=1, column=0, pady=(0, 12))

        frame = ctk.CTkFrame(self)
        frame.grid(row=2, column=0, sticky="nsew", padx=20)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(
            frame,
            columns=("row", "x", "y", "sheet"),
            show="headings",
            selectmode="browse",
        )
        for column, title, width in (
            ("row", "Baris", 65),
            ("x", "Struktur X", 150),
            ("y", "Struktur Y", 150),
            ("sheet", "Sheet", 130),
        ):
            self.tree.heading(column, text=title)
            self.tree.column(column, width=width, anchor="center")
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        for index, entry in enumerate(self._entries):
            iid = str(index)
            self.tree.insert("", "end", iid=iid, values=(entry.row, entry.structure_x, entry.structure_y, entry.sheet))
            if entry.row == scenario.target_row and entry.sheet == scenario.target_sheet:
                self.tree.selection_set(iid)
                self.tree.see(iid)
        self.tree.bind("<Double-1>", lambda _event: self._apply())

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=3, column=0, pady=18)
        ctk.CTkButton(buttons, text="Gunakan Mapping", command=self._apply).pack(side="left", padx=6)
        ctk.CTkButton(
            buttons,
            text="Batal",
            command=self.destroy,
            fg_color="#64748B",
            hover_color="#475569",
        ).pack(side="left", padx=6)

    def _apply(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Belum dipilih", "Pilih satu kombinasi mapping.", parent=self)
            return
        self._on_apply(self._entries[int(selection[0])])
        self.destroy()
