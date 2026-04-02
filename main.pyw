from __future__ import annotations

import socket
import threading
import time

import uvicorn
import webview

from app import app


class DialogBridge:
    def __init__(self) -> None:
        self.window = None

    def set_window(self, window: webview.Window) -> None:
        self.window = window

    def choose_file(self):
        return self._dialog(webview.OPEN_DIALOG)

    def choose_multiple(self):
        return self._dialog(webview.OPEN_DIALOG, multiple=True) or []

    def choose_save_path(self, extension=""):
        label = f"Output (*{extension})" if extension else "All files (*.*)"
        return self._dialog(webview.SAVE_DIALOG, file_types=(label, "All files (*.*)"))

    def choose_folder(self):
        return self._dialog(webview.FOLDER_DIALOG)

    def _dialog(self, dialog_type, multiple=False, file_types=None):
        if not self.window:
            return [] if multiple else None
        if file_types is None:
            file_types = ("Media files (*.mp4;*.mkv;*.ts;*.mov;*.avi;*.mp3;*.m4a;*.aac;*.srt;*.ass;*.vtt)", "All files (*.*)")
        result = self.window.create_file_dialog(dialog_type, allow_multiple=multiple, file_types=file_types)
        if multiple:
            return result
        return result[0] if result else None

class ServerThread(threading.Thread):
    def __init__(self, port: int) -> None:
        super().__init__(daemon=True)
        config = uvicorn.Config(app=app, host="127.0.0.1", port=port, log_level="warning")
        self.server = uvicorn.Server(config)

    def run(self) -> None:
        self.server.run()

    def stop(self) -> None:
        self.server.should_exit = True


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_for_server(port: int, timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("The CineCraft server did not start in time.")


def main() -> None:
    bridge = DialogBridge()
    port = free_port()
    server = ServerThread(port)
    server.start()
    wait_for_server(port)
    
    window = webview.create_window(
        "CineCraft",
        url=f"http://127.0.0.1:{port}",
        js_api=bridge,
        width=1200,
        height=760,
        min_size=(1150, 850),
        maximized=False,
        frameless=False,
        easy_drag=False,
        background_color="#08090d",
    )
    bridge.set_window(window)
    window.events.closed += lambda: server.stop()

    try:
        webview.start(debug=False)
    finally:
        server.stop()


if __name__ == "__main__":
    main()
