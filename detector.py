"""Conservative Windows app detection. Never infers installation from a filename alone."""
from __future__ import annotations
import os, sys, glob, subprocess
from pathlib import Path

APP_INSTALLED="APP INSTALLED"; WEB_ONLY="WEB ONLY"; DETECTION_REQUIRED="DETECTION REQUIRED"

def _valid(path):
    if not path: return False
    path=os.path.expandvars(os.path.expanduser(str(path).strip().strip('"')))
    return os.path.isfile(path) and os.path.splitext(path)[1].lower() in ('.exe','.com','.bat','.cmd')

def detect(platform):
    """Return (state, executable, details); registry publisher matching is conservative."""
    configured=platform.get("executable", "")
    if configured:
        if _valid(configured): return APP_INSTALLED, os.path.expandvars(configured.strip('"')), "Configured executable exists"
        return DETECTION_REQUIRED, None, "Configured path is missing or is not an executable"
    if os.name != "nt" or not platform.get("auto_detect", True): return WEB_ONLY, None, "No verified desktop installation detected"
    try:
        import winreg
        roots=[(winreg.HKEY_LOCAL_MACHINE, winreg.KEY_READ), (winreg.HKEY_CURRENT_USER, winreg.KEY_READ)]
        for root, access in roots:
            for view in (getattr(winreg,"KEY_WOW64_64KEY",0), getattr(winreg,"KEY_WOW64_32KEY",0)):
                try: key=winreg.OpenKey(root, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", 0, access|view)
                except OSError: continue
                try:
                    for idx in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            sub=winreg.OpenKey(key, winreg.EnumKey(key,idx)); vals={}
                            for name in ("DisplayName","Publisher","InstallLocation","DisplayIcon","UninstallString"):
                                try: vals[name]=winreg.QueryValueEx(sub,name)[0]
                                except OSError: pass
                            sub.Close()
                            name=str(vals.get("DisplayName","" )).casefold(); publisher=str(vals.get("Publisher","" )).casefold()
                            expected=str(platform.get("publisher", "")).casefold()
                            if expected and expected in publisher and platform["name"].split()[0].casefold() in name:
                                candidate=vals.get("DisplayIcon","").split(",")[0].strip('"') or vals.get("InstallLocation","")
                                if os.path.isdir(candidate):
                                    for exe in glob.glob(os.path.join(candidate,"*.exe")): return APP_INSTALLED,exe,"Matched registered product and publisher"
                                if _valid(candidate): return APP_INSTALLED,candidate,"Matched registered product and publisher"
                        except OSError: continue
                finally: key.Close()
    except (ImportError, OSError): pass
    return WEB_ONLY, None, "No verified desktop installation detected"

def protocol_registered(protocol):
    if os.name != "nt" or not protocol: return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, protocol) as k:
            return winreg.QueryValueEx(k,"URL Protocol")[0] is not None
    except OSError: return False
