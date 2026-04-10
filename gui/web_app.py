"""APK-Lator — pywebview entry point.

Opens a native Windows window rendering the HTML/CSS/JS frontend,
with the Python backend exposed as window.pywebview.api in JavaScript.
"""
import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import webview
from gui.api import APKLatorAPI


def main():
    """Launch the APK U Lator native window."""
    api = APKLatorAPI()

    html_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "static", "index.html"
    )

    # Normalise to forward slashes for file:// URL on Windows
    html_url = "file:///" + html_path.replace("\\", "/")

    window = webview.create_window(
        title="APK U Lator",
        url=html_url,
        js_api=api,
        width=1440,
        height=900,
        min_size=(1024, 700),
        background_color="#0B0E14",
        text_select=False,
        zoomable=False,
    )

    def on_closed():
        """Clean up resources when the window is closed."""
        api.cleanup()

    window.events.closed += on_closed

    # Start the webview event loop (blocks until window closes)
    webview.start(debug=False, private_mode=False)


if __name__ == "__main__":
    main()
