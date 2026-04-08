"""Virtual disk image and ISO management for APK-Lator."""
import subprocess
import os
import shutil
from typing import Optional, Callable
from core.platform_utils import get_qemu_img_path, get_project_root


class DiskManager:
    """Manages qcow2 virtual disk images and ISO files."""

    def __init__(self, on_log: Optional[Callable[[str], None]] = None):
        self.on_log = on_log

    def _log(self, msg: str):
        if self.on_log:
            self.on_log(f"[DISK] {msg}")

    def create_disk(self, path: str, size_gb: int = 20) -> bool:
        """Create a qcow2 virtual disk image.

        Args:
            path: Full path for the new .qcow2 file.
            size_gb: Disk size in gigabytes.

        Returns:
            True if the disk was created or already exists.
        """
        if os.path.exists(path):
            self._log(f"Disk already exists: {path}")
            return True

        # Ensure parent directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)

        qemu_img = get_qemu_img_path()
        cmd = [qemu_img, "create", "-f", "qcow2", path, f"{size_gb}G"]
        self._log(f"Creating {size_gb}GB qcow2 disk at {path}...")

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30,
                creationflags=(subprocess.CREATE_NO_WINDOW
                               if os.name == "nt" else 0)
            )
            if result.returncode == 0:
                self._log(f"✓ Disk created successfully ({size_gb}GB)")
                return True
            else:
                self._log(f"✗ Failed: {result.stderr.strip()}")
                return False
        except FileNotFoundError:
            self._log("✗ qemu-img not found. Is QEMU installed?")
            return False
        except subprocess.TimeoutExpired:
            self._log("✗ Disk creation timed out.")
            return False

    def get_disk_info(self, path: str) -> Optional[dict]:
        """Get information about a qcow2 disk image.

        Returns:
            dict with 'size', 'actual_size', 'format' or None on failure.
        """
        if not os.path.exists(path):
            return None

        qemu_img = get_qemu_img_path()
        try:
            result = subprocess.run(
                [qemu_img, "info", "--output=json", path],
                capture_output=True, text=True, timeout=10,
                creationflags=(subprocess.CREATE_NO_WINDOW
                               if os.name == "nt" else 0)
            )
            if result.returncode == 0:
                import json
                info = json.loads(result.stdout)
                return {
                    "virtual_size": info.get("virtual-size", 0),
                    "actual_size": info.get("actual-size", 0),
                    "format": info.get("format", "unknown"),
                    "virtual_size_gb": round(
                        info.get("virtual-size", 0) / (1024 ** 3), 1
                    ),
                    "actual_size_mb": round(
                        info.get("actual-size", 0) / (1024 ** 2), 1
                    ),
                }
        except Exception:
            pass
        return None

    def create_snapshot(self, disk_path: str, name: str = "clean_install") -> bool:
        """Create a named snapshot of the disk image.

        Args:
            disk_path: Path to the qcow2 image.
            name: Snapshot name (e.g. 'clean_install').

        Returns:
            True on success.
        """
        qemu_img = get_qemu_img_path()
        cmd = [qemu_img, "snapshot", "-c", name, disk_path]
        self._log(f"Creating snapshot '{name}'...")

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30,
                creationflags=(subprocess.CREATE_NO_WINDOW
                               if os.name == "nt" else 0)
            )
            if result.returncode == 0:
                self._log(f"✓ Snapshot '{name}' created.")
                return True
            else:
                self._log(f"✗ Snapshot failed: {result.stderr.strip()}")
                return False
        except Exception as e:
            self._log(f"✗ Snapshot error: {e}")
            return False

    def restore_snapshot(self, disk_path: str, name: str = "clean_install") -> bool:
        """Restore a named snapshot.

        Args:
            disk_path: Path to the qcow2 image.
            name: Snapshot name to restore.

        Returns:
            True on success.
        """
        qemu_img = get_qemu_img_path()
        cmd = [qemu_img, "snapshot", "-a", name, disk_path]
        self._log(f"Restoring snapshot '{name}'...")

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60,
                creationflags=(subprocess.CREATE_NO_WINDOW
                               if os.name == "nt" else 0)
            )
            if result.returncode == 0:
                self._log(f"✓ Snapshot '{name}' restored.")
                return True
            else:
                self._log(f"✗ Restore failed: {result.stderr.strip()}")
                return False
        except Exception as e:
            self._log(f"✗ Restore error: {e}")
            return False

    def list_snapshots(self, disk_path: str) -> list[str]:
        """List all snapshots on a disk image."""
        qemu_img = get_qemu_img_path()
        try:
            result = subprocess.run(
                [qemu_img, "snapshot", "-l", disk_path],
                capture_output=True, text=True, timeout=10,
                creationflags=(subprocess.CREATE_NO_WINDOW
                               if os.name == "nt" else 0)
            )
            if result.returncode == 0:
                names = []
                for line in result.stdout.splitlines()[2:]:  # Skip header
                    parts = line.split()
                    if len(parts) >= 2:
                        names.append(parts[1])
                return names
        except Exception:
            pass
        return []

    def check_iso_exists(self, iso_path: str) -> bool:
        """Check if the Android-x86 ISO is present."""
        return os.path.exists(iso_path) and os.path.getsize(iso_path) > 100_000_000

    def get_disk_path(self) -> str:
        """Return the default disk path."""
        return os.path.join(get_project_root(), "vm", "android.qcow2")

    def get_iso_path(self) -> str:
        """Return the default ISO path."""
        return os.path.join(get_project_root(), "vm", "android-x86_64-9.0-r2.iso")
