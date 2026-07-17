from __future__ import annotations

import os
from concurrent.futures import Future
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog

import customtkinter as ctk

from ..constants import (
    DEFAULT_STRUCTURE_MAPPING,
    RUNTIME_DATA_ROOT,
    ensure_runtime_directories,
)
from ..excel.importer import import_results_from_workbook
from ..excel.reader import read_workbook_mapping
from ..excel.validator import validate_workbook
from ..models import AxisResult, MappingEntry, ProjectSession, Scenario
from ..project.autosave import SessionAutosaver
from ..project.service import ProjectService
from ..rsx.mapper import scenario_from_parsed
from ..services.export_service import ExportService
from ..services.import_service import ImportReport
from ..services.recap_service import export_recap
from .dashboard_frame import DashboardFrame
from .generator_dialog import GeneratorDialog
from .mapping_dialog import MappingDialog
from .result_form import ResultFormDialog
from .rsx_detail_dialog import RSXDetailDialog
from .scenario_table import ScenarioTable
from .settings_dialog import SettingsDialog


class MainWindow(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        ensure_runtime_directories()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.title("RESIST Automation Desktop")
        self.geometry("1420x840")
        self.minsize(1200, 750)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.project_service = ProjectService()
        self.export_service = ExportService()
        self.project: ProjectSession | None = None
        self.project_path: Path | None = None
        self.autosaver: SessionAutosaver | None = None
        self.dirty = False
        self.last_output: Path | None = None
        self._scan_future: Future[ImportReport] | None = None

        self._build_header()
        self._build_toolbar()
        self.dashboard = DashboardFrame(self)
        self.dashboard.grid(row=2, column=0, sticky="ew", padx=14, pady=5)
        self._build_project_info()
        self._build_content()
        self._build_statusbar()
        self._refresh_all()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, corner_radius=0, fg_color="#0F172A", height=70)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header,
            text="RESIST Automation Desktop",
            text_color="white",
            font=ctk.CTkFont(size=23, weight="bold"),
        ).grid(row=0, column=0, padx=18, pady=(10, 0), sticky="w")
        ctk.CTkLabel(
            header,
            text="Kelola RSX, input hasil analisis, dan ekspor workbook dengan aman",
            text_color="#CBD5E1",
            font=ctk.CTkFont(size=12),
        ).grid(row=1, column=0, padx=18, pady=(0, 10), sticky="w")

    def _build_toolbar(self) -> None:
        toolbar = ctk.CTkFrame(self, corner_radius=0, fg_color="#E2E8F0")
        toolbar.grid(row=1, column=0, sticky="ew")
        rows = (
            (
                ("Proyek Baru", self.new_project),
                ("Buka Proyek", self.open_project),
                ("Simpan", self.save_project),
                ("Tambah RSX", self.add_rsx),
                ("Scan Folder", self.scan_folder),
                ("Input Hasil", self.edit_results),
                ("Ubah Mapping", self.change_mapping),
            ),
            (
                ("Validasi", self.validate_all),
                ("Impor Hasil", self.import_previous_results),
                ("Ekspor Excel", self.export_excel),
                ("Rekap CSV/JSON", self.export_recap_file),
                ("Generator RSX", self.open_generator),
                ("Buka Output", self.open_output_folder),
                ("Pengaturan", self.open_settings),
            ),
        )
        for row_index, buttons in enumerate(rows):
            for column, (text, command) in enumerate(buttons):
                color = "#2563EB"
                hover = "#1D4ED8"
                if text in {"Generator RSX", "Pengaturan"}:
                    color, hover = "#475569", "#334155"
                ctk.CTkButton(
                    toolbar,
                    text=text,
                    command=command,
                    width=122,
                    height=30,
                    fg_color=color,
                    hover_color=hover,
                ).grid(row=row_index, column=column, padx=5, pady=(6 if row_index == 0 else 2, 2 if row_index == 0 else 6))

    def _build_project_info(self) -> None:
        frame = ctk.CTkFrame(self, corner_radius=8)
        frame.grid(row=3, column=0, sticky="ew", padx=14, pady=5)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_columnconfigure(3, weight=1)
        ctk.CTkLabel(frame, text="Proyek:", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=(12, 5), pady=7
        )
        self.project_label = ctk.CTkLabel(frame, text="Belum ada proyek", anchor="w")
        self.project_label.grid(row=0, column=1, sticky="ew", pady=7)
        ctk.CTkLabel(frame, text="Template:", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=2, padx=(15, 5), pady=7
        )
        self.template_label = ctk.CTkLabel(frame, text="-", anchor="w")
        self.template_label.grid(row=0, column=3, sticky="ew", padx=(0, 12), pady=7)

    def _build_content(self) -> None:
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=4, column=0, sticky="nsew", padx=14, pady=4)
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=5)
        content.grid_columnconfigure(1, weight=1)
        self.table = ScenarioTable(content, self._table_action)
        self.table.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        detail = ctk.CTkFrame(content, corner_radius=10)
        detail.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        detail.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            detail,
            text="Detail Skenario",
            font=ctk.CTkFont(size=17, weight="bold"),
        ).grid(row=0, column=0, padx=12, pady=(15, 8))
        self.detail_text = ctk.CTkTextbox(detail, height=320, wrap="word")
        self.detail_text.grid(row=1, column=0, padx=12, pady=5, sticky="nsew")
        self.detail_text.configure(state="disabled")
        detail.grid_rowconfigure(1, weight=1)
        ctk.CTkButton(detail, text="Input/Edit Hasil", command=self.edit_results).grid(
            row=2, column=0, padx=12, pady=(12, 4), sticky="ew"
        )
        ctk.CTkButton(
            detail,
            text="Ubah Mapping",
            command=self.change_mapping,
            fg_color="#0F766E",
            hover_color="#115E59",
        ).grid(row=3, column=0, padx=12, pady=4, sticky="ew")
        ctk.CTkButton(
            detail,
            text="Lihat Detail RSX",
            command=lambda: self._show_detail(self.table.selected()),
            fg_color="#475569",
            hover_color="#334155",
        ).grid(row=4, column=0, padx=12, pady=(4, 12), sticky="ew")

    def _build_statusbar(self) -> None:
        frame = ctk.CTkFrame(self, corner_radius=0, height=30)
        frame.grid(row=5, column=0, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)
        self.status_label = ctk.CTkLabel(frame, text="Siap", anchor="w")
        self.status_label.grid(row=0, column=0, padx=12, pady=4, sticky="ew")
        self.progress = ctk.CTkProgressBar(frame, width=180, mode="indeterminate")
        self.progress.grid(row=0, column=1, padx=12, pady=6)
        self.progress.grid_remove()

    def _set_status(self, message: str) -> None:
        self.status_label.configure(text=message)

    def _require_project(self) -> ProjectSession | None:
        if self.project is None:
            messagebox.showwarning("Belum ada proyek", "Buat atau buka proyek terlebih dahulu.", parent=self)
        return self.project

    def _selected(self) -> Scenario | None:
        scenario = self.table.selected()
        if scenario is None:
            messagebox.showwarning("Belum dipilih", "Pilih satu skenario pada tabel.", parent=self)
        return scenario

    def _refresh_all(self, *, preserve_selection: bool = True) -> None:
        self.dashboard.update_project(self.project)
        self.project_label.configure(
            text=(self.project.name + (" *" if self.dirty else "")) if self.project else "Belum ada proyek"
        )
        self.template_label.configure(text=str(self.project.template_path) if self.project else "-")
        self.table.set_scenarios(self.project.scenarios if self.project else [])
        if not preserve_selection:
            self._update_detail(None)
        else:
            self._update_detail(self.table.selected())

    def _update_detail(self, scenario: Scenario | None) -> None:
        self.detail_text.configure(state="normal")
        self.detail_text.delete("1.0", "end")
        if scenario:
            text = (
                f"File: {scenario.source_path.name}\n"
                f"PGA: {scenario.pga:g}\n\n"
                f"Struktur X: {scenario.structure_x.structure_id or '-'}\n"
                f"Dimensi X: {scenario.structure_x.depth_cm if scenario.structure_x.depth_cm is not None else '-'} cm\n"
                f"Struktur Y: {scenario.structure_y.structure_id or '-'}\n"
                f"Dimensi Y: {scenario.structure_y.depth_cm if scenario.structure_y.depth_cm is not None else '-'} cm\n\n"
                f"Target: {scenario.target_sheet or '-'} / baris {scenario.target_row or '-'}\n"
                f"Hasil X: {scenario.result_x.completed_count()}/4\n"
                f"Hasil Y: {scenario.result_y.completed_count()}/4\n"
                f"Status: {scenario.status}\n"
            )
            if scenario.notes:
                text += f"\nCatatan:\n{scenario.notes}"
            self.detail_text.insert("1.0", text)
        else:
            self.detail_text.insert("1.0", "Pilih skenario untuk melihat detail.")
        self.detail_text.configure(state="disabled")

    def _mark_dirty(self, message: str = "Perubahan belum disimpan") -> None:
        self.dirty = True
        if self.autosaver:
            self.autosaver.mark_dirty()
            message += " • autosave dijadwalkan"
        self._set_status(message)
        self._refresh_all()

    def _confirm_replace_project(self) -> bool:
        if not self.project or not self.dirty:
            return True
        answer = messagebox.askyesnocancel(
            "Perubahan belum disimpan",
            "Simpan perubahan proyek saat ini sebelum melanjutkan?",
            parent=self,
        )
        if answer is None:
            return False
        if answer:
            return bool(self.save_project())
        if self.autosaver:
            self.autosaver.cancel()
        return True

    def _replace_project(self, project: ProjectSession, path: Path | None) -> None:
        if self.autosaver:
            self.autosaver.cancel()
        self.project = project
        self.project_path = path
        self.dirty = False
        self.autosaver = None
        if path:
            self.autosaver = SessionAutosaver(lambda: self.project, path)  # type: ignore[arg-type,return-value]
        self._refresh_all(preserve_selection=False)

    def new_project(self) -> None:
        if not self._confirm_replace_project():
            return
        template = filedialog.askopenfilename(
            parent=self,
            title="Pilih template workbook",
            filetypes=[("Excel workbook", "*.xlsx")],
        )
        if not template:
            return
        report = validate_workbook(Path(template))
        if not report.valid:
            messagebox.showerror(
                "Template tidak valid",
                "\n".join(issue.message for issue in report.issues),
                parent=self,
            )
            return
        name = simpledialog.askstring("Nama proyek", "Masukkan nama proyek:", parent=self)
        if not name:
            return
        project = self.project_service.new_project(name.strip(), Path(template))
        self._replace_project(project, None)
        self.dirty = True
        self._set_status("Proyek baru dibuat. Simpan proyek untuk mengaktifkan autosave.")
        self._refresh_all()
        if messagebox.askyesno("Scan RSX", "Pilih dan scan folder RSX sekarang?", parent=self):
            self.scan_folder()

    def open_project(self) -> None:
        if not self._confirm_replace_project():
            return
        value = filedialog.askopenfilename(
            parent=self,
            title="Buka proyek RESIST Automation",
            initialdir=RUNTIME_DATA_ROOT / "projects",
            filetypes=[("RESIST project JSON", "*.json")],
        )
        if not value:
            return
        try:
            project = self.project_service.open(Path(value))
            read_workbook_mapping(project.template_path)
        except Exception as exc:
            messagebox.showerror("Proyek gagal dibuka", str(exc), parent=self)
            return
        self._replace_project(project, Path(value).resolve())
        self._set_status(f"Proyek dibuka: {project.name}")

    def save_project(self) -> bool:
        project = self._require_project()
        if not project:
            return False
        path = self.project_path
        if path is None:
            value = filedialog.asksaveasfilename(
                parent=self,
                title="Simpan proyek",
                initialdir=RUNTIME_DATA_ROOT / "projects",
                initialfile=f"{project.name}.json",
                defaultextension=".json",
                filetypes=[("RESIST project JSON", "*.json")],
            )
            if not value:
                return False
            path = Path(value)
        try:
            self.project_service.save(project, path)
        except Exception as exc:
            messagebox.showerror("Gagal menyimpan proyek", str(exc), parent=self)
            return False
        self.project_path = path.resolve()
        self.dirty = False
        if self.autosaver:
            self.autosaver.cancel()
        self.autosaver = SessionAutosaver(lambda: self.project, self.project_path)  # type: ignore[arg-type,return-value]
        self._set_status(f"Proyek tersimpan: {self.project_path}")
        self._refresh_all()
        return True

    def add_rsx(self) -> None:
        project = self._require_project()
        if not project:
            return
        values = filedialog.askopenfilenames(
            parent=self,
            title="Tambah file RSX",
            filetypes=[("RESIST project", "*.rsx")],
        )
        if not values:
            return
        added, failures = self.project_service.import_paths(project, [Path(value) for value in values])
        if failures:
            messagebox.showwarning(
                "Sebagian file gagal",
                "\n".join(f"{failure.path.name}: {failure.message}" for failure in failures[:10]),
                parent=self,
            )
        if added:
            self._mark_dirty(f"{len(added)} file RSX ditambahkan")

    def scan_folder(self) -> None:
        project = self._require_project()
        if not project or self._scan_future is not None:
            return
        value = filedialog.askdirectory(parent=self, title="Pilih folder RSX")
        if not value:
            return
        recursive = messagebox.askyesno(
            "Scan subfolder",
            "Sertakan semua subfolder?",
            parent=self,
        )
        folder = Path(value)
        project.rsx_folder = folder
        self.progress.grid()
        self.progress.start()
        self._set_status(f"Memindai {folder}...")
        self._scan_future = self.project_service.importer.scan_folder_async(folder, recursive=recursive)
        self.after(100, self._poll_scan)

    def _poll_scan(self) -> None:
        future = self._scan_future
        if future is None:
            return
        if not future.done():
            self.after(100, self._poll_scan)
            return
        self._scan_future = None
        self.progress.stop()
        self.progress.grid_remove()
        try:
            report = future.result()
            project = self._require_project()
            if not project:
                return
            mapping = read_workbook_mapping(project.template_path)
            known = {scenario.source_path.resolve() for scenario in project.scenarios}
            added = []
            for parsed in report.parsed:
                if parsed.source_path.resolve() not in known:
                    scenario = scenario_from_parsed(parsed, mapping)
                    project.scenarios.append(scenario)
                    known.add(parsed.source_path.resolve())
                    added.append(scenario)
            project.scenarios.sort(
                key=lambda item: (
                    item.pga,
                    item.target_row if item.target_row is not None else 999,
                    item.source_path.name.casefold(),
                )
            )
        except Exception as exc:
            messagebox.showerror("Scan gagal", str(exc), parent=self)
            return
        if report.failures:
            messagebox.showwarning(
                "Scan selesai dengan error",
                "\n".join(f"{item.path.name}: {item.message}" for item in report.failures[:10]),
                parent=self,
            )
        self._mark_dirty(f"Scan selesai: {len(added)} baru, {len(report.failures)} gagal")

    def edit_results(self) -> None:
        scenario = self._selected()
        if not scenario:
            return
        current_index = self.table.selected_index() or 0

        def save(result_x: AxisResult, result_y: AxisResult, move_next: bool) -> None:
            self.project_service.set_results(scenario, result_x, result_y)
            self._mark_dirty(f"Hasil {scenario.source_path.name} diperbarui")
            if move_next:
                self.table.select_index(current_index + 1)
                next_scenario = self.table.selected()
                if next_scenario is not None and next_scenario is not scenario:
                    self.after(100, self.edit_results)

        ResultFormDialog(self, scenario, save)

    def change_mapping(self) -> None:
        project = self._require_project()
        scenario = self._selected()
        if not project or not scenario:
            return
        try:
            entries = read_workbook_mapping(project.template_path).entries
        except Exception as exc:
            messagebox.showerror("Mapping gagal dibaca", str(exc), parent=self)
            return

        def apply(entry: MappingEntry) -> None:
            scenario.structure_x.structure_id = entry.structure_x
            scenario.structure_y.structure_id = entry.structure_y
            scenario.target_sheet = entry.sheet
            scenario.target_row = entry.row
            scenario.notes = (scenario.notes + "\n" if scenario.notes else "") + "Mapping dipilih manual oleh pengguna."
            scenario.refresh_status()
            self._mark_dirty(f"Mapping {scenario.source_path.name} diperbarui")

        MappingDialog(self, scenario, entries, apply)

    def validate_all(self) -> None:
        project = self._require_project()
        if not project:
            return
        workbook_report = validate_workbook(project.template_path)
        scenario_report = self.project_service.validator.validate_project(project)
        self._refresh_all()
        lines = [
            f"Template: {'valid' if workbook_report.valid else 'tidak valid'}",
            f"Total skenario: {len(project.scenarios)}",
        ]
        for status, count in sorted(scenario_report.counts.items()):
            lines.append(f"{status}: {count}")
        issues = workbook_report.issues + scenario_report.issues
        if issues:
            lines.append("")
            lines.extend(f"[{issue.severity}] {issue.message}" for issue in issues[:15])
            if len(issues) > 15:
                lines.append(f"... dan {len(issues) - 15} isu lainnya")
        messagebox.showinfo("Hasil validasi", "\n".join(lines), parent=self)
        self._set_status("Validasi selesai")

    def import_previous_results(self) -> None:
        project = self._require_project()
        if not project:
            return
        value = filedialog.askopenfilename(
            parent=self,
            title="Pilih workbook hasil sebelumnya",
            filetypes=[("Excel workbook", "*.xlsx")],
        )
        if not value:
            return
        try:
            imported = import_results_from_workbook(Path(value), project.scenarios)
        except Exception as exc:
            messagebox.showerror("Impor hasil gagal", str(exc), parent=self)
            return
        if imported:
            self._mark_dirty(f"Hasil dari {imported} skenario berhasil diimpor")
        messagebox.showinfo("Impor hasil", f"{imported} skenario diperbarui.", parent=self)

    def export_excel(self) -> None:
        project = self._require_project()
        if not project:
            return
        complete: list[Scenario] = []
        incomplete = 0
        high_values = False
        for scenario in project.scenarios:
            scenario.refresh_status()
            if scenario.status == "Lengkap":
                complete.append(scenario)
                values = list(scenario.result_x.model_dump().values()) + list(scenario.result_y.model_dump().values())
                high_values = high_values or any(value is not None and value > 100 for value in values)
            else:
                incomplete += 1
        if not complete:
            messagebox.showwarning("Belum dapat diekspor", "Belum ada skenario lengkap.", parent=self)
            self._refresh_all()
            return
        if incomplete and not messagebox.askyesno(
            "Skenario belum lengkap",
            f"{incomplete} skenario belum lengkap dan tidak akan ditulis. Lanjutkan {len(complete)} skenario lengkap?",
            parent=self,
        ):
            return
        confirm_high = False
        if high_values:
            confirm_high = messagebox.askyesno(
                "Konfirmasi nilai tinggi",
                "Ada hasil di atas 100. Apakah seluruh nilai tersebut sudah benar?",
                parent=self,
            )
            if not confirm_high:
                return
        default_name = f"Hasil RESIST {datetime.now():%Y-%m-%d_%H%M}.xlsx"
        value = filedialog.asksaveasfilename(
            parent=self,
            title="Simpan workbook hasil",
            initialdir=project.template_path.parent,
            initialfile=default_name,
            defaultextension=".xlsx",
            filetypes=[("Excel workbook", "*.xlsx")],
        )
        if not value:
            return
        output = Path(value)
        overwrite = False
        if output.exists():
            overwrite = messagebox.askyesno(
                "Konfirmasi overwrite",
                "File sudah ada. Buat backup lalu timpa file tersebut?",
                parent=self,
            )
            if not overwrite:
                return
        try:
            report = self.export_service.export(
                project.template_path,
                output,
                complete,
                allow_overwrite=overwrite,
                confirm_high_values=confirm_high,
                backup_directory=RUNTIME_DATA_ROOT / "backups",
            )
        except Exception as exc:
            messagebox.showerror("Ekspor gagal", str(exc), parent=self)
            return
        self.last_output = report.output_path
        self._mark_dirty(f"Ekspor selesai: {report.output_path.name}")
        details = f"{report.exported_scenarios} skenario dan {len(report.changes)} sel berhasil ditulis."
        if report.backup_path:
            details += f"\nBackup: {report.backup_path}"
        if messagebox.askyesno("Ekspor berhasil", details + "\n\nBuka folder output?", parent=self):
            os.startfile(report.output_path.parent)  # type: ignore[attr-defined]

    def export_recap_file(self) -> None:
        project = self._require_project()
        if not project:
            return
        value = filedialog.asksaveasfilename(
            parent=self,
            title="Simpan rekap",
            initialfile=f"rekap-{project.name}.csv",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("JSON", "*.json")],
        )
        if not value:
            return
        try:
            path = export_recap(Path(value), project.scenarios)
        except Exception as exc:
            messagebox.showerror("Rekap gagal", str(exc), parent=self)
            return
        self._set_status(f"Rekap tersimpan: {path}")
        messagebox.showinfo("Rekap berhasil", str(path), parent=self)

    def open_generator(self) -> None:
        GeneratorDialog(self)

    def open_settings(self) -> None:
        SettingsDialog(self, DEFAULT_STRUCTURE_MAPPING)

    def open_output_folder(self) -> None:
        if not self.last_output or not self.last_output.parent.exists():
            messagebox.showwarning("Belum ada output", "Belum ada folder output dari sesi ini.", parent=self)
            return
        os.startfile(self.last_output.parent)  # type: ignore[attr-defined]

    def _show_detail(self, scenario: Scenario | None) -> None:
        if scenario is None:
            messagebox.showwarning("Belum dipilih", "Pilih satu skenario.", parent=self)
            return
        RSXDetailDialog(self, scenario)

    def _table_action(self, action: str, scenario: Scenario | None) -> None:
        if action == "select":
            self._update_detail(scenario)
        elif action == "results":
            self.edit_results()
        elif action == "mapping":
            self.change_mapping()
        elif action == "detail":
            self._show_detail(scenario)
        elif action == "location" and scenario:
            os.startfile(scenario.source_path.parent)  # type: ignore[attr-defined]
        elif action == "remove" and scenario and self.project:
            if messagebox.askyesno(
                "Hapus skenario",
                f"Hapus {scenario.source_path.name} dari proyek? File RSX tidak akan dihapus.",
                parent=self,
            ):
                self.project.scenarios.remove(scenario)
                self._mark_dirty("Skenario dihapus dari proyek")

    def _on_close(self) -> None:
        if self.dirty:
            answer = messagebox.askyesnocancel(
                "Tutup aplikasi",
                "Simpan perubahan sebelum keluar?",
                parent=self,
            )
            if answer is None:
                return
            if answer and not self.save_project():
                return
            if not answer and self.autosaver:
                self.autosaver.cancel()
        elif self.autosaver:
            self.autosaver.cancel()
        self.project_service.importer.close()
        self.destroy()


def run_gui() -> None:
    app = MainWindow()
    app.mainloop()
