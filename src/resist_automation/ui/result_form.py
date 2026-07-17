from __future__ import annotations

from collections.abc import Callable
from tkinter import messagebox

import customtkinter as ctk
from pydantic import ValidationError

from ..models import AxisResult, Scenario


SaveCallback = Callable[[AxisResult, AxisResult, bool], None]


class ResultFormDialog(ctk.CTkToplevel):
    FIELDS = (
        ("drift_ultimate", "Drift Ultimate"),
        ("braced_ultimate", "Braced Ultimate"),
        ("drift_service", "Drift Service"),
        ("braced_service", "Braced Service"),
    )

    def __init__(self, master: ctk.CTkBaseClass, scenario: Scenario, on_save: SaveCallback) -> None:
        super().__init__(master)
        self.scenario = scenario
        self.on_save = on_save
        self.title(f"Input Hasil — {scenario.source_path.name}")
        self.geometry("700x470")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(
            self,
            text="Input Hasil Analisis RESIST",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, columnspan=2, pady=(20, 4))
        ctk.CTkLabel(
            self,
            text="Masukkan angka persen seperti 38, bukan 0.38. Nilai ini tidak dihitung aplikasi.",
            text_color="#64748B",
        ).grid(row=1, column=0, columnspan=2, pady=(0, 16))

        self.entries: dict[tuple[str, str], ctk.CTkEntry] = {}
        for column, (axis, result) in enumerate((("x", scenario.result_x), ("y", scenario.result_y))):
            frame = ctk.CTkFrame(self)
            frame.grid(row=2, column=column, padx=(20 if column == 0 else 8, 20 if column == 1 else 8), sticky="nsew")
            ctk.CTkLabel(
                frame,
                text=f"Sumbu {axis.upper()}",
                font=ctk.CTkFont(size=16, weight="bold"),
            ).pack(pady=(14, 10))
            for field_name, label in self.FIELDS:
                row = ctk.CTkFrame(frame, fg_color="transparent")
                row.pack(fill="x", padx=14, pady=5)
                ctk.CTkLabel(row, text=label, width=135, anchor="w").pack(side="left")
                entry = ctk.CTkEntry(row, width=110, placeholder_text="Kosong")
                entry.pack(side="left", padx=5)
                ctk.CTkLabel(row, text="%").pack(side="left")
                value = getattr(result, field_name)
                if value is not None:
                    entry.insert(0, f"{value:g}")
                self.entries[(axis, field_name)] = entry

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=3, column=0, columnspan=2, pady=20)
        ctk.CTkButton(buttons, text="Simpan", command=lambda: self._save(False), width=105).pack(
            side="left", padx=5
        )
        ctk.CTkButton(
            buttons,
            text="Simpan & Berikutnya",
            command=lambda: self._save(True),
            width=150,
        ).pack(side="left", padx=5)
        ctk.CTkButton(
            buttons,
            text="Kosongkan",
            fg_color="#D97706",
            hover_color="#B45309",
            command=self._clear,
            width=105,
        ).pack(side="left", padx=5)
        ctk.CTkButton(
            buttons,
            text="Batal",
            fg_color="#64748B",
            hover_color="#475569",
            command=self.destroy,
            width=90,
        ).pack(side="left", padx=5)

    def _axis_result(self, axis: str) -> AxisResult:
        values: dict[str, float | None] = {}
        for field_name, _label in self.FIELDS:
            raw = self.entries[(axis, field_name)].get().strip().replace(",", ".")
            if not raw:
                values[field_name] = None
                continue
            try:
                values[field_name] = float(raw)
            except ValueError as exc:
                raise ValueError(f"{field_name.replace('_', ' ').title()} sumbu {axis.upper()} bukan angka.") from exc
        return AxisResult(**values)

    def _save(self, move_next: bool) -> None:
        try:
            result_x = self._axis_result("x")
            result_y = self._axis_result("y")
        except (ValueError, ValidationError) as exc:
            messagebox.showerror("Nilai tidak valid", str(exc), parent=self)
            return
        values = [
            value
            for result in (result_x, result_y)
            for value in result.model_dump().values()
            if value is not None
        ]
        if any(value > 100 for value in values) and not messagebox.askyesno(
            "Konfirmasi nilai",
            "Ada nilai di atas 100. Apakah angka tersebut sudah benar?",
            parent=self,
        ):
            return
        self.on_save(result_x, result_y, move_next)
        self.destroy()

    def _clear(self) -> None:
        if not messagebox.askyesno("Kosongkan hasil", "Kosongkan seluruh delapan nilai?", parent=self):
            return
        for entry in self.entries.values():
            entry.delete(0, "end")
