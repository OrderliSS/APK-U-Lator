"""APK-Lator Setup Script — Downloads dependencies and prepares the environment.

Automates:
  1. Python dependency installation (customtkinter, Pillow)
  2. ADB Platform Tools download & extraction
  3. QEMU availability check
  4. Virtual disk image creation (qcow2)
  5. Android-x86 ISO download guidance

Usage:
    python setup.py
"""
import os
import sys
import platform
import subprocess
import urllib.request
import zipfile
import shutil

# ═══════════════════════════════════════════════════
#  Configuration
# ═══════════════════════════════════════════════════

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
VM_DIR = os.path.join(PROJECT_ROOT, "vm")
TOOLS_DIR = os.path.join(PROJECT_ROOT, "tools")
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")

ADB_WINDOWS_URL = (
    "https://dl.google.com/android/repository/"
    "platform-tools-latest-windows.zip"
)
ADB_LINUX_URL = (
    "https://dl.google.com/android/repository/"
    "platform-tools-latest-linux.zip"
)
ANDROID_ISO_URL = (
    "https://sourceforge.net/projects/android-x86/files/"
    "Release%209.0/android-x86_64-9.0-r2.iso/download"
)


# ═══════════════════════════════════════════════════
#  Utilities
# ═══════════════════════════════════════════════════

def print_banner():
    print()
    print("  ╔═══════════════════════════════════════════════════╗")
    print("  ║         🤖  APK-Lator  Setup  Wizard            ║")
    print("  ║         Lightweight Android Emulator             ║")
    print("  ║         QEMU + Android-x86 + Python GUI          ║")
    print("  ╚═══════════════════════════════════════════════════╝")
    print()


def print_step(n: int, total: int, label: str):
    print(f"\n  [{n}/{total}] {label}")
    print(f"  {'─' * 45}")


def print_ok(msg: str):
    print(f"    ✓ {msg}")


def print_warn(msg: str):
    print(f"    ⚠ {msg}")


def print_err(msg: str):
    print(f"    ✗ {msg}")


def download_file(url: str, dest: str, label: str):
    """Download a file with progress display."""
    if os.path.exists(dest):
        print_ok(f"{label} already downloaded, skipping.")
        return True

    print(f"    ⬇ Downloading {label}...")
    try:
        def _progress(count, block_size, total_size):
            if total_size > 0:
                pct = min(int(count * block_size * 100 / total_size), 100)
                bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
                print(f"\r    [{bar}] {pct}%", end="", flush=True)

        urllib.request.urlretrieve(url, dest, reporthook=_progress)
        print()
        print_ok(f"{label} downloaded.")
        return True
    except Exception as e:
        print()
        print_err(f"Download failed: {e}")
        return False


# ═══════════════════════════════════════════════════
#  Setup Steps
# ═══════════════════════════════════════════════════

TOTAL_STEPS = 5


def ensure_directories():
    """Create required project directories."""
    for d in [VM_DIR, TOOLS_DIR, ASSETS_DIR]:
        os.makedirs(d, exist_ok=True)


def step_python_deps():
    """Install Python dependencies from requirements.txt."""
    print_step(1, TOTAL_STEPS, "Installing Python Dependencies")

    req_file = os.path.join(PROJECT_ROOT, "requirements.txt")
    if not os.path.exists(req_file):
        print_err("requirements.txt not found!")
        return False

    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", req_file],
            stdout=subprocess.DEVNULL if "--quiet" in sys.argv else None,
        )
        print_ok("Python dependencies installed.")
        return True
    except subprocess.CalledProcessError as e:
        print_err(f"pip install failed: {e}")
        return False


def step_setup_adb():
    """Download and extract ADB Platform Tools."""
    print_step(2, TOTAL_STEPS, "Setting Up ADB Platform Tools")

    # Check if already in PATH
    if shutil.which("adb"):
        print_ok("ADB already available in PATH.")
        return True

    # Check bundled
    ext = ".exe" if platform.system() == "Windows" else ""
    bundled = os.path.join(TOOLS_DIR, "platform-tools", f"adb{ext}")
    if os.path.exists(bundled):
        print_ok("ADB already in tools/ folder.")
        return True

    # Download
    is_win = platform.system() == "Windows"
    url = ADB_WINDOWS_URL if is_win else ADB_LINUX_URL
    zip_path = os.path.join(TOOLS_DIR, "platform-tools.zip")

    if download_file(url, zip_path, "ADB Platform Tools"):
        print("    📦 Extracting...")
        try:
            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(TOOLS_DIR)
            os.remove(zip_path)
            print_ok("ADB extracted to tools/platform-tools/")
            return True
        except Exception as e:
            print_err(f"Extraction failed: {e}")
            return False

    return False


def step_check_qemu():
    """Check if QEMU is installed and accessible."""
    print_step(3, TOTAL_STEPS, "Checking QEMU Installation")

    qemu_path = shutil.which("qemu-system-x86_64")
    if qemu_path:
        # Get version
        try:
            result = subprocess.run(
                [qemu_path, "--version"],
                capture_output=True, text=True, timeout=10
            )
            version_line = result.stdout.splitlines()[0] if result.stdout else "Unknown"
            print_ok(f"QEMU found: {version_line}")
            return True
        except Exception:
            print_ok(f"QEMU found at: {qemu_path}")
            return True

    # Check bundled (Windows)
    bundled = os.path.join(TOOLS_DIR, "qemu", "qemu-system-x86_64.exe")
    if os.path.exists(bundled):
        print_ok(f"QEMU found in tools/: {bundled}")
        return True

    # Not found — provide install instructions
    print_warn("QEMU not found!")
    print()
    if platform.system() == "Windows":
        print("    Install QEMU for Windows:")
        print("      Option 1: winget install SoftwareFreedomConservancy.QEMU")
        print("      Option 2: Download from https://qemu.weilnetz.de/w64/")
        print()
        print("    After installation, ensure qemu-system-x86_64.exe is in PATH")
        print("    or place it in the tools/qemu/ directory.")
    else:
        print("    Install QEMU:")
        print("      Debian/Ubuntu: sudo apt install qemu-system-x86 qemu-utils")
        print("      Arch Linux:    sudo pacman -S qemu-full")
        print("      Fedora:        sudo dnf install qemu-system-x86")

    return False


def step_create_disk():
    """Create the virtual disk image."""
    print_step(4, TOTAL_STEPS, "Creating Virtual Disk Image")

    disk_path = os.path.join(VM_DIR, "android.qcow2")
    if os.path.exists(disk_path):
        size_mb = round(os.path.getsize(disk_path) / (1024 * 1024), 1)
        print_ok(f"Disk image exists ({size_mb} MB on disk).")
        return True

    qemu_img = shutil.which("qemu-img")
    if not qemu_img:
        bundled = os.path.join(TOOLS_DIR, "qemu", "qemu-img.exe")
        if os.path.exists(bundled):
            qemu_img = bundled
        else:
            print_warn("qemu-img not found — disk will be created on first launch.")
            return False

    try:
        subprocess.run(
            [qemu_img, "create", "-f", "qcow2", disk_path, "20G"],
            check=True, capture_output=True
        )
        print_ok("Created 20GB qcow2 disk at vm/android.qcow2")
        return True
    except subprocess.CalledProcessError as e:
        print_err(f"Disk creation failed: {e.stderr}")
        return False


def step_download_iso():
    """Guide the user to download the Android-x86 ISO."""
    print_step(5, TOTAL_STEPS, "Android-x86 ISO")

    iso_path = os.path.join(VM_DIR, "android-x86_64-9.0-r2.iso")
    if os.path.exists(iso_path) and os.path.getsize(iso_path) > 100_000_000:
        size_mb = round(os.path.getsize(iso_path) / (1024 * 1024), 1)
        print_ok(f"ISO already present ({size_mb} MB).")
        return True

    print_warn("Android-x86 ISO not found (it's ~900MB).")
    print()
    print("    Download Android-x86 9.0-r2 (Pie) from:")
    print(f"      {ANDROID_ISO_URL}")
    print()
    print(f"    Save it to:")
    print(f"      {iso_path}")
    print()
    print("    Alternative mirrors:")
    print("      https://www.fosshub.com/Android-x86.html")
    print("      https://osdn.net/projects/android-x86/releases/71931")

    return False


def print_summary(results: dict):
    """Print the final setup summary."""
    print()
    print("  ╔═══════════════════════════════════════════════════╗")
    print("  ║               📋 Setup Summary                   ║")
    print("  ╠═══════════════════════════════════════════════════╣")

    for step, ok in results.items():
        status = "✓" if ok else "✗"
        emoji = "🟢" if ok else "🔴"
        print(f"  ║  {emoji}  {status}  {step:<40} ║")

    print("  ╚═══════════════════════════════════════════════════╝")

    all_ok = all(results.values())

    print()
    if all_ok:
        print("  ✅ All checks passed! Ready to launch.")
    else:
        print("  ⚠  Some items need attention (see above).")

    print()
    print("  ╔═══════════════════════════════════════════════════╗")
    print("  ║               🚀 Next Steps                      ║")
    print("  ╠═══════════════════════════════════════════════════╣")
    print("  ║                                                   ║")
    print("  ║  1. Ensure QEMU is installed                      ║")
    print("  ║  2. Download Android-x86 ISO to vm/ folder        ║")
    print("  ║  3. Launch the app:                               ║")
    print("  ║                                                   ║")
    print("  ║     python __main__.py                            ║")
    print("  ║                                                   ║")
    print("  ║  4. Click '💿 First Boot' for OS installation     ║")
    print("  ║  5. After install, use '▶ Start VM'               ║")
    print("  ║  6. Click '🔗 Connect ADB' then install APKs!    ║")
    print("  ║                                                   ║")
    print("  ╚═══════════════════════════════════════════════════╝")
    print()


# ═══════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════

def main():
    print_banner()
    ensure_directories()

    results = {}
    results["Python Dependencies"] = step_python_deps()
    results["ADB Platform Tools"] = step_setup_adb()
    results["QEMU Installation"] = step_check_qemu()
    results["Virtual Disk Image"] = step_create_disk()
    results["Android-x86 ISO"] = step_download_iso()

    print_summary(results)


if __name__ == "__main__":
    main()
