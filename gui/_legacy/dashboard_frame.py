"""Dashboard Frame — VM status cards, start/stop controls, and mini log viewer."""
import customtkinter as ctk
import threading
import os
from gui.theme import Colors, Fonts, styled_button, styled_card, styled_label
from core.qemu_manager import QemuManager
from core.adb_manager import AdbManager
from core.disk_manager import DiskManager
from core.platform_utils import (
    get_accelerator, get_project_root, check_qemu_installed,
    check_adb_installed, get_qemu_version, load_settings
)


class DashboardFrame(ctk.CTkFrame):
    """Main dashboard with VM status, controls, and log output."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        root = get_project_root()
        settings = load_settings()

        # Resolve disk & ISO paths
        disk_path = os.path.join(root, settings["vm"]["disk_path"])
        iso_path = os.path.join(root, settings["vm"]["iso_path"])

        # ── Core Managers ──
        self.disk_mgr = DiskManager(on_log=self._on_log)
        self.qemu = QemuManager(
            disk_path=disk_path,
            iso_path=iso_path,
            cores=settings["vm"]["cores"],
            ram_mb=settings["vm"]["ram_mb"],
            enable_audio=settings["vm"]["enable_audio"],
            virgl=settings["vm"]["virgl"],
            on_log=self._on_log,
            on_exit=self._on_qemu_exit,
        )
        self.adb = AdbManager(
            host=settings["adb"]["host"],
            port=settings["adb"]["port"],
            on_log=self._on_log,
        )

        self._build_ui()
        self._check_prerequisites()

    def _build_ui(self):
        # ── Page Header ──
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 16))

        styled_label(
            header_frame, text="Dashboard",
            font=Fonts.heading_xl(), color=Colors.PRIMARY
        ).pack(side="left")

        # Version badge
        qemu_ver = get_qemu_version() or "Not Found"
        ver_badge = ctk.CTkFrame(header_frame, fg_color=Colors.BG_ELEVATED,
                                  corner_radius=6)
        ver_badge.pack(side="right")
        styled_label(
            ver_badge, text=f"QEMU {qemu_ver}",
            font=Fonts.badge(), color=Colors.TEXT_MUTED
        ).pack(padx=8, pady=3)

        # ── Status Cards Row ──
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack(fill="x", pady=(0, 16))

        self.vm_status_label = self._make_status_card(
            cards_frame, "VM Status", "⏹ Stopped", Colors.DANGER
        )
        self.accel_label = self._make_status_card(
            cards_frame, "Accelerator",
            get_accelerator().upper(), Colors.CYAN
        )
        self.adb_status_label = self._make_status_card(
            cards_frame, "ADB", "Disconnected", Colors.WARNING
        )
        self.disk_label = self._make_status_card(
            cards_frame, "Disk", "Checking...", Colors.TEXT_SECONDARY
        )

        # ── Control Bar ──
        controls = styled_card(self)
        controls.pack(fill="x", pady=(0, 16), ipady=12)

        ctrl_inner = ctk.CTkFrame(controls, fg_color="transparent")
        ctrl_inner.pack(fill="x", padx=16)

        self.btn_start = styled_button(
            ctrl_inner, "▶  Start VM", self._start_vm,
            color=Colors.SUCCESS, width=150
        )
        self.btn_start.pack(side="left", padx=(0, 10))

        self.btn_first_boot = styled_button(
            ctrl_inner, "💿  First Boot (ISO)", self._first_boot,
            color=Colors.INFO, width=180
        )
        self.btn_first_boot.pack(side="left", padx=(0, 10))

        self.btn_stop = styled_button(
            ctrl_inner, "⏹  Stop VM", self._stop_vm,
            color=Colors.DANGER, width=150
        )
        self.btn_stop.pack(side="left", padx=(0, 10))
        self.btn_stop.configure(state="disabled")

        self.btn_adb = styled_button(
            ctrl_inner, "🔗  Connect ADB", self._connect_adb,
            color=Colors.INFO, width=170
        )
        self.btn_adb.pack(side="left", padx=(0, 10))
        self.btn_adb.configure(state="disabled")

        self.btn_snapshot = styled_button(
            ctrl_inner, "📸  Snapshot", self._create_snapshot,
            color=Colors.ORANGE, width=140
        )
        self.btn_snapshot.pack(side="right")

        # ── Log Viewer ──
        log_header = ctk.CTkFrame(self, fg_color="transparent")
        log_header.pack(fill="x", pady=(0, 4))

        styled_label(log_header, text="Live Output",
                      font=Fonts.heading_sm(), color=Colors.TEXT_SECONDARY
                      ).pack(side="left")

        self.btn_clear_log = ctk.CTkButton(
            log_header, text="Clear", width=60, height=26,
            fg_color=Colors.BG_ELEVATED, hover_color=Colors.BG_HOVER,
            font=Fonts.body_sm(), text_color=Colors.TEXT_MUTED,
            command=self._clear_log
        )
        self.btn_clear_log.pack(side="right")

        self.log_box = ctk.CTkTextbox(
            self, fg_color=Colors.BG_INPUT,
            text_color=Colors.TEXT_LOG,
            font=Fonts.mono(),
            corner_radius=8, border_width=1,
            border_color=Colors.BORDER,
        )
        self.log_box.pack(fill="both", expand=True)
        self.log_box.configure(state="disabled")

    # ── Status Card Factory ──

    def _make_status_card(self, parent, title: str, value: str, color: str):
        card = styled_card(parent, width=180, height=80)
        card.pack(side="left", padx=(0, 12), pady=4)
        card.pack_propagate(False)

        styled_label(
            card, text=title, font=Fonts.body_sm(), color=Colors.TEXT_MUTED
        ).pack(pady=(10, 2))

        value_label = styled_label(
            card, text=value, font=Fonts.heading_sm(), color=color
        )
        value_label.pack()
        return value_label

    # ── Prerequisite Checks ──

    def _check_prerequisites(self):
        """Check system state and update dashboard cards."""
        # QEMU
        if not check_qemu_installed():
            self._on_log("⚠ QEMU not found in PATH or tools/ folder.")
            self.btn_start.configure(state="disabled")
            self.btn_first_boot.configure(state="disabled")

        # ADB
        if not check_adb_installed():
            self._on_log("⚠ ADB not found in PATH or tools/ folder.")

        # Disk
        disk_path = self.qemu.disk_path
        if os.path.exists(disk_path):
            info = self.disk_mgr.get_disk_info(disk_path)
            if info:
                self.disk_label.configure(
                    text=f"{info['actual_size_mb']}MB / {info['virtual_size_gb']}GB",
                    text_color=Colors.CYAN
                )
            else:
                self.disk_label.configure(text="Found", text_color=Colors.SUCCESS)
        else:
            self.disk_label.configure(text="Not Created", text_color=Colors.DANGER)
            self._on_log("ℹ No disk image found. Creating one...")
            threading.Thread(target=self._auto_create_disk, daemon=True).start()

        # ISO
        iso_path = self.qemu.iso_path
        if iso_path and not self.disk_mgr.check_iso_exists(iso_path):
            self._on_log(f"ℹ Android-x86 ISO not found at: {iso_path}")
            self._on_log("  Download from: https://www.fosshub.com/Android-x86.html")

    def _auto_create_disk(self):
        """Auto-create the virtual disk if it doesn't exist."""
        success = self.disk_mgr.create_disk(self.qemu.disk_path, size_gb=20)
        if success:
            self.after(0, lambda: self.disk_label.configure(
                text="20GB (new)", text_color=Colors.SUCCESS
            ))

    # ── VM Control Actions ──

    def _start_vm(self):
        self.btn_start.configure(state="disabled")
        self.btn_first_boot.configure(state="disabled")
        self.qemu.start(first_boot=False)
        self.vm_status_label.configure(text="▶ Running", text_color=Colors.SUCCESS)
        self.btn_stop.configure(state="normal")
        self.btn_adb.configure(state="normal")

    def _first_boot(self):
        """Start VM booting from the ISO for first-time installation."""
        if not self.qemu.iso_path or not os.path.exists(self.qemu.iso_path):
            self._on_log("✗ ISO not found. Please download Android-x86 first.")
            return
        self.btn_start.configure(state="disabled")
        self.btn_first_boot.configure(state="disabled")
        self.qemu.start(first_boot=True)
        self.vm_status_label.configure(
            text="💿 Installing", text_color=Colors.WARNING
        )
        self.btn_stop.configure(state="normal")
        self.btn_adb.configure(state="normal")

    def _stop_vm(self):
        self.qemu.stop()
        self.adb.disconnect()
        self.vm_status_label.configure(text="⏹ Stopped", text_color=Colors.DANGER)
        self.adb_status_label.configure(
            text="Disconnected", text_color=Colors.WARNING
        )
        self.btn_start.configure(state="normal")
        self.btn_first_boot.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.btn_adb.configure(state="disabled")

    def _connect_adb(self):
        """Connect ADB in a background thread."""
        self.btn_adb.configure(state="disabled", text="🔗  Connecting...")
        self.adb_status_label.configure(
            text="Connecting...", text_color=Colors.WARNING
        )

        def _do():
            ok = self.adb.connect(retries=10, delay=3.0)
            self.after(0, lambda: self._update_adb_status(ok))

        threading.Thread(target=_do, daemon=True).start()

    def _update_adb_status(self, connected: bool):
        if connected:
            self.adb_status_label.configure(
                text="Connected ✓", text_color=Colors.CYAN
            )
            self.btn_adb.configure(text="🔗  Connected", state="normal")
        else:
            self.adb_status_label.configure(
                text="Failed ✗", text_color=Colors.DANGER
            )
            self.btn_adb.configure(text="🔗  Retry", state="normal")

    def _create_snapshot(self):
        """Create a snapshot of the current disk state."""
        def _do():
            self.disk_mgr.create_snapshot(self.qemu.disk_path, "manual_snapshot")
        threading.Thread(target=_do, daemon=True).start()

    # ── Log Handling ──

    def _on_log(self, line: str):
        """Thread-safe log append."""
        self.after(0, lambda: self._append_log(line))

    def _append_log(self, line: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", line + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def _on_qemu_exit(self, code: int):
        """Handle QEMU process exit."""
        self.after(0, self._stop_vm)

    # ── Public Access (for cross-frame communication) ──

    def get_adb_manager(self) -> AdbManager:
        return self.adb

    def get_qemu_manager(self) -> QemuManager:
        return self.qemu
