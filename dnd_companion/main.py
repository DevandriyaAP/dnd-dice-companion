import sys
import os
import ctypes
import traceback

def log_error(err_msg):
    try:
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "widget_error.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(err_msg + "\n")
    except Exception:
        pass

try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont, QIcon

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from window import FloatingDndWidget, get_asset_path

    def main():
        try:
            myappid = "dndbeyond.dicewidget.companion.v1"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

        app = QApplication(sys.argv)
        app.setApplicationName("D&D Dice Widget")
        app.setQuitOnLastWindowClosed(False)

        icon_path = get_asset_path("dnd_dice.ico")
        if os.path.exists(icon_path):
            app_icon = QIcon(icon_path)
            app.setWindowIcon(app_icon)

        font = QFont("Segoe UI", 10)
        app.setFont(font)

        widget = FloatingDndWidget()

        # Center-right on available screen
        screen = app.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            x = max(40, geom.right() - widget.width() - 40)
            y = max(40, geom.top() + int((geom.height() - widget.height()) / 2))
            widget.move(x, y)

        widget.show()
        widget.raise_()
        widget.activateWindow()

        sys.exit(app.exec())

    if __name__ == "__main__":
        main()

except Exception as ex:
    err = traceback.format_exc()
    log_error(err)
    sys.exit(1)
