"""OS detection, path resolution, and hardware acceleration capability checks."""
import platform
import subprocess
import os
import sys
import shutil
import json
from typing import Optional


def detect_platform() -> str:
    """Return 'windows' or 'linux'."""
    return "windows" if os.name == "nt" else "linux"


def get_project_root() -> str:
    """Return the absolute path to the APK-Lator project root."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_vm_dir() -> str:
    return os.path.join(get_project_root(), "vm")


def get_tools_dir() -> str:
    return os.path.join(get_project_root(), "tools")


# ═══════════════════════════════════════════════════
#  Binary Path Resolution
# ═══════════════════════════════════════════════════

def get_qemu_path() -> str:
    """Resolve the path to qemu-system-x86_64."""
    root = get_project_root()
    if detect_platform() == "windows":
        bundled = os.path.join(root, "tools", "qemu", "qemu-system-x86_64.exe")
        if os.path.exists(bundled):
            return bundled
    system = shutil.which("qemu-system-x86_64")
    if system:
        return system
    return "qemu-system-x86_64"


def get_qemu_img_path() -> str:
    """Resolve the path to qemu-img."""
    root = get_project_root()
    if detect_platform() == "windows":
        bundled = os.path.join(root, "tools", "qemu", "qemu-img.exe")
        if os.path.exists(bundled):
            return bundled
    system = shutil.which("qemu-img")
    if system:
        return system
    return "qemu-img"


def get_adb_path() -> str:
    """Resolve the path to adb."""
    root = get_project_root()
    ext = ".exe" if detect_platform() == "windows" else ""
    bundled = os.path.join(root, "tools", "platform-tools", f"adb{ext}")
    if os.path.exists(bundled):
        return bundled
    system = shutil.which("adb")
    if system:
        return system
    return "adb"


# ═══════════════════════════════════════════════════
#  Hardware Acceleration Detection
# ═══════════════════════════════════════════════════

def get_accelerator() -> str:
    """Detect the best available hardware accelerator.

    Returns one of: 'kvm', 'whpx', 'tcg' (software fallback).
    """
    plat = detect_platform()

    if plat == "linux":
        if os.path.exists("/dev/kvm"):
            return "kvm"

    elif plat == "windows":
        try:
            result = subprocess.run(
                [
                    "powershell", "-NoProfile", "-Command",
                    "(Get-WindowsOptionalFeature -Online "
                    "-FeatureName HypervisorPlatform).State"
                ],
                capture_output=True, text=True, timeout=15,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if "Enabled" in result.stdout:
                return "whpx"
        except Exception:
            pass

    return "tcg"


def check_virgl_support() -> bool:
    """Test if the QEMU binary was compiled with virtio-vga/virgl support."""
    try:
        result = subprocess.run(
            [get_qemu_path(), "-device", "help"],
            capture_output=True, text=True, timeout=10,
            creationflags=(subprocess.CREATE_NO_WINDOW
                           if os.name == "nt" else 0)
        )
        return "virtio-vga" in result.stdout
    except Exception:
        return False


def check_qemu_installed() -> bool:
    """Check if QEMU is available."""
    try:
        result = subprocess.run(
            [get_qemu_path(), "--version"],
            capture_output=True, text=True, timeout=10,
            creationflags=(subprocess.CREATE_NO_WINDOW
                           if os.name == "nt" else 0)
        )
        return result.returncode == 0
    except Exception:
        return False


def get_qemu_version() -> Optional[str]:
    """Return the installed QEMU version string."""
    try:
        result = subprocess.run(
            [get_qemu_path(), "--version"],
            capture_output=True, text=True, timeout=10,
            creationflags=(subprocess.CREATE_NO_WINDOW
                           if os.name == "nt" else 0)
        )
        if result.returncode == 0:
            # Parse: "QEMU emulator version X.Y.Z ..."
            for line in result.stdout.splitlines():
                if "version" in line.lower():
                    parts = line.split("version")
                    if len(parts) > 1:
                        return parts[1].strip().split()[0]
        return None
    except Exception:
        return None


def check_adb_installed() -> bool:
    """Check if ADB is available."""
    try:
        result = subprocess.run(
            [get_adb_path(), "version"],
            capture_output=True, text=True, timeout=10,
            creationflags=(subprocess.CREATE_NO_WINDOW
                           if os.name == "nt" else 0)
        )
        return result.returncode == 0
    except Exception:
        return False


# ═══════════════════════════════════════════════════
#  Settings Management
# ═══════════════════════════════════════════════════

def load_settings() -> dict:
    """Load settings from config/settings.json, with fallback defaults."""
    settings_path = os.path.join(get_project_root(), "config", "settings.json")
    defaults = {
        "vm": {
            "cores": 4,
            "ram_mb": 4096,
            "disk_path": os.path.join("vm", "android.qcow2"),
            "iso_path": os.path.join("vm", "android-x86_64-9.0-r2.iso"),
            "disk_size_gb": 20,
            "enable_audio": True,
            "display_backend": "gtk",
            "virgl": True,
        },
        "adb": {
            "host": "127.0.0.1",
            "port": 5555,
            "connect_retries": 15,
            "connect_delay_sec": 3,
        },
        "ui": {
            "theme": "dark",
            "accent_color": "#e94560",
            "window_width": 1000,
            "window_height": 700,
        },
    }
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r") as f:
                user_settings = json.load(f)
            # Deep merge user settings over defaults
            for section in defaults:
                if section in user_settings:
                    defaults[section].update(user_settings[section])
        except (json.JSONDecodeError, IOError):
            pass
    return defaults


def save_settings(settings: dict) -> bool:
    """Persist settings to config/settings.json."""
    settings_path = os.path.join(get_project_root(), "config", "settings.json")
    try:
        os.makedirs(os.path.dirname(settings_path), exist_ok=True)
        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=2)
        return True
    except IOError:
        return False


# ═══════════════════════════════════════════════════
#  System Info Summary
# ═══════════════════════════════════════════════════

def get_system_info() -> dict:
    """Return a summary dict of the host system capabilities."""
    return {
        "platform": detect_platform(),
        "os": platform.system(),
        "os_version": platform.version(),
        "arch": platform.machine(),
        "python": sys.version.split()[0],
        "accelerator": get_accelerator(),
        "qemu_installed": check_qemu_installed(),
        "qemu_version": get_qemu_version(),
        "virgl_support": check_virgl_support(),
        "adb_installed": check_adb_installed(),
        "cpu_count": os.cpu_count(),
    }
