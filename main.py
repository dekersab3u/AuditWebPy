import sys
import ctypes

def fix_dpi():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

from src.gui.window import AuditWindow
if __name__ == "__main__":
    fix_dpi()
    app = AuditWindow()
    app.mainloop()