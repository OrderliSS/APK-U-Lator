"""APK-Lator — Main GUI Application.

A lightweight, ad-free Android emulator control surface built with CustomTkinter.
Orchestrates QEMU + Android-x86 with an intuitive dark-mode interface.
"""
import customtkinter as ctk
import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.dashboard_frame import DashboardFrame
from gui.apk_installer_frame import ApkInstallerFrame
from gui.settings_frame import SettingsFrame
from gui.log_frame import LogFrame
from gui.theme import Colors, Fonts, apply_theme
from core.platform_utils import load_settings


class APKLatorApp(ctk.CTk):
    """Main application window with sidebar navigation and page routing."""

    def __init__(self):
        super().__init__()
        apply_theme()

        settings = load_settings()
        width = settings["ui"]["window_width"]
        height = settings["ui"]["window_height"]

        self.title("APK-Lator — Android Emulator")
        self.geometry(f"{width}x{height}")
        self.minsize(800, 550)

        # Try to set icon
        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "assets", "icon.ico"
        )
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        # ═══════════════════════════════════════
        #  Sidebar Navigation
        # ═══════════════════════════════════════
        self.sidebar = ctk.CTkFrame(
            self, width=220, corner_radius=0, fg_color=Colors.BG_SIDEBAR
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # ── Logo ──
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", pady=(24, 8), padx=16)

        ctk.CTkLabel(
            logo_frame, text="🤖",
            font=ctk.CTkFont(size=32)
        ).pack(side="left", padx=(0, 8))

        logo_text_frame = ctk.CTkFrame(logo_frame, fg_color="transparent")
        logo_text_frame.pack(side="left")

        ctk.CTkLabel(
            logo_text_frame, text="APK-Lator",
            font=Fonts.logo(), text_color=Colors.PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            logo_text_frame, text="Android Emulator",
            font=Fonts.body_sm(), text_color=Colors.TEXT_MUTED
        ).pack(anchor="w")

        # Divider
        divider = ctk.CTkFrame(
            self.sidebar, height=1, fg_color=Colors.BORDER
        )
        divider.pack(fill="x", padx=16, pady=(12, 16))

        # ── Nav Buttons ──
        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        pages = [
            ("🏠", "Dashboard", "dashboard"),
            ("📦", "APK Install", "apk"),
            ("⚙️", "Settings", "settings"),
            ("📋", "Logs", "logs"),
        ]

        for icon, label, key in pages:
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"  {icon}   {label}",
                anchor="w",
                font=Fonts.nav(),
                fg_color="transparent",
                hover_color=Colors.BG_HOVER,
                text_color=Colors.TEXT_SECONDARY,
                height=42,
                corner_radius=8,
                command=lambda k=key: self.show_page(k),
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[key] = btn

        # ── Sidebar Footer ──
        self.sidebar_footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.sidebar_footer.pack(side="bottom", fill="x", padx=16, pady=16)

        ctk.CTkLabel(
            self.sidebar_footer,
            text="v1.0.0 • Open Source",
            font=Fonts.body_sm(),
            text_color=Colors.TEXT_MUTED,
        ).pack()

        ctk.CTkLabel(
            self.sidebar_footer,
            text="QEMU + Android-x86",
            font=Fonts.body_sm(),
            text_color=Colors.TEXT_MUTED,
        ).pack()

        # ═══════════════════════════════════════
        #  Content Area
        # ═══════════════════════════════════════
        self.content = ctk.CTkFrame(
            self, fg_color=Colors.BG_DARK, corner_radius=0
        )
        self.content.pack(side="right", fill="both", expand=True)

        # ═══════════════════════════════════════
        #  Page Frames
        # ═══════════════════════════════════════
        self.dashboard = DashboardFrame(self.content)
        self.apk_installer = ApkInstallerFrame(self.content)
        self.settings_page = SettingsFrame(self.content)
        self.log_page = LogFrame(self.content)

        self.pages = {
            "dashboard": self.dashboard,
            "apk": self.apk_installer,
            "settings": self.settings_page,
            "logs": self.log_page,
        }

        # ── Wire cross-frame references ──
        # Share ADB manager from dashboard to APK installer and settings
        adb_mgr = self.dashboard.get_adb_manager()
        qemu_mgr = self.dashboard.get_qemu_manager()

        self.apk_installer.set_adb(adb_mgr)
        self.settings_page.set_adb(adb_mgr)
        self.settings_page.set_qemu(qemu_mgr)

        # Wire log forwarding: dashboard logs → log page
        original_on_log = self.dashboard._on_log

        def _forward_log(line: str):
            original_on_log(line)
            self.log_page.append_log(line)

        self.dashboard.qemu.on_log = _forward_log
        self.dashboard.adb.on_log = _forward_log
        self.dashboard.disk_mgr.on_log = _forward_log

        # Show initial page
        self.show_page("dashboard")

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def show_page(self, page_key: str):
        """Switch the visible page and update nav highlight."""
        for frame in self.pages.values():
            frame.pack_forget()

        self.pages[page_key].pack(
            fill="both", expand=True, padx=20, pady=20
        )

        # Update nav button styles
        for key, btn in self.nav_buttons.items():
            if key == page_key:
                btn.configure(
                    fg_color=Colors.BG_HOVER,
                    text_color=Colors.PRIMARY
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=Colors.TEXT_SECONDARY
                )

    def _on_close(self):
        """Clean up resources on window close."""
        qemu = self.dashboard.get_qemu_manager()
        if qemu.is_running:
            qemu.stop()

        adb = self.dashboard.get_adb_manager()
        adb.disconnect()

        self.destroy()


def main():
    """Entry point for APK-Lator."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = APKLatorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
