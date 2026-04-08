"""QEMU process lifecycle manager for APK-Lator.

Handles starting, stopping, monitoring, and configuring the QEMU virtual machine
with appropriate flags for the host platform (Windows WHPX / Linux KVM).
"""
import subprocess
import threading
import queue
import signal
import os
from typing import Optional, Callable
from core.platform_utils import (
    detect_platform, get_qemu_path, get_accelerator,
    check_virgl_support, load_settings
)


class QemuManager:
    """Manages the QEMU virtual machine process lifecycle.

    Attributes:
        disk_path: Path to the .qcow2 virtual disk image.
        iso_path: Optional path to Android-x86 ISO (for first-time install).
        cores: Number of vCPUs to assign.
        ram_mb: RAM allocation in megabytes.
        on_log: Callback for log output lines.
        on_exit: Callback when QEMU process exits with return code.
    """

    def __init__(
        self,
        disk_path: str,
        iso_path: Optional[str] = None,
        cores: int = 4,
        ram_mb: int = 4096,
        enable_audio: bool = True,
        virgl: bool = True,
        display_backend: str = "gtk",
        on_log: Optional[Callable[[str], None]] = None,
        on_exit: Optional[Callable[[int], None]] = None,
    ):
        self.disk_path = disk_path
        self.iso_path = iso_path
        self.cores = cores
        self.ram_mb = ram_mb
        self.enable_audio = enable_audio
        self.virgl = virgl
        self.display_backend = display_backend
        self.on_log = on_log
        self.on_exit = on_exit

        self._process: Optional[subprocess.Popen] = None
        self._log_queue: queue.Queue = queue.Queue()
        self._running = False

    # ── Properties ──

    @property
    def is_running(self) -> bool:
        """True if the QEMU process is alive."""
        return self._process is not None and self._process.poll() is None

    @property
    def pid(self) -> Optional[int]:
        """PID of the running QEMU process."""
        if self._process and self.is_running:
            return self._process.pid
        return None

    # ── Command Builder ──

    def build_command(self, first_boot: bool = False) -> list[str]:
        """Build the full QEMU command-line argument list.

        Args:
            first_boot: If True, mounts the ISO as a CD-ROM and boots from it.

        Returns:
            List of command-line arguments.
        """
        plat = detect_platform()
        accel = get_accelerator()
        qemu = get_qemu_path()
        has_virgl = check_virgl_support() if self.virgl else False

        self._emit(f"Platform: {plat} | Accelerator: {accel} | virgl: {has_virgl}")

        cmd = [qemu]

        # ── Machine & CPU ──
        cmd += ["-machine", f"pc,accel={accel}"]

        # WHPX doesn't fully support -cpu host on all chips
        if accel == "kvm":
            cmd += ["-cpu", "host"]
        elif accel == "whpx":
            cmd += ["-cpu", "qemu64"]
        else:
            cmd += ["-cpu", "qemu64"]

        cmd += ["-smp", f"cores={self.cores},threads=1"]
        cmd += ["-m", str(self.ram_mb)]

        # ── GPU ──
        if has_virgl:
            cmd += ["-device", "virtio-vga,virgl=on"]
            cmd += ["-display", f"{self.display_backend},gl=on"]
        else:
            # Fallback: software-rendered VGA
            cmd += ["-device", "virtio-vga"]
            cmd += ["-display", self.display_backend]
            self._emit("⚠ virgl not available — using software rendering")

        # ── Network with ADB port forwarding ──
        cmd += ["-device", "virtio-net-pci,netdev=n0"]
        cmd += ["-netdev", "user,id=n0,hostfwd=tcp::5555-:5555"]

        # ── Storage (virtio block device) ──
        cmd += ["-device", "virtio-blk-pci,drive=hd0"]
        cmd += [
            "-drive",
            f"file={self.disk_path},id=hd0,if=none,format=qcow2"
        ]

        # ── Input ──
        cmd += ["-device", "usb-ehci"]
        cmd += ["-device", "usb-tablet"]

        # ── Audio ──
        if self.enable_audio:
            if plat == "windows":
                cmd += ["-audiodev", "dsound,id=snd0"]
            else:
                cmd += ["-audiodev", "pa,id=snd0"]
            cmd += ["-device", "ich9-intel-hda"]
            cmd += ["-device", "hda-duplex,audiodev=snd0"]

        # ── Boot order ──
        if first_boot and self.iso_path and os.path.exists(self.iso_path):
            cmd += ["-cdrom", self.iso_path]
            cmd += ["-boot", "order=d"]
            self._emit(f"First boot: mounting ISO {self.iso_path}")
        else:
            cmd += ["-boot", "order=c"]

        # ── Serial console → stdout for log capture ──
        cmd += ["-serial", "mon:stdio"]

        return cmd

    # ── Lifecycle ──

    def start(self, first_boot: bool = False) -> bool:
        """Start the QEMU virtual machine.

        Args:
            first_boot: If True, boots from the Android-x86 ISO for installation.

        Returns:
            True if the process started successfully.
        """
        if self.is_running:
            self._emit("VM is already running.")
            return False

        cmd = self.build_command(first_boot=first_boot)
        self._emit(f"Starting QEMU: {' '.join(cmd[:6])}...")

        try:
            creationflags = 0
            if os.name == "nt":
                creationflags = subprocess.CREATE_NO_WINDOW

            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=creationflags,
            )
            self._running = True

            # Start log reader thread
            log_thread = threading.Thread(
                target=self._read_output, daemon=True, name="qemu-log-reader"
            )
            log_thread.start()

            # Start exit watcher
            exit_thread = threading.Thread(
                target=self._wait_exit, daemon=True, name="qemu-exit-watcher"
            )
            exit_thread.start()

            self._emit(f"✓ QEMU started (PID: {self._process.pid})")
            return True

        except FileNotFoundError:
            self._emit("✗ qemu-system-x86_64 not found. Is QEMU installed?")
            return False
        except OSError as e:
            self._emit(f"✗ Failed to start QEMU: {e}")
            return False

    def stop(self) -> bool:
        """Gracefully stop the QEMU process.

        Returns:
            True if a stop signal was sent.
        """
        if not self._process or not self.is_running:
            self._emit("VM is not running.")
            return False

        self._emit("Stopping QEMU...")
        try:
            if os.name == "nt":
                self._process.terminate()
            else:
                self._process.send_signal(signal.SIGTERM)
            self._running = False
            self._emit("✓ Stop signal sent.")
            return True
        except OSError as e:
            self._emit(f"✗ Failed to stop: {e}")
            return False

    def force_kill(self) -> bool:
        """Forcefully kill the QEMU process.

        Returns:
            True if the process was killed.
        """
        if not self._process:
            return False
        try:
            self._process.kill()
            self._running = False
            self._emit("✓ QEMU force-killed.")
            return True
        except OSError as e:
            self._emit(f"✗ Kill failed: {e}")
            return False

    # ── Configuration Update ──

    def update_config(
        self,
        cores: Optional[int] = None,
        ram_mb: Optional[int] = None,
        virgl: Optional[bool] = None,
        enable_audio: Optional[bool] = None,
    ):
        """Update VM configuration (takes effect on next start)."""
        if cores is not None:
            self.cores = cores
        if ram_mb is not None:
            self.ram_mb = ram_mb
        if virgl is not None:
            self.virgl = virgl
        if enable_audio is not None:
            self.enable_audio = enable_audio
        self._emit("Configuration updated (restart VM to apply).")

    # ── Internal ──

    def _read_output(self):
        """Read QEMU stdout/stderr in a background thread."""
        try:
            for line in iter(self._process.stdout.readline, ""):
                stripped = line.rstrip()
                if stripped:
                    self._emit(stripped)
                self._log_queue.put(stripped)
        except (ValueError, OSError):
            pass
        finally:
            try:
                self._process.stdout.close()
            except Exception:
                pass

    def _wait_exit(self):
        """Wait for QEMU to exit and fire callback."""
        code = self._process.wait()
        self._running = False
        self._emit(f"QEMU exited with code {code}")
        if self.on_exit:
            self.on_exit(code)

    def _emit(self, message: str):
        """Emit a log message through the callback."""
        if self.on_log:
            self.on_log(message)
