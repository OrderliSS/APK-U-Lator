"""APK Installer Frame — browse, queue, and install APK files via ADB."""
import customtkinter as ctk
from tkinter import filedialog
import threading
import os
from gui.theme import Colors, Fonts, styled_button, styled_card, styled_label


class ApkInstallerFrame(ctk.CTkFrame):
    """APK installation interface with file browser and install queue."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.adb = None  # Set externally by app.py after init
        self.apk_paths: list[str] = []
        self._build_ui()

    def _build_ui(self):
        # ── Header ──
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 16))

        styled_label(
            header_frame, text="APK Installer",
            font=Fonts.heading_xl(), color=Colors.PRIMARY
        ).pack(side="left")

        # Package count badge
        self.pkg_badge = ctk.CTkFrame(header_frame, fg_color=Colors.BG_ELEVATED,
                                       corner_radius=6)
        self.pkg_badge.pack(side="right")
        self.pkg_count_label = styled_label(
            self.pkg_badge, text="0 queued",
            font=Fonts.badge(), color=Colors.TEXT_MUTED
        )
        self.pkg_count_label.pack(padx=8, pady=3)

        # ── Drop Zone / Browse Area ──
        drop_zone = styled_card(self, height=160)
        drop_zone.pack(fill="x", pady=(0, 16))
        drop_zone.pack_propagate(False)

        inner = ctk.CTkFrame(drop_zone, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        styled_label(
            inner, text="📦",
            font=ctk.CTkFont(size=42), color=Colors.TEXT_PRIMARY
        ).pack(pady=(0, 4))

        styled_label(
            inner, text="Select APK files to install on your Android VM",
            font=Fonts.body(), color=Colors.TEXT_SECONDARY
        ).pack(pady=(0, 10))

        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack()

        styled_button(
            btn_row, "Browse Files", self._browse_apk,
            color=Colors.INFO, width=140
        ).pack(side="left", padx=5)

        styled_button(
            btn_row, "Clear Queue", self._clear_queue,
            color=Colors.BG_ELEVATED, width=120
        ).pack(side="left", padx=5)

        # ── Queue List ──
        queue_header = ctk.CTkFrame(self, fg_color="transparent")
        queue_header.pack(fill="x", pady=(0, 6))

        styled_label(
            queue_header, text="Install Queue",
            font=Fonts.heading_sm(), color=Colors.TEXT_SECONDARY
        ).pack(side="left")

        self.queue_frame = ctk.CTkScrollableFrame(
            self, fg_color=Colors.BG_INPUT,
            corner_radius=8, height=200,
            border_width=1, border_color=Colors.BORDER,
        )
        self.queue_frame.pack(fill="both", expand=True, pady=(0, 12))

        # Empty state
        self.empty_label = styled_label(
            self.queue_frame,
            text="No APK files queued. Click 'Browse Files' to add some.",
            font=Fonts.body_sm(), color=Colors.TEXT_MUTED
        )
        self.empty_label.pack(pady=30)

        # ── Action Bar ──
        action_bar = ctk.CTkFrame(self, fg_color="transparent")
        action_bar.pack(fill="x")

        self.btn_install = styled_button(
            action_bar, "⬆  Install All APKs", self._install_all,
            color=Colors.SUCCESS, width=200, height=44
        )
        self.btn_install.pack(side="left")

        # Status label
        self.status_label = styled_label(
            action_bar, text="",
            font=Fonts.body(), color=Colors.TEXT_MUTED
        )
        self.status_label.pack(side="left", padx=20)

        # ── Installed Packages Section ──
        pkg_header = ctk.CTkFrame(self, fg_color="transparent")
        pkg_header.pack(fill="x", pady=(16, 6))

        styled_label(
            pkg_header, text="Installed Packages",
            font=Fonts.heading_sm(), color=Colors.TEXT_SECONDARY
        ).pack(side="left")

        self.btn_refresh_pkgs = ctk.CTkButton(
            pkg_header, text="Refresh", width=70, height=26,
            fg_color=Colors.BG_ELEVATED, hover_color=Colors.BG_HOVER,
            font=Fonts.body_sm(), text_color=Colors.TEXT_MUTED,
            command=self._refresh_packages
        )
        self.btn_refresh_pkgs.pack(side="right")

        self.pkg_list = ctk.CTkTextbox(
            self, height=100, fg_color=Colors.BG_INPUT,
            text_color=Colors.CYAN,
            font=Fonts.mono_sm(),
            corner_radius=8, border_width=1,
            border_color=Colors.BORDER,
        )
        self.pkg_list.pack(fill="x", pady=(0, 0))
        self.pkg_list.configure(state="disabled")

    # ── ADB Setter (called by app.py) ──

    def set_adb(self, adb):
        """Set the ADB manager instance for this frame."""
        self.adb = adb

    # ── File Selection ──

    def _browse_apk(self):
        files = filedialog.askopenfilenames(
            title="Select APK Files",
            filetypes=[("Android Package", "*.apk"), ("All Files", "*.*")]
        )
        if not files:
            return

        # Hide empty state
        self.empty_label.pack_forget()

        for f in files:
            if f not in self.apk_paths:
                self.apk_paths.append(f)
                self._add_queue_item(f)

        self._update_badge()

    def _add_queue_item(self, path: str):
        """Add a visual queue item for an APK."""
        item = ctk.CTkFrame(
            self.queue_frame, fg_color=Colors.BG_CARD,
            corner_radius=8, height=36
        )
        item.pack(fill="x", padx=4, pady=2)
        item.pack_propagate(False)

        filename = os.path.basename(path)
        size_mb = round(os.path.getsize(path) / (1024 * 1024), 1)

        styled_label(
            item, text=f"📦  {filename}",
            font=Fonts.body(), color=Colors.TEXT_PRIMARY
        ).pack(side="left", padx=10)

        styled_label(
            item, text=f"{size_mb} MB",
            font=Fonts.body_sm(), color=Colors.TEXT_MUTED
        ).pack(side="right", padx=10)

    def _clear_queue(self):
        self.apk_paths.clear()
        for child in self.queue_frame.winfo_children():
            child.destroy()
        self.empty_label = styled_label(
            self.queue_frame,
            text="No APK files queued. Click 'Browse Files' to add some.",
            font=Fonts.body_sm(), color=Colors.TEXT_MUTED
        )
        self.empty_label.pack(pady=30)
        self._update_badge()
        self.status_label.configure(text="")

    def _update_badge(self):
        count = len(self.apk_paths)
        self.pkg_count_label.configure(text=f"{count} queued")

    # ── Installation ──

    def _install_all(self):
        if not self.apk_paths:
            self.status_label.configure(
                text="No APKs in queue.", text_color=Colors.WARNING
            )
            return

        if not self.adb or not self.adb.is_connected:
            self.status_label.configure(
                text="ADB not connected. Connect from Dashboard first.",
                text_color=Colors.DANGER
            )
            return

        self.btn_install.configure(state="disabled")
        self.status_label.configure(
            text="Installing...", text_color=Colors.WARNING
        )

        paths = list(self.apk_paths)

        def _do():
            success_count = 0
            fail_count = 0

            for i, path in enumerate(paths):
                name = os.path.basename(path)
                self.after(0, lambda n=name, idx=i: self.status_label.configure(
                    text=f"Installing {n} ({idx + 1}/{len(paths)})...",
                    text_color=Colors.WARNING
                ))

                ok, msg = self.adb.install_apk(path)
                if ok:
                    success_count += 1
                else:
                    fail_count += 1

            # Done
            self.after(0, lambda: self._on_install_complete(
                success_count, fail_count
            ))

        threading.Thread(target=_do, daemon=True).start()

    def _on_install_complete(self, success: int, failed: int):
        self.btn_install.configure(state="normal")
        total = success + failed

        if failed == 0:
            self.status_label.configure(
                text=f"✓ All {total} APKs installed successfully!",
                text_color=Colors.SUCCESS
            )
        else:
            self.status_label.configure(
                text=f"Done: {success} installed, {failed} failed.",
                text_color=Colors.ORANGE
            )

        self._clear_queue()
        self._refresh_packages()

    # ── Package List ──

    def _refresh_packages(self):
        if not self.adb or not self.adb.is_connected:
            return

        def _do():
            packages = self.adb.list_packages(third_party_only=True)
            self.after(0, lambda: self._display_packages(packages))

        threading.Thread(target=_do, daemon=True).start()

    def _display_packages(self, packages: list[str]):
        self.pkg_list.configure(state="normal")
        self.pkg_list.delete("1.0", "end")
        if packages:
            for pkg in sorted(packages):
                self.pkg_list.insert("end", f"  📱 {pkg}\n")
        else:
            self.pkg_list.insert("end", "  No third-party packages installed.\n")
        self.pkg_list.configure(state="disabled")
