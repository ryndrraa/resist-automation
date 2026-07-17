from __future__ import annotations

import os
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from ..rsx.mapper import ids_from_filename
from ..rsx.parser import parse_rsx
from ..rsx.writer import generate_rsx_batch


class GeneratorDialog(ctk.CTkToplevel):
    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master)
        self.title("Generator Variasi RSX Aman")
        self.geometry("820x680")
        self.transient(master)
        self.grab_set()
        self.grid_columnconfigure(0, weight=1)
        self.source_var = ctk.StringVar()
        self.output_var = ctk.StringVar()
        self.id_x_var = ctk.StringVar()
        self.id_y_var = ctk.StringVar()
        self.depth_x_var = ctk.StringVar(value="0.1")
        self.depth_y_var = ctk.StringVar(value="0.1")
        self.modeller_var = ctk.StringVar()
        self.project_var = ctk.StringVar()
        self.pga_04 = ctk.BooleanVar(value=True)
        self.pga_05 = ctk.BooleanVar(value=True)

        ctk.CTkLabel(
            self,
            text="Generator Variasi RSX",
            font=ctk.CTkFont(size=21, weight="bold"),
        ).grid(row=0, column=0, pady=(18, 2))
        ctk.CTkLabel(
            self,
            text="Hanya Earthquake.zone_factor, Braces.depth, dan metadata aman yang diubah.",
            text_color="#64748B",
        ).grid(row=1, column=0, pady=(0, 12))

        form = ctk.CTkScrollableFrame(self)
        form.grid(row=2, column=0, sticky="nsew", padx=20, pady=5)
        form.grid_columnconfigure(1, weight=1)
        self._path_row(form, 0, "RSX dasar", self.source_var, self._choose_source)
        self._path_row(form, 1, "Folder output", self.output_var, self._choose_output)

        ctk.CTkLabel(form, text="PGA", anchor="w").grid(row=2, column=0, padx=10, pady=8, sticky="w")
        pga_frame = ctk.CTkFrame(form, fg_color="transparent")
        pga_frame.grid(row=2, column=1, sticky="w")
        ctk.CTkCheckBox(pga_frame, text="0,4", variable=self.pga_04).pack(side="left", padx=5)
        ctk.CTkCheckBox(pga_frame, text="0,5", variable=self.pga_05).pack(side="left", padx=5)

        self._entry_row(form, 3, "ID struktur X", self.id_x_var, "contoh: BFCTST")
        self._entry_row(form, 4, "ID struktur Y", self.id_y_var, "contoh: BFCTST")
        self._entry_row(form, 5, "Depth X (meter)", self.depth_x_var, "pisahkan dengan koma: 0.1, 0.2")
        self._entry_row(form, 6, "Depth Y (meter)", self.depth_y_var, "pisahkan dengan koma: 0.1, 0.2")
        self._entry_row(form, 7, "Modeller (opsional)", self.modeller_var, "metadata modeller")
        self._entry_row(form, 8, "Project (opsional)", self.project_var, "metadata project")
        ctk.CTkLabel(
            form,
            text=(
                "Penting: ID X/Y hanya dipakai untuk penamaan file. Generator tidak mengganti class, "
                "bracing type, layout, beban, soil, atau importance category. Gunakan RSX dasar yang "
                "memang memiliki struktur tersebut."
            ),
            wraplength=690,
            justify="left",
            text_color="#B45309",
        ).grid(row=9, column=0, columnspan=3, padx=10, pady=14, sticky="w")

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=3, column=0, pady=16)
        ctk.CTkButton(buttons, text="Generate", command=self._generate, width=120).pack(side="left", padx=6)
        ctk.CTkButton(
            buttons,
            text="Buka Folder",
            command=self._open_output,
            fg_color="#0F766E",
            hover_color="#115E59",
            width=120,
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            buttons,
            text="Tutup",
            command=self.destroy,
            fg_color="#64748B",
            hover_color="#475569",
            width=100,
        ).pack(side="left", padx=6)

    @staticmethod
    def _path_row(
        parent: ctk.CTkFrame,
        row: int,
        label: str,
        variable: ctk.StringVar,
        command: object,
    ) -> None:
        ctk.CTkLabel(parent, text=label, anchor="w").grid(row=row, column=0, padx=10, pady=8, sticky="w")
        ctk.CTkEntry(parent, textvariable=variable).grid(row=row, column=1, padx=8, pady=8, sticky="ew")
        ctk.CTkButton(parent, text="Pilih", command=command, width=70).grid(row=row, column=2, padx=8, pady=8)

    @staticmethod
    def _entry_row(
        parent: ctk.CTkFrame,
        row: int,
        label: str,
        variable: ctk.StringVar,
        placeholder: str,
    ) -> None:
        ctk.CTkLabel(parent, text=label, anchor="w").grid(row=row, column=0, padx=10, pady=8, sticky="w")
        ctk.CTkEntry(parent, textvariable=variable, placeholder_text=placeholder).grid(
            row=row, column=1, columnspan=2, padx=8, pady=8, sticky="ew"
        )

    def _choose_source(self) -> None:
        value = filedialog.askopenfilename(parent=self, filetypes=[("RESIST project", "*.rsx")])
        if not value:
            return
        self.source_var.set(value)
        if not self.output_var.get():
            self.output_var.set(str(Path(value).parent / "generated"))
        try:
            parsed = parse_rsx(Path(value))
            mapping = ids_from_filename(Path(value).name)
            if mapping:
                self.id_x_var.set(mapping[1])
                self.id_y_var.set(mapping[2])
            self.depth_x_var.set(str(parsed.structures["x"].depth_m or 0.1))
            self.depth_y_var.set(str(parsed.structures["y"].depth_m or 0.1))
            self.modeller_var.set(parsed.metadata.modeller or "")
            self.project_var.set(parsed.metadata.project or "")
        except Exception as exc:
            messagebox.showerror("RSX tidak valid", str(exc), parent=self)

    def _choose_output(self) -> None:
        value = filedialog.askdirectory(parent=self)
        if value:
            self.output_var.set(value)

    @staticmethod
    def _numbers(raw: str, label: str) -> list[float]:
        try:
            values = [float(part.strip().replace(",", ".")) for part in raw.replace(";", " ").split()]
        except ValueError:
            # Untuk daftar desimal, gunakan titik dan pemisah koma/semicolon. Normalisasi manual.
            try:
                values = [float(part.strip()) for part in raw.replace(";", ",").split(",") if part.strip()]
            except ValueError as exc:
                raise ValueError(f"{label} harus berupa daftar angka, misalnya 0.1, 0.2.") from exc
        if not values or any(value < 0 for value in values):
            raise ValueError(f"{label} wajib berisi angka non-negatif.")
        return values

    def _generate(self) -> None:
        try:
            pgas = [value for selected, value in ((self.pga_04.get(), 0.4), (self.pga_05.get(), 0.5)) if selected]
            depth_x = self._parse_depth_list(self.depth_x_var.get(), "Depth X")
            depth_y = self._parse_depth_list(self.depth_y_var.get(), "Depth Y")
            generated = generate_rsx_batch(
                Path(self.source_var.get()),
                Path(self.output_var.get()),
                pga_values=pgas,
                depth_x_values_m=depth_x,
                depth_y_values_m=depth_y,
                structure_x_id=self.id_x_var.get(),
                structure_y_id=self.id_y_var.get(),
                modeller=self.modeller_var.get(),
                project=self.project_var.get(),
            )
        except Exception as exc:
            messagebox.showerror("Generator gagal", str(exc), parent=self)
            return
        messagebox.showinfo(
            "Generator selesai",
            f"{len(generated)} file RSX berhasil dibuat dan divalidasi ulang.",
            parent=self,
        )

    @staticmethod
    def _parse_depth_list(raw: str, label: str) -> list[float]:
        # Koma desimal tunggal (0,1) diterima; daftar dianjurkan menggunakan titik dan koma pemisah.
        raw = raw.strip()
        if not raw:
            raise ValueError(f"{label} wajib diisi.")
        if ";" in raw:
            parts = raw.split(";")
        elif raw.count(",") == 1 and "." not in raw:
            parts = [raw.replace(",", ".")]
        else:
            parts = raw.split(",")
        try:
            values = [float(part.strip()) for part in parts if part.strip()]
        except ValueError as exc:
            raise ValueError(f"{label} harus berupa angka, misalnya 0.1, 0.2.") from exc
        if not values or any(value < 0 for value in values):
            raise ValueError(f"{label} wajib berisi angka non-negatif.")
        return values

    def _open_output(self) -> None:
        path = Path(self.output_var.get())
        if not path.exists():
            messagebox.showwarning("Folder belum ada", "Generate file terlebih dahulu.", parent=self)
            return
        os.startfile(path)  # type: ignore[attr-defined]
