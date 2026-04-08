# 🤖 APK-Lator

**A lightweight, ad-free, open-source Android Emulator for Windows & Linux.**

APK-Lator orchestrates **QEMU** and **Android-x86** through a sleek **Python/CustomTkinter** GUI — giving you a "Bluestacks Light" experience without the bloat, ads, or background resource drain.

---

## ✨ Features

- **Zero Bloat** — No ads, no telemetry, no unnecessary background processes
- **Hardware Accelerated** — WHPX (Windows) / KVM (Linux) for near-native performance
- **virtio-GPU** — OpenGL passthrough via virgl for graphics acceleration
- **One-Click APK Install** — Browse & batch-install APK files through the GUI
- **ADB Integration** — Full ADB connectivity with auto-connect and retry logic
- **Performance Optimization** — Built-in Android tweaks (build.prop, animation disabling, heap tuning)
- **Snapshot Management** — Create and restore VM snapshots for "factory reset"
- **Cross-Platform** — Windows 10/11 and Linux (Ubuntu, Arch, Fedora)
- **Modular Architecture** — Clean separation of QEMU engine, ADB manager, and GUI layers

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│              CustomTkinter GUI              │
│  ┌──────────┬──────────┬─────────┬───────┐  │
│  │Dashboard │APK Inst. │Settings │ Logs  │  │
│  └────┬─────┴────┬─────┴────┬────┴───┬───┘  │
│       │          │          │        │       │
│  ┌────▼──────────▼──────────▼────────▼───┐  │
│  │           Core Engine                  │  │
│  │  ┌────────────┬────────────┬────────┐  │  │
│  │  │QemuManager │AdbManager  │DiskMgr │  │  │
│  │  └─────┬──────┴──────┬─────┴────┬───┘  │  │
│  └────────┼─────────────┼──────────┼──────┘  │
│           │             │          │         │
│     ┌─────▼────┐  ┌─────▼────┐ ┌──▼──────┐  │
│     │  QEMU    │  │   ADB    │ │qemu-img │  │
│     │ Process  │  │ Process  │ │ Process  │  │
│     └─────┬────┘  └─────┬────┘ └─────────┘  │
│           │             │                    │
│     ┌─────▼─────────────▼────────────────┐   │
│     │      Android-x86 9.0 VM (qcow2)   │   │
│     └────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

| Tool | Windows | Linux |
|------|---------|-------|
| **Python 3.10+** | `winget install Python.Python.3.12` | `sudo apt install python3` |
| **QEMU** | `winget install SoftwareFreedomConservancy.QEMU` | `sudo apt install qemu-system-x86` |

### Setup

**Windows:**
```batch
setup.bat
```

**Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

**Or manually:**
```bash
pip install -r requirements.txt
python setup.py
```

### Download Android-x86

Download the [Android-x86 9.0-r2 ISO](https://www.fosshub.com/Android-x86.html) (~900MB) and save it to the `vm/` folder:

```
vm/android-x86_64-9.0-r2.iso
```

### Launch

```bash
python __main__.py
```

### First-Time Setup

1. Click **💿 First Boot (ISO)** to boot from the Android installer
2. Select **Advanced Options → Auto Installation** in the GRUB menu
3. Wait for installation to complete, then the VM will shut down
4. Click **▶ Start VM** for normal boots going forward
5. Click **🔗 Connect ADB** once Android has fully booted
6. Navigate to **APK Install** to install your apps!

---

## 📁 Project Structure

```
APK-Lator/
├── __main__.py              # Entry point
├── setup.py                 # Dependency bootstrapper
├── setup.bat / setup.sh     # One-click setup scripts
├── requirements.txt         # Python deps
│
├── config/
│   ├── defaults.py          # Constants, paths, optimization params
│   └── settings.json        # User-configurable VM settings
│
├── core/
│   ├── platform_utils.py    # OS detection, QEMU/ADB path resolution
│   ├── qemu_manager.py      # VM lifecycle (start/stop/config)
│   ├── adb_manager.py       # ADB connect, APK install, optimizations
│   └── disk_manager.py      # qcow2 creation, snapshots
│
├── gui/
│   ├── app.py               # Main window, navigation, wiring
│   ├── theme.py             # Design tokens, styled components
│   ├── dashboard_frame.py   # VM controls, status cards, log viewer
│   ├── apk_installer_frame.py  # APK browser & batch installer
│   ├── settings_frame.py    # VM config, optimization, system info
│   └── log_frame.py         # Filtered log viewer with export
│
├── vm/                      # Runtime (auto-created)
│   ├── android.qcow2        # Virtual disk
│   └── *.iso                # Android-x86 ISO
│
└── tools/                   # External binaries (auto-downloaded)
    └── platform-tools/      # ADB
```

---

## ⚙️ Configuration

Edit `config/settings.json` or use the **Settings** page in the GUI:

```json
{
  "vm": {
    "cores": 4,
    "ram_mb": 4096,
    "virgl": true,
    "enable_audio": true
  },
  "adb": {
    "port": 5555,
    "connect_retries": 15
  }
}
```

---

## 🔧 QEMU Flags Reference

### Windows (WHPX)
```bash
qemu-system-x86_64 -machine pc,accel=whpx -cpu qemu64 \
  -smp cores=4 -m 4096 -device virtio-vga,virgl=on \
  -display gtk,gl=on -netdev user,hostfwd=tcp::5555-:5555 \
  -device virtio-net-pci -device virtio-blk-pci ...
```

### Linux (KVM)
```bash
qemu-system-x86_64 -machine pc,accel=kvm -cpu host \
  -smp cores=4 -m 4096 -device virtio-vga,virgl=on \
  -display gtk,gl=on -netdev user,hostfwd=tcp::5555-:5555 \
  -device virtio-net-pci -device virtio-blk-pci ...
```

> **Note:** Standard QEMU Windows binaries may not include virgl. The app auto-detects and falls back to software rendering.

---

## 🚀 Performance Optimization

Use the **Settings → Optimization** panel to apply:

### ADB Shell Tweaks (No Root)
- Disable all animations
- Disable package verifier
- Keep screen on while "charging"

### build.prop Tweaks (Root Required)
- Disable logging subsystems
- Constrain Dalvik heap (256MB max)
- Limit background apps to 4
- Disable boot animation
- Force GPU rendering

---

## 📋 Troubleshooting

| Issue | Solution |
|-------|----------|
| "No accelerator found" | Enable Virtualization (VT-x/AMD-V) in BIOS and Windows Hypervisor Platform |
| Black screen on boot | Try disabling virgl in Settings (virgl=off) |
| ADB won't connect | Wait 30-60s after boot, then retry. Check port 5555 isn't in use |
| Slow graphics | Ensure host GPU drivers are updated; virgl requires OpenGL 3.3+ |
| QEMU not found | Install QEMU and add to PATH, or place in `tools/qemu/` |

---

## 📄 License

MIT License — Free for personal and commercial use.

---

## 🤝 Contributing

This is a "vibe code" project — contributions, ideas, and PRs are welcome! The modular architecture makes it easy to add features:

- **New GUI pages** → Add a frame in `gui/` and register in `app.py`
- **New QEMU features** → Extend `core/qemu_manager.py`
- **New ADB operations** → Extend `core/adb_manager.py`

---

*Built with ❤️ using QEMU, Android-x86, Python, and CustomTkinter.*
