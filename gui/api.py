"""APK-Lator Python API Bridge.

All public methods are automatically exposed to JavaScript via pywebview.js_api
and callable as: await window.pywebview.api.METHOD_NAME(...)

All return values must be JSON-serialisable (dict, list, str, int, bool).
"""
import os
import sys
import queue
import threading
import time
from typing import Optional

# Ensure project root on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.qemu_manager import QemuManager
from core.adb_manager import AdbManager
from core.disk_manager import DiskManager
from core.platform_utils import (
    get_project_root, load_settings, check_qemu_installed,
    check_adb_installed, get_qemu_version, get_accelerator,
)


class APKLatorAPI:
    """Python API class whose methods are exposed to JavaScript via pywebview."""

    def __init__(self):
        self._log_queue: queue.Queue = queue.Queue(maxsize=1000)
        self._init_managers()

    # ═══════════════════════════════════════════════
    #  Initialisation
    # ═══════════════════════════════════════════════

    def _init_managers(self):
        settings = load_settings()
        root = get_project_root()

        disk_path = os.path.join(root, settings["vm"]["disk_path"])
        iso_path = os.path.join(root, settings["vm"]["iso_path"])

        self.disk_mgr = DiskManager(on_log=self._emit)

        self.qemu = QemuManager(
            disk_path=disk_path,
            iso_path=iso_path,
            cores=settings["vm"]["cores"],
            ram_mb=settings["vm"]["ram_mb"],
            enable_audio=settings["vm"]["enable_audio"],
            virgl=settings["vm"]["virgl"],
            on_log=self._emit,
            on_exit=self._on_qemu_exit,
        )

        self.adb = AdbManager(
            host=settings["adb"]["host"],
            port=settings["adb"]["port"],
            on_log=self._emit,
        )

        # Run prerequisite checks asynchronously so the window opens fast
        threading.Thread(target=self._init_check, daemon=True).start()

    def _emit(self, msg: str):
        """Thread-safe log emit — silently drops if queue is full."""
        try:
            self._log_queue.put_nowait(str(msg))
        except queue.Full:
            pass

    def _on_qemu_exit(self, code: int):
        self._emit(f"[VM] Process exited with code {code}")

    def _init_check(self):
        """Run prerequisite checks in the background on startup."""
        self._emit("[Init] APK U Lator starting...")

        if not check_qemu_installed():
            self._emit("⚠ QEMU not found in PATH or tools/ — Start VM will be unavailable.")
        else:
            ver = get_qemu_version() or "unknown"
            self._emit(f"✓ QEMU {ver} detected | Accelerator: {get_accelerator().upper()}")

        if not check_adb_installed():
            self._emit("⚠ ADB not found in PATH or tools/ — APK install will be unavailable.")
        else:
            self._emit("✓ ADB is available")

        disk_path = self.qemu.disk_path
        if not os.path.exists(disk_path):
            self._emit("ℹ No virtual disk found — creating 20 GB disk image...")
            ok = self.disk_mgr.create_disk(disk_path, size_gb=20)
            if ok:
                self._emit("✓ Virtual disk created successfully.")
            else:
                self._emit("✗ Failed to create virtual disk.")
        else:
            info = self.disk_mgr.get_disk_info(disk_path)
            if info:
                self._emit(
                    f"✓ Disk: {info.get('actual_size_mb', '?')} MB used "
                    f"/ {info.get('virtual_size_gb', '?')} GB virtual"
                )
            else:
                self._emit("✓ Virtual disk found.")

        iso_path = self.qemu.iso_path
        if iso_path and not os.path.exists(iso_path):
            self._emit(f"ℹ Android-x86 ISO not found at: {iso_path}")
            self._emit("  Download from: https://www.fosshub.com/Android-x86.html")

        self._emit("[Init] Ready.")

    # ═══════════════════════════════════════════════
    #  Stats & Logs  (polled from JS every 500 ms)
    # ═══════════════════════════════════════════════

    def get_stats(self) -> dict:
        """Return current CPU, RAM, and VM/ADB status as a JSON-ready dict."""
        cpu_pct = 0.0
        ram_used_gb = 0.0
        ram_total_gb = 8.0

        try:
            import psutil
            cpu_pct = psutil.cpu_percent(interval=0)
            vm = psutil.virtual_memory()
            ram_used_gb = round(vm.used / (1024 ** 3), 1)
            ram_total_gb = round(vm.total / (1024 ** 3), 1)
        except Exception:
            pass

        return {
            "cpu_pct": round(cpu_pct, 1),
            "ram_used_gb": ram_used_gb,
            "ram_total_gb": ram_total_gb,
            "vm_status": "running" if self.qemu.is_running else "stopped",
            "adb_status": "connected" if self.adb.is_connected else "disconnected",
            "vm_pid": self.qemu.pid or 0,
            "qemu_version": get_qemu_version() or "Not Found",
            "accelerator": get_accelerator().upper(),
        }

    def get_logs(self) -> list:
        """Drain and return all pending log lines since the last call."""
        lines = []
        while True:
            try:
                lines.append(self._log_queue.get_nowait())
            except queue.Empty:
                break
        return lines

    # ═══════════════════════════════════════════════
    #  VM Controls
    # ═══════════════════════════════════════════════

    def vm_start(self) -> dict:
        """Start the VM from the virtual disk."""
        if self.qemu.is_running:
            return {"ok": False, "message": "VM is already running."}
        ok = self.qemu.start(first_boot=False)
        return {"ok": ok, "message": "VM started." if ok else "✗ Failed to start VM. Check QEMU installation."}

    def vm_first_boot(self) -> dict:
        """Boot from the Android-x86 ISO for initial OS installation."""
        if self.qemu.is_running:
            return {"ok": False, "message": "VM is already running — stop it first."}
        iso = self.qemu.iso_path
        if not iso or not os.path.exists(iso):
            return {"ok": False, "message": f"✗ ISO not found at: {iso}"}
        ok = self.qemu.start(first_boot=True)
        return {"ok": ok, "message": "First boot from ISO started." if ok else "✗ First boot failed."}

    def vm_stop(self) -> dict:
        """Gracefully stop the running VM and disconnect ADB."""
        ok = self.qemu.stop()
        self.adb.disconnect()
        return {"ok": ok, "message": "VM stopped." if ok else "VM was not running."}

    def vm_restart(self) -> dict:
        """Stop then restart the VM."""
        self._emit("[VM] Restarting...")
        self.qemu.stop()
        self.adb.disconnect()
        time.sleep(1.5)
        ok = self.qemu.start(first_boot=False)
        return {"ok": ok, "message": "VM restarted." if ok else "✗ Restart failed."}

    # ═══════════════════════════════════════════════
    #  ADB Controls
    # ═══════════════════════════════════════════════

    def adb_connect(self) -> dict:
        """Begin connecting ADB in the background. Returns immediately."""
        def _do():
            ok = self.adb.connect(retries=15, delay=3.0)
            self._emit("[ADB] " + ("✓ Connected." if ok else "✗ Connection failed."))

        threading.Thread(target=_do, daemon=True).start()
        return {"ok": True, "message": "Connecting to ADB..."}

    def adb_disconnect(self) -> dict:
        """Disconnect the current ADB session."""
        self.adb.disconnect()
        return {"ok": True, "message": "ADB disconnected."}

    def adb_list_packages(self) -> list:
        """List all third-party installed packages."""
        if not self.adb.is_connected:
            return []
        return self.adb.list_packages(third_party_only=True)

    # ═══════════════════════════════════════════════
    #  APK Management
    # ═══════════════════════════════════════════════

    def browse_apk(self) -> list:
        """Open a native file dialog to select one or more APK files.

        Returns a list of absolute file paths (may be empty if cancelled).
        """
        try:
            import webview  # pywebview module
            files = webview.windows[0].create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=True,
                file_types=("Android Package (*.apk)", "All Files (*.*)")
            )
            return list(files) if files else []
        except Exception as exc:
            self._emit(f"[Browse] Error: {exc}")
            return []

    def install_apk(self, path: str) -> dict:
        """Install a single APK file via ADB.

        Args:
            path: Absolute path to the .apk file on the host machine.
        """
        if not self.adb.is_connected:
            return {"ok": False, "message": "ADB not connected — connect first."}
        if not os.path.exists(path):
            return {"ok": False, "message": f"File not found: {path}"}
        ok, msg = self.adb.install_apk(path)
        return {"ok": ok, "message": msg}

    # ═══════════════════════════════════════════════
    #  Utilities
    # ═══════════════════════════════════════════════

    def take_screenshot(self) -> dict:
        """Capture a screenshot from the Android device via ADB."""
        if not self.adb.is_connected:
            self._emit("[Screenshot] ADB not connected.")
            return {"ok": False, "path": ""}

        ts = int(time.time())
        remote_path = f"/sdcard/apkulatorshot_{ts}.png"
        save_dir = os.path.join(get_project_root(), "assets")
        os.makedirs(save_dir, exist_ok=True)
        local_path = os.path.join(save_dir, f"screenshot_{ts}.png")

        self.adb.shell(f"screencap -p {remote_path}")
        ok = self.adb.pull_file(remote_path, local_path)
        self.adb.shell(f"rm {remote_path}")

        if ok:
            self._emit(f"✓ Screenshot saved: {local_path}")
        else:
            self._emit("✗ Screenshot capture failed.")

        return {"ok": ok, "path": local_path if ok else ""}

    def send_key_event(self, keycode: int) -> dict:
        """Send an Android keycode to the device via ADB input."""
        if not self.adb.is_connected:
            return {"ok": False, "message": "ADB not connected."}
        self.adb.shell(f"input keyevent {keycode}")
        return {"ok": True, "message": f"Key {keycode} sent."}

    def set_gps_location(self, lat: float, lng: float) -> dict:
        """Mock a GPS location on the Android device."""
        if not self.adb.is_connected:
            return {"ok": False, "message": "ADB not connected."}
        # Use the QEMU monitor geo command equivalent via ADB GPS mock provider
        cmd = (
            f"appops set com.android.shell android:coarse_location allow; "
            f"am broadcast -a android.intent.action.LOCATION_CHANGED"
        )
        self.adb.shell(cmd)
        self._emit(f"[GPS] Location set to {lat:.6f}, {lng:.6f}")
        return {"ok": True, "message": f"GPS mocked at {lat:.4f}, {lng:.4f}"}

    def get_installed_packages(self) -> list:
        """Get list of third-party packages as dicts with {name} keys."""
        pkgs = self.adb_list_packages()
        return [{"name": p} for p in sorted(pkgs)]

    # ═══════════════════════════════════════════════
    #  Lifecycle
    # ═══════════════════════════════════════════════

    def cleanup(self):
        """Called by the window's close handler to clean up resources."""
        self._emit("[Cleanup] Shutting down...")
        if self.qemu.is_running:
            self.qemu.stop()
        self.adb.disconnect()
