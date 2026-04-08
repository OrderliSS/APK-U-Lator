"""APK-Lator default constants and paths."""
import os

# ── Project Paths ──
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VM_DIR = os.path.join(PROJECT_ROOT, "vm")
TOOLS_DIR = os.path.join(PROJECT_ROOT, "tools")
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")

# ── VM Defaults ──
DEFAULT_CORES = 4
DEFAULT_RAM_MB = 4096
DEFAULT_DISK_SIZE_GB = 20
DEFAULT_DISK_NAME = "android.qcow2"
DEFAULT_ISO_NAME = "android-x86_64-9.0-r2.iso"
DEFAULT_DISK_PATH = os.path.join(VM_DIR, DEFAULT_DISK_NAME)
DEFAULT_ISO_PATH = os.path.join(VM_DIR, DEFAULT_ISO_NAME)

# ── ADB Defaults ──
ADB_HOST = "127.0.0.1"
ADB_PORT = 5555
ADB_CONNECT_RETRIES = 15
ADB_CONNECT_DELAY = 3.0

# ── Display ──
DEFAULT_RESOLUTION = "1280x720"
DEFAULT_DISPLAY_BACKEND = "gtk"
DEFAULT_VIRGL = True

# ── Download URLs ──
ADB_WINDOWS_URL = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
ADB_LINUX_URL = "https://dl.google.com/android/repository/platform-tools-latest-linux.zip"
ANDROID_ISO_URL = (
    "https://sourceforge.net/projects/android-x86/files/"
    "Release%209.0/android-x86_64-9.0-r2.iso/download"
)

# ── UI Theme Defaults ──
ACCENT_PRIMARY = "#e94560"
ACCENT_SUCCESS = "#00b894"
ACCENT_WARNING = "#ffe66d"
ACCENT_INFO = "#6c5ce7"
ACCENT_DANGER = "#ff6b6b"
ACCENT_CYAN = "#4ecdc4"

BG_DARK = "#0f0f1a"
BG_SIDEBAR = "#1a1a2e"
BG_CARD = "#1a1a2e"
BG_INPUT = "#12121f"
BG_HOVER = "#16213e"

TEXT_PRIMARY = "#e0e0e0"
TEXT_SECONDARY = "#a0a0b0"
TEXT_MUTED = "#666680"
TEXT_LOG = "#a0ffa0"

# ── Android Optimization ──
BUILD_PROP_TWEAKS = """
# === APK-Lator Performance Tweaks ===
logcat.live=disable
profiler.force_disable_err_rpt=1
profiler.force_disable_ulog=1
persist.sys.purgeable_assets=1
dalvik.vm.heapsize=256m
dalvik.vm.heapgrowthlimit=128m
dalvik.vm.heapminfree=2m
dalvik.vm.heapmaxfree=8m
dalvik.vm.heaptargetutilization=0.75
ro.config.nocheckin=1
ro.kernel.android.checkjni=0
ro.debuggable=0
ro.sys.fw.bg_apps_limit=4
debug.sf.nobootanimation=1
persist.sys.ui.hw=1
""".strip()

OPTIMIZATION_ADB_COMMANDS = [
    "settings put global window_animation_scale 0",
    "settings put global transition_animation_scale 0",
    "settings put global animator_duration_scale 0",
    "settings put global package_verifier_enable 0",
    "settings put global stay_on_while_plugged_in 3",
]

# ── Settings File ──
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")
