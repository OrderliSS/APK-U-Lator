"""Settings Frame — VM configuration, optimization, and system info panel."""
import customtkinter as ctk
import threading
import os
from gui.theme import Colors, Fonts, styled_button, styled_card, styled_label
from core.platform_utils import (
    load_settings, save_settings, get_system_info, get_project_root
)


class SettingsFrame(ctk.CTkFrame):
    """VM configuration and optimization settings panel."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.adb = None  # Set externally
        self.qemu = None  # Set externally
        self.settings = load_settings()
        self._build_ui()

    def _build_ui(self):
        # ── Header ──
        styled_label(
            self, text="Settings",
            font=Fonts.heading_xl(), color=Colors.PRIMARY
        ).pack(anchor="w", pady=(0, 16))

        # Scrollable content
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            corner_radius=0
        )
        scroll.pack(fill="both", expand=True)

        # ══════════════════════════════════
        #  VM Configuration
        # ══════════════════════════════════
        self._section_header(scroll, "⚡ Virtual Machine")

        vm_card = styled_card(scroll)
        vm_card.pack(fill="x", pady=(0, 16), padx=4)

        vm_inner = ctk.CTkFrame(vm_card, fg_color="transparent")
        vm_inner.pack(fill="x", padx=16, pady=12)

        # CPU Cores
        row1 = ctk.CTkFrame(vm_inner, fg_color="transparent")
        row1.pack(fill="x", pady=4)
        styled_label(row1, text="CPU Cores", font=Fonts.body(),
                      color=Colors.TEXT_PRIMARY).pack(side="left")
        self.cores_var = ctk.StringVar(value=str(self.settings["vm"]["cores"]))
        self.cores_menu = ctk.CTkOptionMenu(
            row1, values=["1", "2", "4", "6", "8"],
            variable=self.cores_var,
            fg_color=Colors.BG_INPUT, button_color=Colors.INFO,
            button_hover_color=Colors.BG_HOVER,
            font=Fonts.body(), width=100
        )
        self.cores_menu.pack(side="right")

        # RAM
        row2 = ctk.CTkFrame(vm_inner, fg_color="transparent")
        row2.pack(fill="x", pady=4)
        styled_label(row2, text="RAM (MB)", font=Fonts.body(),
                      color=Colors.TEXT_PRIMARY).pack(side="left")
        self.ram_var = ctk.StringVar(value=str(self.settings["vm"]["ram_mb"]))
        self.ram_menu = ctk.CTkOptionMenu(
            row2, values=["1024", "2048", "3072", "4096", "6144", "8192"],
            variable=self.ram_var,
            fg_color=Colors.BG_INPUT, button_color=Colors.INFO,
            button_hover_color=Colors.BG_HOVER,
            font=Fonts.body(), width=100
        )
        self.ram_menu.pack(side="right")

        # virgl
        row3 = ctk.CTkFrame(vm_inner, fg_color="transparent")
        row3.pack(fill="x", pady=4)
        styled_label(row3, text="GPU Acceleration (virgl)",
                      font=Fonts.body(), color=Colors.TEXT_PRIMARY).pack(side="left")
        self.virgl_var = ctk.BooleanVar(value=self.settings["vm"]["virgl"])
        self.virgl_switch = ctk.CTkSwitch(
            row3, text="", variable=self.virgl_var,
            onvalue=True, offvalue=False,
            progress_color=Colors.SUCCESS,
            button_color=Colors.TEXT_SECONDARY,
            button_hover_color=Colors.CYAN,
        )
        self.virgl_switch.pack(side="right")

        # Audio
        row4 = ctk.CTkFrame(vm_inner, fg_color="transparent")
        row4.pack(fill="x", pady=4)
        styled_label(row4, text="Audio", font=Fonts.body(),
                      color=Colors.TEXT_PRIMARY).pack(side="left")
        self.audio_var = ctk.BooleanVar(value=self.settings["vm"]["enable_audio"])
        self.audio_switch = ctk.CTkSwitch(
            row4, text="", variable=self.audio_var,
            onvalue=True, offvalue=False,
            progress_color=Colors.SUCCESS,
            button_color=Colors.TEXT_SECONDARY,
            button_hover_color=Colors.CYAN,
        )
        self.audio_switch.pack(side="right")

        # Save button
        save_row = ctk.CTkFrame(vm_inner, fg_color="transparent")
        save_row.pack(fill="x", pady=(10, 0))

        self.save_status = styled_label(
            save_row, text="", font=Fonts.body_sm(), color=Colors.TEXT_MUTED
        )
        self.save_status.pack(side="left")

        styled_button(
            save_row, "💾  Save Settings", self._save_settings,
            color=Colors.SUCCESS, width=160
        ).pack(side="right")

        # ══════════════════════════════════
        #  Optimization
        # ══════════════════════════════════
        self._section_header(scroll, "🚀 Optimization")

        opt_card = styled_card(scroll)
        opt_card.pack(fill="x", pady=(0, 16), padx=4)

        opt_inner = ctk.CTkFrame(opt_card, fg_color="transparent")
        opt_inner.pack(fill="x", padx=16, pady=12)

        styled_label(
            opt_inner,
            text="Apply performance tweaks to reduce RAM usage and\n"
                 "disable unnecessary animations/services inside Android.",
            font=Fonts.body_sm(), color=Colors.TEXT_SECONDARY
        ).pack(anchor="w", pady=(0, 10))

        opt_buttons = ctk.CTkFrame(opt_inner, fg_color="transparent")
        opt_buttons.pack(fill="x")

        styled_button(
            opt_buttons, "⚡ Apply ADB Tweaks", self._apply_adb_tweaks,
            color=Colors.INFO, width=180
        ).pack(side="left", padx=(0, 10))

        styled_button(
            opt_buttons, "🔧 Push build.prop", self._push_build_prop,
            color=Colors.ORANGE, width=180
        ).pack(side="left", padx=(0, 10))

        styled_button(
            opt_buttons, "🔄 Reboot VM", self._reboot_vm,
            color=Colors.WARNING, width=140
        ).pack(side="left")

        self.opt_status = styled_label(
            opt_inner, text="", font=Fonts.body_sm(), color=Colors.TEXT_MUTED
        )
        self.opt_status.pack(anchor="w", pady=(8, 0))

        # ══════════════════════════════════
        #  System Info
        # ══════════════════════════════════
        self._section_header(scroll, "🖥  System Information")

        info_card = styled_card(scroll)
        info_card.pack(fill="x", pady=(0, 16), padx=4)

        info_inner = ctk.CTkFrame(info_card, fg_color="transparent")
        info_inner.pack(fill="x", padx=16, pady=12)

        sys_info = get_system_info()
        info_rows = [
            ("Platform", f"{sys_info['os']} {sys_info['os_version'][:30]}"),
            ("Architecture", sys_info["arch"]),
            ("CPU Cores", str(sys_info["cpu_count"])),
            ("Python", sys_info["python"]),
            ("Accelerator", sys_info["accelerator"].upper()),
            ("QEMU", sys_info["qemu_version"] or "Not Installed"),
            ("virgl Support", "✓ Yes" if sys_info["virgl_support"] else "✗ No"),
            ("ADB", "✓ Installed" if sys_info["adb_installed"] else "✗ Not Found"),
        ]

        for label, value in info_rows:
            row = ctk.CTkFrame(info_inner, fg_color="transparent")
            row.pack(fill="x", pady=2)
            styled_label(row, text=label, font=Fonts.body_sm(),
                          color=Colors.TEXT_MUTED).pack(side="left")
            color = Colors.SUCCESS if "✓" in value else (
                Colors.DANGER if "✗" in value or "Not" in value
                else Colors.TEXT_PRIMARY
            )
            styled_label(row, text=value, font=Fonts.body_sm(),
                          color=color).pack(side="right")

        # ══════════════════════════════════
        #  Disk Management
        # ══════════════════════════════════
        self._section_header(scroll, "💾 Disk Management")

        disk_card = styled_card(scroll)
        disk_card.pack(fill="x", pady=(0, 16), padx=4)

        disk_inner = ctk.CTkFrame(disk_card, fg_color="transparent")
        disk_inner.pack(fill="x", padx=16, pady=12)

        disk_buttons = ctk.CTkFrame(disk_inner, fg_color="transparent")
        disk_buttons.pack(fill="x")

        styled_button(
            disk_buttons, "📸 Create Snapshot", self._create_snapshot,
            color=Colors.CYAN, width=170
        ).pack(side="left", padx=(0, 10))

        styled_button(
            disk_buttons, "⏮ Restore Snapshot", self._restore_snapshot,
            color=Colors.WARNING, width=170
        ).pack(side="left")

        self.disk_status = styled_label(
            disk_inner, text="", font=Fonts.body_sm(), color=Colors.TEXT_MUTED
        )
        self.disk_status.pack(anchor="w", pady=(8, 0))

    # ── Section Header Helper ──

    def _section_header(self, parent, text: str):
        styled_label(
            parent, text=text,
            font=Fonts.heading_md(), color=Colors.TEXT_PRIMARY
        ).pack(anchor="w", pady=(12, 6), padx=4)

    # ── External Setters ──

    def set_adb(self, adb):
        self.adb = adb

    def set_qemu(self, qemu):
        self.qemu = qemu

    # ── Actions ──

    def _save_settings(self):
        self.settings["vm"]["cores"] = int(self.cores_var.get())
        self.settings["vm"]["ram_mb"] = int(self.ram_var.get())
        self.settings["vm"]["virgl"] = self.virgl_var.get()
        self.settings["vm"]["enable_audio"] = self.audio_var.get()

        if save_settings(self.settings):
            self.save_status.configure(
                text="✓ Settings saved. Restart VM to apply.",
                text_color=Colors.SUCCESS
            )
            # Update QEMU manager if available
            if self.qemu:
                self.qemu.update_config(
                    cores=self.settings["vm"]["cores"],
                    ram_mb=self.settings["vm"]["ram_mb"],
                    virgl=self.settings["vm"]["virgl"],
                    enable_audio=self.settings["vm"]["enable_audio"],
                )
        else:
            self.save_status.configure(
                text="✗ Failed to save settings.",
                text_color=Colors.DANGER
            )

    def _apply_adb_tweaks(self):
        if not self.adb or not self.adb.is_connected:
            self.opt_status.configure(
                text="ADB not connected.", text_color=Colors.DANGER
            )
            return

        self.opt_status.configure(
            text="Applying tweaks...", text_color=Colors.WARNING
        )

        def _do():
            results = self.adb.apply_optimizations()
            passed = sum(1 for _, s in results if s)
            total = len(results)
            self.after(0, lambda: self.opt_status.configure(
                text=f"✓ {passed}/{total} tweaks applied.",
                text_color=Colors.SUCCESS if passed == total else Colors.ORANGE
            ))

        threading.Thread(target=_do, daemon=True).start()

    def _push_build_prop(self):
        if not self.adb or not self.adb.is_connected:
            self.opt_status.configure(
                text="ADB not connected.", text_color=Colors.DANGER
            )
            return

        self.opt_status.configure(
            text="Pushing build.prop tweaks (requires root)...",
            text_color=Colors.WARNING
        )

        def _do():
            ok = self.adb.push_build_prop_tweaks()
            self.after(0, lambda: self.opt_status.configure(
                text="✓ build.prop updated. Reboot to apply." if ok
                     else "✗ Failed (root required).",
                text_color=Colors.SUCCESS if ok else Colors.DANGER
            ))

        threading.Thread(target=_do, daemon=True).start()

    def _reboot_vm(self):
        if self.adb and self.adb.is_connected:
            self.adb.reboot()
            self.opt_status.configure(
                text="Rebooting...", text_color=Colors.WARNING
            )

    def _create_snapshot(self):
        from core.disk_manager import DiskManager
        dm = DiskManager()
        disk_path = os.path.join(get_project_root(), self.settings["vm"]["disk_path"])

        def _do():
            ok = dm.create_snapshot(disk_path, "settings_snapshot")
            self.after(0, lambda: self.disk_status.configure(
                text="✓ Snapshot created." if ok else "✗ Snapshot failed.",
                text_color=Colors.SUCCESS if ok else Colors.DANGER
            ))

        threading.Thread(target=_do, daemon=True).start()

    def _restore_snapshot(self):
        from core.disk_manager import DiskManager
        dm = DiskManager()
        disk_path = os.path.join(get_project_root(), self.settings["vm"]["disk_path"])

        if self.qemu and self.qemu.is_running:
            self.disk_status.configure(
                text="Stop the VM before restoring.", text_color=Colors.DANGER
            )
            return

        def _do():
            ok = dm.restore_snapshot(disk_path, "settings_snapshot")
            self.after(0, lambda: self.disk_status.configure(
                text="✓ Snapshot restored." if ok else "✗ Restore failed.",
                text_color=Colors.SUCCESS if ok else Colors.DANGER
            ))

        threading.Thread(target=_do, daemon=True).start()
