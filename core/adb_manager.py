"""ADB connection and APK management for APK-Lator.

Provides connectivity to the Android VM via ADB over TCP,
APK installation, package listing, device info queries,
and post-install optimization routines.
"""
import subprocess
import time
import os
from typing import Optional, Callable
from core.platform_utils import get_adb_path
from config.defaults import OPTIMIZATION_ADB_COMMANDS, BUILD_PROP_TWEAKS


class AdbManager:
    """Manages ADB connections and APK operations against the Android VM.

    Args:
        host: ADB TCP host (default 127.0.0.1).
        port: ADB TCP port (default 5555, forwarded from QEMU).
        on_log: Optional callback for log messages.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 5555,
        on_log: Optional[Callable[[str], None]] = None,
    ):
        self.host = host
        self.port = port
        self.address = f"{host}:{port}"
        self.on_log = on_log
        self._connected = False

    # ── Internal Helpers ──

    def _run(self, *args, timeout: int = 30) -> subprocess.CompletedProcess:
        """Execute an ADB command and return the result."""
        cmd = [get_adb_path()] + list(args)
        try:
            return subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout,
                creationflags=(subprocess.CREATE_NO_WINDOW
                               if os.name == "nt" else 0)
            )
        except subprocess.TimeoutExpired:
            return subprocess.CompletedProcess(
                cmd, returncode=-1, stdout="", stderr="Timeout"
            )
        except FileNotFoundError:
            return subprocess.CompletedProcess(
                cmd, returncode=-1, stdout="", stderr="ADB not found"
            )

    def _log(self, msg: str):
        if self.on_log:
            self.on_log(f"[ADB] {msg}")

    # ── Connection ──

    def connect(self, retries: int = 15, delay: float = 3.0) -> bool:
        """Connect to the Android VM via ADB TCP.

        Retries several times to allow the VM to finish booting.

        Args:
            retries: Max connection attempts.
            delay: Seconds between attempts.

        Returns:
            True if successfully connected.
        """
        self._log(f"Connecting to {self.address}...")

        for attempt in range(1, retries + 1):
            self._log(f"Attempt {attempt}/{retries}...")
            result = self._run("connect", self.address)
            output = result.stdout.lower() + result.stderr.lower()

            if "connected" in output and "cannot" not in output:
                self._connected = True
                self._log(f"✓ Connected to {self.address}")
                return True

            if attempt < retries:
                self._log(f"  Waiting {delay}s before retry...")
                time.sleep(delay)

        self._log("✗ Failed to connect after all retries.")
        self._connected = False
        return False

    def disconnect(self):
        """Disconnect from the Android VM."""
        self._run("disconnect", self.address)
        self._connected = False
        self._log("Disconnected.")

    def kill_server(self):
        """Kill the ADB server."""
        self._run("kill-server")
        self._connected = False
        self._log("ADB server killed.")

    # ── Status ──

    @property
    def is_connected(self) -> bool:
        """Check if the device is currently connected and responsive."""
        result = self._run("devices", timeout=5)
        return (
            self.address in result.stdout
            and "device" in result.stdout.split(self.address)[-1]
            if self.address in result.stdout
            else False
        )

    def wait_for_boot(self, timeout: int = 120) -> bool:
        """Wait for the Android system to finish booting.

        Args:
            timeout: Maximum seconds to wait.

        Returns:
            True if the boot completed within the timeout.
        """
        self._log("Waiting for Android boot to complete...")
        start = time.time()
        while time.time() - start < timeout:
            result = self._run(
                "-s", self.address, "shell",
                "getprop", "sys.boot_completed", timeout=5
            )
            if result.stdout.strip() == "1":
                self._log("✓ Android boot completed.")
                return True
            time.sleep(2)
        self._log("✗ Boot timeout.")
        return False

    # ── APK Management ──

    def install_apk(self, apk_path: str) -> tuple[bool, str]:
        """Install an APK file on the connected device.

        Args:
            apk_path: Path to the .apk file.

        Returns:
            Tuple of (success: bool, message: str).
        """
        if not os.path.exists(apk_path):
            return False, f"File not found: {apk_path}"

        filename = os.path.basename(apk_path)
        self._log(f"Installing {filename}...")

        result = self._run(
            "-s", self.address, "install", "-r", apk_path, timeout=120
        )
        output = result.stdout.strip() + " " + result.stderr.strip()
        success = "success" in output.lower()

        if success:
            self._log(f"✓ {filename} installed successfully.")
        else:
            self._log(f"✗ {filename} failed: {output}")

        return success, output

    def uninstall_package(self, package_name: str) -> tuple[bool, str]:
        """Uninstall a package by name.

        Args:
            package_name: e.g. 'com.example.app'

        Returns:
            Tuple of (success, message).
        """
        self._log(f"Uninstalling {package_name}...")
        result = self._run(
            "-s", self.address, "uninstall", package_name, timeout=30
        )
        output = result.stdout.strip()
        success = "success" in output.lower()
        return success, output

    def list_packages(self, third_party_only: bool = True) -> list[str]:
        """List installed packages.

        Args:
            third_party_only: If True, only list user-installed packages.

        Returns:
            List of package names.
        """
        args = ["-s", self.address, "shell", "pm", "list", "packages"]
        if third_party_only:
            args.append("-3")

        result = self._run(*args, timeout=15)
        if result.returncode != 0:
            return []

        return [
            line.replace("package:", "").strip()
            for line in result.stdout.splitlines()
            if line.startswith("package:")
        ]

    # ── Device Info ──

    def get_device_info(self) -> dict:
        """Fetch basic device properties via getprop."""
        props = {}
        keys = [
            "ro.build.version.release",
            "ro.product.model",
            "ro.build.display.id",
            "dalvik.vm.heapsize",
            "ro.product.cpu.abi",
            "persist.sys.timezone",
        ]
        for key in keys:
            result = self._run(
                "-s", self.address, "shell", "getprop", key, timeout=5
            )
            props[key] = result.stdout.strip() if result.returncode == 0 else "N/A"
        return props

    def get_screen_resolution(self) -> Optional[str]:
        """Get the current display resolution."""
        result = self._run(
            "-s", self.address, "shell", "wm", "size", timeout=5
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if "Physical size" in line or "Override size" in line:
                    return line.split(":")[-1].strip()
        return None

    # ── Optimization ──

    def apply_optimizations(self) -> list[tuple[str, bool]]:
        """Apply performance optimization commands via ADB shell.

        Returns:
            List of (command, success) tuples.
        """
        self._log("Applying performance optimizations...")
        results = []

        for cmd_str in OPTIMIZATION_ADB_COMMANDS:
            result = self._run(
                "-s", self.address, "shell", *cmd_str.split(), timeout=10
            )
            success = result.returncode == 0
            results.append((cmd_str, success))
            status = "✓" if success else "✗"
            self._log(f"  {status} {cmd_str}")

        self._log(f"Optimization complete: {sum(1 for _, s in results if s)}/{len(results)} applied.")
        return results

    def push_build_prop_tweaks(self) -> bool:
        """Push build.prop performance tweaks to the device.

        Requires root access. Appends tweaks to /system/build.prop.

        Returns:
            True if tweaks were applied.
        """
        self._log("Pushing build.prop tweaks (requires root)...")

        # Remount /system as read-write
        self._run("-s", self.address, "shell", "su", "-c",
                  "mount -o rw,remount /system", timeout=10)

        # Pull current build.prop
        result = self._run(
            "-s", self.address, "shell", "su", "-c",
            "cat /system/build.prop", timeout=10
        )

        if result.returncode != 0:
            self._log("✗ Could not read build.prop (root required).")
            return False

        # Check if tweaks are already applied
        if "APK-Lator Performance Tweaks" in result.stdout:
            self._log("✓ Tweaks already applied.")
            return True

        # Append tweaks
        for line in BUILD_PROP_TWEAKS.splitlines():
            if line.strip() and not line.strip().startswith("#"):
                escaped = line.replace("=", "\\=")
                self._run(
                    "-s", self.address, "shell", "su", "-c",
                    f"echo '{line}' >> /system/build.prop", timeout=5
                )

        self._log("✓ build.prop tweaks applied. Reboot required.")
        return True

    def reboot(self):
        """Reboot the Android device."""
        self._log("Rebooting device...")
        self._run("-s", self.address, "reboot", timeout=10)
        self._connected = False

    # ── File Operations ──

    def push_file(self, local_path: str, remote_path: str) -> bool:
        """Push a file from host to device."""
        result = self._run(
            "-s", self.address, "push", local_path, remote_path, timeout=60
        )
        return result.returncode == 0

    def pull_file(self, remote_path: str, local_path: str) -> bool:
        """Pull a file from device to host."""
        result = self._run(
            "-s", self.address, "pull", remote_path, local_path, timeout=60
        )
        return result.returncode == 0

    def shell(self, command: str) -> str:
        """Execute a raw shell command on the device."""
        result = self._run(
            "-s", self.address, "shell", command, timeout=15
        )
        return result.stdout.strip()
