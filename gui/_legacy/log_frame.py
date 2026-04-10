"""Log Frame — Real-time log viewer with filtering and export."""
import customtkinter as ctk
import os
import time
from gui.theme import Colors, Fonts, styled_button, styled_card, styled_label


class LogFrame(ctk.CTkFrame):
    """Full-screen log viewer with severity filtering and export capabilities."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._all_logs: list[str] = []
        self._filter = "all"
        self._build_ui()

    def _build_ui(self):
        # ── Header ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 12))

        styled_label(
            header, text="Logs",
            font=Fonts.heading_xl(), color=Colors.PRIMARY
        ).pack(side="left")

        # Log count badge
        self.count_badge = ctk.CTkFrame(header, fg_color=Colors.BG_ELEVATED,
                                         corner_radius=6)
        self.count_badge.pack(side="left", padx=12)
        self.count_label = styled_label(
            self.count_badge, text="0 entries",
            font=Fonts.badge(), color=Colors.TEXT_MUTED
        )
        self.count_label.pack(padx=8, pady=3)

        # ── Toolbar ──
        toolbar = styled_card(self)
        toolbar.pack(fill="x", pady=(0, 8))

        tb_inner = ctk.CTkFrame(toolbar, fg_color="transparent")
        tb_inner.pack(fill="x", padx=12, pady=8)

        # Filter buttons
        styled_label(
            tb_inner, text="Filter:", font=Fonts.body_sm(),
            color=Colors.TEXT_MUTED
        ).pack(side="left", padx=(0, 8))

        filters = [
            ("All", "all", Colors.TEXT_SECONDARY),
            ("✓ Success", "success", Colors.SUCCESS),
            ("⚠ Warning", "warning", Colors.WARNING),
            ("✗ Error", "error", Colors.DANGER),
            ("ADB", "adb", Colors.CYAN),
            ("QEMU", "qemu", Colors.INFO),
        ]

        for label, key, color in filters:
            btn = ctk.CTkButton(
                tb_inner, text=label, width=70, height=26,
                fg_color=Colors.BG_ELEVATED if key != "all" else Colors.BG_HOVER,
                hover_color=Colors.BG_HOVER,
                font=Fonts.body_sm(), text_color=color,
                corner_radius=6,
                command=lambda k=key: self._set_filter(k)
            )
            btn.pack(side="left", padx=2)

        # Right-side actions
        styled_button(
            tb_inner, "Export", self._export_logs,
            color=Colors.BG_ELEVATED, width=70, height=26
        ).pack(side="right", padx=(4, 0))

        styled_button(
            tb_inner, "Clear", self._clear_logs,
            color=Colors.BG_ELEVATED, width=60, height=26
        ).pack(side="right", padx=(4, 0))

        # ── Log Area ──
        self.log_box = ctk.CTkTextbox(
            self, fg_color=Colors.BG_INPUT,
            text_color=Colors.TEXT_LOG,
            font=Fonts.mono(),
            corner_radius=8,
            border_width=1,
            border_color=Colors.BORDER,
        )
        self.log_box.pack(fill="both", expand=True)
        self.log_box.configure(state="disabled")

        # Welcome message
        self._append_raw("═" * 50)
        self._append_raw("  APK-Lator Log Viewer")
        self._append_raw("  Logs from QEMU, ADB, and system operations")
        self._append_raw("  appear here in real-time.")
        self._append_raw("═" * 50)

    # ── Public API ──

    def append_log(self, message: str):
        """Add a log entry (called from other frames)."""
        timestamp = time.strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        self._all_logs.append(entry)
        self._update_count()

        if self._should_show(entry):
            self._append_raw(entry)

    # ── Filtering ──

    def _set_filter(self, filter_key: str):
        self._filter = filter_key
        self._rerender_logs()

    def _should_show(self, entry: str) -> bool:
        if self._filter == "all":
            return True
        lower = entry.lower()
        if self._filter == "success":
            return "✓" in entry or "success" in lower
        if self._filter == "warning":
            return "⚠" in entry or "warning" in lower or "warn" in lower
        if self._filter == "error":
            return "✗" in entry or "error" in lower or "fail" in lower
        if self._filter == "adb":
            return "[adb]" in lower
        if self._filter == "qemu":
            return "qemu" in lower or "[disk]" in lower
        return True

    def _rerender_logs(self):
        """Re-render the log box with current filter applied."""
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        for entry in self._all_logs:
            if self._should_show(entry):
                self.log_box.insert("end", entry + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    # ── Actions ──

    def _clear_logs(self):
        self._all_logs.clear()
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        self._update_count()

    def _export_logs(self):
        """Export logs to a text file."""
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            title="Export Logs",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            initialfile=f"apklator_log_{time.strftime('%Y%m%d_%H%M%S')}.txt"
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write("\n".join(self._all_logs))
                self.append_log(f"✓ Logs exported to {path}")
            except IOError as e:
                self.append_log(f"✗ Export failed: {e}")

    # ── Internal ──

    def _append_raw(self, text: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _update_count(self):
        self.count_label.configure(text=f"{len(self._all_logs)} entries")
