from __future__ import annotations

import json
from pathlib import Path
from tkinter import messagebox, ttk

import customtkinter as ctk


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, master: ctk.CTkBaseClass, mapping_path: Path) -> None:
        super().__init__(master)
        self.mapping_path = mapping_path
        self.title("Pengaturan Mapping Struktur")
        self.geometry("900x600")
        self.transient(master)
        self.grab_set()
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.mappings = self._load()

        ctk.CTkLabel(
            self,
            text="Mapping Struktur XML",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, pady=(18, 8))
        content = ctk.CTkFrame(self)
        content.grid(row=1, column=0, sticky="nsew", padx=18)
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=2)

        table_frame = ctk.CTkFrame(content, fg_color="transparent")
        table_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(
            table_frame,
            columns=("id", "class", "type"),
            show="headings",
            selectmode="browse",
        )
        for column, title, width in (
            ("id", "ID", 90),
            ("class", "Class XML", 230),
            ("type", "Bracing Type", 220),
        ):
            self.tree.heading(column, text=title)
            self.tree.column(column, width=width, anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self._select)

        form = ctk.CTkFrame(content)
        form.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        self.id_entry = self._field(form, "Structure ID", 0)
        self.class_entry = self._field(form, "Class XML", 1)
        self.type_entry = self._field(form, "Bracing Type", 2)
        ctk.CTkButton(form, text="Tambah / Perbarui", command=self._upsert).grid(
            row=6, column=0, padx=12, pady=(18, 6), sticky="ew"
        )
        ctk.CTkButton(
            form,
            text="Hapus Terpilih",
            command=self._delete,
            fg_color="#DC2626",
            hover_color="#B91C1C",
        ).grid(row=7, column=0, padx=12, pady=6, sticky="ew")
        ctk.CTkLabel(
            form,
            text="Tambahkan hanya mapping yang sudah Anda verifikasi dari model RESIST.",
            wraplength=260,
            text_color="#64748B",
        ).grid(row=8, column=0, padx=12, pady=18)

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=2, column=0, pady=16)
        ctk.CTkButton(buttons, text="Simpan", command=self._save).pack(side="left", padx=6)
        ctk.CTkButton(
            buttons,
            text="Batal",
            command=self.destroy,
            fg_color="#64748B",
            hover_color="#475569",
        ).pack(side="left", padx=6)
        self._render()

    @staticmethod
    def _field(parent: ctk.CTkFrame, label: str, index: int) -> ctk.CTkEntry:
        ctk.CTkLabel(parent, text=label, anchor="w").grid(
            row=index * 2, column=0, padx=12, pady=(12 if index == 0 else 8, 2), sticky="ew"
        )
        entry = ctk.CTkEntry(parent)
        entry.grid(row=index * 2 + 1, column=0, padx=12, sticky="ew")
        return entry

    def _load(self) -> list[dict[str, str]]:
        try:
            payload = json.loads(self.mapping_path.read_text(encoding="utf-8"))
            return [dict(item) for item in payload.get("mappings", [])]
        except Exception:
            return []

    def _render(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for index, mapping in enumerate(self.mappings):
            self.tree.insert(
                "",
                "end",
                iid=str(index),
                values=(mapping.get("structure_id", ""), mapping.get("class", ""), mapping.get("bracing_type", "")),
            )

    def _select(self, _event: object) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        mapping = self.mappings[int(selection[0])]
        for entry, key in (
            (self.id_entry, "structure_id"),
            (self.class_entry, "class"),
            (self.type_entry, "bracing_type"),
        ):
            entry.delete(0, "end")
            entry.insert(0, mapping.get(key, ""))

    def _upsert(self) -> None:
        mapping = {
            "structure_id": self.id_entry.get().strip().upper(),
            "class": self.class_entry.get().strip(),
            "bracing_type": self.type_entry.get().strip(),
        }
        if not all(mapping.values()):
            messagebox.showwarning("Data belum lengkap", "ID, class, dan bracing type wajib diisi.", parent=self)
            return
        selection = self.tree.selection()
        if selection:
            self.mappings[int(selection[0])] = mapping
        else:
            duplicate = next(
                (item for item in self.mappings if item.get("structure_id") == mapping["structure_id"]),
                None,
            )
            if duplicate:
                messagebox.showwarning("ID duplikat", "Structure ID sudah tersedia.", parent=self)
                return
            self.mappings.append(mapping)
        self._render()

    def _delete(self) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        del self.mappings[int(selection[0])]
        self._render()

    def _save(self) -> None:
        self.mapping_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": 1, "mappings": self.mappings}
        self.mapping_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        messagebox.showinfo("Tersimpan", "Mapping struktur berhasil disimpan.", parent=self)
        self.destroy()
