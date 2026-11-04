"""Launch desktop app or official website, never both."""
import os, subprocess, webbrowser
from detector import detect, APP_INSTALLED, DETECTION_REQUIRED

def launch(platform, preference="APP FIRST", choose=None):
    preference=(platform.get("preference") or preference).upper()
    state, exe, detail=detect(platform)
    if preference == "WEB FIRST": return open_website(platform), "WEB", detail
    if preference == "ASK EVERY TIME" and state == APP_INSTALLED:
        choice=choose() if choose else "web"
        if choice == "cancel": return False, "CANCEL", detail
        if choice == "web": return open_website(platform), "WEB", detail
    if state == APP_INSTALLED and exe:
        try:
            if os.name == "nt": os.startfile(exe)
            else: subprocess.Popen([exe], close_fds=True)
            return True, "APP", detail
        except (OSError, subprocess.SubprocessError) as e:
            return False, "APP_FAILED", str(e)
    return open_website(platform), "WEB", detail

def open_website(platform):
    url=platform.get("url", "").strip()
    if not url.lower().startswith(("https://", "http://")): raise ValueError("Enter a valid http or https website URL")
    return bool(webbrowser.open(url, new=2))
