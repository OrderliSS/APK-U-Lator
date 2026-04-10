"""APK-Lator design system — color palette, fonts, and theme configuration.

Provides a cohesive dark-mode cyberpunk aesthetic across the entire GUI.
"""
import customtkinter as ctk


# ═══════════════════════════════════════════════════
#  Color Palette
# ═══════════════════════════════════════════════════

class Colors:
    """Centralized color tokens for the APK-Lator UI."""

    # Accent colors
    PRIMARY = "#e94560"          # Neon red-pink
    SUCCESS = "#00b894"          # Mint green
    WARNING = "#fdcb6e"          # Warm yellow
    INFO = "#6c5ce7"             # Royal purple
    DANGER = "#ff6b6b"           # Soft red
    CYAN = "#4ecdc4"             # Teal cyan
    ORANGE = "#e17055"           # Warm orange

    # Backgrounds
    BG_DARK = "#0f0f1a"         # Deepest background
    BG_SIDEBAR = "#1a1a2e"      # Sidebar panel
    BG_CARD = "#1a1a2e"         # Card/panel background
    BG_INPUT = "#12121f"        # Input fields, text areas
    BG_HOVER = "#16213e"        # Hover state
    BG_ELEVATED = "#222240"     # Elevated elements

    # Text
    TEXT_PRIMARY = "#e0e0e0"    # Main text
    TEXT_SECONDARY = "#a0a0b0"  # Subtitles
    TEXT_MUTED = "#666680"      # Disabled/muted
    TEXT_LOG = "#a0ffa0"        # Log output (matrix green)
    TEXT_LOG_ERROR = "#ff6b6b"  # Error logs
    TEXT_LOG_WARN = "#fdcb6e"   # Warning logs

    # Borders
    BORDER = "#333355"          # Subtle borders
    BORDER_ACTIVE = "#e94560"   # Active/focused borders

    # Gradients (for manual painting if needed)
    GRADIENT_START = "#e94560"
    GRADIENT_END = "#6c5ce7"


# ═══════════════════════════════════════════════════
#  Font Configuration
# ═══════════════════════════════════════════════════

class Fonts:
    """Font presets for consistent typography."""

    @staticmethod
    def heading_xl() -> ctk.CTkFont:
        return ctk.CTkFont(family="Segoe UI", size=28, weight="bold")

    @staticmethod
    def heading_lg() -> ctk.CTkFont:
        return ctk.CTkFont(family="Segoe UI", size=22, weight="bold")

    @staticmethod
    def heading_md() -> ctk.CTkFont:
        return ctk.CTkFont(family="Segoe UI", size=18, weight="bold")

    @staticmethod
    def heading_sm() -> ctk.CTkFont:
        return ctk.CTkFont(family="Segoe UI", size=15, weight="bold")

    @staticmethod
    def body() -> ctk.CTkFont:
        return ctk.CTkFont(family="Segoe UI", size=13)

    @staticmethod
    def body_sm() -> ctk.CTkFont:
        return ctk.CTkFont(family="Segoe UI", size=11)

    @staticmethod
    def mono() -> ctk.CTkFont:
        return ctk.CTkFont(family="Consolas", size=12)

    @staticmethod
    def mono_sm() -> ctk.CTkFont:
        return ctk.CTkFont(family="Consolas", size=11)

    @staticmethod
    def nav() -> ctk.CTkFont:
        return ctk.CTkFont(family="Segoe UI", size=14)

    @staticmethod
    def logo() -> ctk.CTkFont:
        return ctk.CTkFont(family="Segoe UI", size=22, weight="bold")

    @staticmethod
    def badge() -> ctk.CTkFont:
        return ctk.CTkFont(family="Segoe UI", size=10, weight="bold")


# ═══════════════════════════════════════════════════
#  Theme Application
# ═══════════════════════════════════════════════════

def apply_theme():
    """Apply the APK-Lator dark cyberpunk theme globally."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")


# ═══════════════════════════════════════════════════
#  Reusable Style Helpers
# ═══════════════════════════════════════════════════

def styled_button(
    parent,
    text: str,
    command=None,
    color: str = Colors.PRIMARY,
    hover: str = None,
    width: int = None,
    height: int = 40,
    **kwargs,
) -> ctk.CTkButton:
    """Create a consistently styled button."""
    if hover is None:
        # Darken the color slightly for hover
        hover = _darken_hex(color, 0.15)

    opts = {
        "text": text,
        "fg_color": color,
        "hover_color": hover,
        "font": Fonts.heading_sm(),
        "height": height,
        "corner_radius": 8,
        "border_width": 0,
    }
    if command:
        opts["command"] = command
    if width:
        opts["width"] = width
    opts.update(kwargs)

    return ctk.CTkButton(parent, **opts)


def styled_card(parent, **kwargs) -> ctk.CTkFrame:
    """Create a styled card panel."""
    defaults = {
        "fg_color": Colors.BG_CARD,
        "corner_radius": 12,
        "border_width": 1,
        "border_color": Colors.BORDER,
    }
    defaults.update(kwargs)
    return ctk.CTkFrame(parent, **defaults)


def styled_label(
    parent,
    text: str,
    color: str = Colors.TEXT_PRIMARY,
    font=None,
    **kwargs,
) -> ctk.CTkLabel:
    """Create a consistently styled label."""
    if font is None:
        font = Fonts.body()
    return ctk.CTkLabel(parent, text=text, text_color=color, font=font, **kwargs)


# ═══════════════════════════════════════════════════
#  Color Utilities
# ═══════════════════════════════════════════════════

def _darken_hex(hex_color: str, factor: float = 0.15) -> str:
    """Darken a hex color by a percentage factor."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    r = max(0, int(r * (1 - factor)))
    g = max(0, int(g * (1 - factor)))
    b = max(0, int(b * (1 - factor)))

    return f"#{r:02x}{g:02x}{b:02x}"


def _lighten_hex(hex_color: str, factor: float = 0.15) -> str:
    """Lighten a hex color by a percentage factor."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    r = min(255, int(r + (255 - r) * factor))
    g = min(255, int(g + (255 - g) * factor))
    b = min(255, int(b + (255 - b) * factor))

    return f"#{r:02x}{g:02x}{b:02x}"
