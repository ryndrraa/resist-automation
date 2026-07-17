from __future__ import annotations

from collections.abc import Callable
from tkinter import Menu, ttk

import customtkinter as ctk

from ..models import Scenario


ActionCallback = Callable[[str, Scenario | None], None]


class ScenarioTable(ctk.CTkFrame):
    COLUMNS = (
        "no",
        "file",
        "pga",
        "x",
        "dx",
        "y",
        "dy",
        "sheet",
        "row",
        "result_x",
        "result_y",
        "status",
    )

    def __init__(self, master: ctk.CTkBaseClass, on_action: ActionCallback) -> None:
        super().__init__(master, corner_radius=10)
        self._on_action = on_action
        self._scenarios: list[Scenario] = []
        self._visible: dict[str, Scenario] = {}
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(9, 5))
        search_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(search_frame, text="Cari skenario:").grid(row=0, column=0, padx=(0, 8))
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._render())
        ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text="Nama file, struktur, PGA, atau status...",
        ).grid(row=0, column=1, sticky="ew")

        table_frame = ctk.CTkFrame(self, fg_color="transparent")
        table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        style.configure("RESIST.Treeview", rowheight=28, font=("Segoe UI", 9))
        style.configure("RESIST.Treeview.Heading", font=("Segoe UI", 9, "bold"))
        self.tree = ttk.Treeview(
            table_frame,
            columns=self.COLUMNS,
            show="headings",
            style="RESIST.Treeview",
            selectmode="browse",
        )
        headings = {
            "no": "No",
            "file": "Nama file",
            "pga": "PGA",
            "x": "Struktur X",
            "dx": "Dim X",
            "y": "Struktur Y",
            "dy": "Dim Y",
            "sheet": "Target sheet",
            "row": "Baris",
            "result_x": "Hasil X",
            "result_y": "Hasil Y",
            "status": "Status",
        }
        widths = {
            "no": 42,
            "file": 210,
            "pga": 52,
            "x": 85,
            "dx": 60,
            "y": 85,
            "dy": 60,
            "sheet": 90,
            "row": 48,
            "result_x": 60,
            "result_y": 60,
            "status": 115,
        }
        for column in self.COLUMNS:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], minwidth=40, anchor="center")
        self.tree.column("file", anchor="w")
        self.tree.column("status", anchor="w")
        self.tree.tag_configure("complete", background="#DCFCE7", foreground="#14532D")
        self.tree.tag_configure("partial", background="#FEF9C3", foreground="#713F12")
        self.tree.tag_configure("unmapped", background="#F1F5F9", foreground="#334155")
        self.tree.tag_configure("error", background="#FEE2E2", foreground="#7F1D1D")
        self.tree.tag_configure("exported", background="#DBEAFE", foreground="#1E3A8A")
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        self.tree.bind("<<TreeviewSelect>>", self._selection_changed)
        self.tree.bind("<Double-1>", lambda _event: self._on_action("results", self.selected()))
        self.tree.bind("<Button-3>", self._show_context_menu)

        self.menu = Menu(self, tearoff=False)
        self.menu.add_command(label="Input/Edit Hasil", command=lambda: self._menu_action("results"))
        self.menu.add_command(label="Ubah Mapping", command=lambda: self._menu_action("mapping"))
        self.menu.add_command(label="Lihat Detail RSX", command=lambda: self._menu_action("detail"))
        self.menu.add_command(label="Buka Lokasi File", command=lambda: self._menu_action("location"))
        self.menu.add_separator()
        self.menu.add_command(label="Hapus dari Proyek", command=lambda: self._menu_action("remove"))

    @staticmethod
    def _status_display(status: str) -> tuple[str, str]:
        mapping = {
            "Lengkap": ("✓ Lengkap", "complete"),
            "Sebagian": ("! Sebagian", "partial"),
            "Siap diisi": ("○ Siap diisi", "unmapped"),
            "Belum dipetakan": ("? Belum dipetakan", "unmapped"),
            "Error": ("× Error", "error"),
            "Sudah diekspor": ("↗ Sudah diekspor", "exported"),
        }
        return mapping.get(status, (status, "unmapped"))

    def set_scenarios(self, scenarios: list[Scenario]) -> None:
        self._scenarios = scenarios
        self._render()

    def _render(self) -> None:
        current = self.selected()
        current_path = current.source_path if current else None
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._visible.clear()
        query = self.search_var.get().strip().casefold()
        visible_index = 0
        for source_index, scenario in enumerate(self._scenarios):
            haystack = " ".join(
                str(value or "")
                for value in (
                    scenario.source_path.name,
                    scenario.pga,
                    scenario.structure_x.structure_id,
                    scenario.structure_y.structure_id,
                    scenario.status,
                    scenario.target_sheet,
                )
            ).casefold()
            if query and query not in haystack:
                continue
            visible_index += 1
            iid = f"scenario-{source_index}"
            status_text, tag = self._status_display(scenario.status)
            values = (
                visible_index,
                scenario.source_path.name,
                f"{scenario.pga:g}",
                scenario.structure_x.structure_id or "-",
                f"{scenario.structure_x.depth_cm:g}" if scenario.structure_x.depth_cm is not None else "-",
                scenario.structure_y.structure_id or "-",
                f"{scenario.structure_y.depth_cm:g}" if scenario.structure_y.depth_cm is not None else "-",
                scenario.target_sheet or "-",
                scenario.target_row or "-",
                f"{scenario.result_x.completed_count()}/4",
                f"{scenario.result_y.completed_count()}/4",
                status_text,
            )
            self.tree.insert("", "end", iid=iid, values=values, tags=(tag,))
            self._visible[iid] = scenario
            if current_path and scenario.source_path == current_path:
                self.tree.selection_set(iid)

    def selected(self) -> Scenario | None:
        selected = self.tree.selection()
        return self._visible.get(selected[0]) if selected else None

    def selected_index(self) -> int | None:
        selected = self.selected()
        if selected is None:
            return None
        try:
            return self._scenarios.index(selected)
        except ValueError:
            return None

    def select_index(self, index: int) -> None:
        if not self._scenarios:
            return
        index = max(0, min(index, len(self._scenarios) - 1))
        target = self._scenarios[index]
        for iid, scenario in self._visible.items():
            if scenario is target:
                self.tree.selection_set(iid)
                self.tree.focus(iid)
                self.tree.see(iid)
                self._on_action("select", target)
                return

    def _selection_changed(self, _event: object) -> None:
        self._on_action("select", self.selected())

    def _show_context_menu(self, event: object) -> None:
        row = self.tree.identify_row(event.y)  # type: ignore[attr-defined]
        if row:
            self.tree.selection_set(row)
            self.menu.tk_popup(event.x_root, event.y_root)  # type: ignore[attr-defined]

    def _menu_action(self, action: str) -> None:
        self._on_action(action, self.selected())
