"""Conservative Windows app detection. Product identity must match exactly; never guess from EXE names."""
from __future__ import annotations
import os
import re
from pathlib import Path
from functools import lru_cache

APP_INSTALLED = "APP INSTALLED"
WEB_ONLY = "WEB ONLY"
DETECTION_REQUIRED = "DETECTION REQUIRED"

# Store/PWA products can use different user-facing names. Keep aliases product-specific:
# in particular, generic publisher matches (e.g. Google -> Google Drive) are unsafe.
ALIASES = {
    "chatgpt": {"chatgpt", "chat gpt", "openai chatgpt"},
    "gemini": {"gemini", "google gemini"},
    "claude": {"claude", "claude by anthropic"},
    "deepseek": {"deepseek", "deepseek chat"},
    "perplexity": {"perplexity", "perplexity ai"},
    "copilot": {"copilot", "microsoft copilot"},
    "grok": {"grok", "grok by xai"},
    "poe": {"poe", "poe by quora"},
    "meta-ai": {"meta ai"},
    "arena": {"arena", "arena ai", "lmarena"},
    "huggingchat": {"huggingchat", "hugging chat"},
    "mistral": {"le chat", "mistral le chat", "mistral"},
}

def _valid_exe(path):
    if not path:
        return False
    path = os.path.expandvars(os.path.expanduser(str(path).strip().strip('"')))
    return os.path.isfile(path) and os.path.splitext(path)[1].lower() in (".exe", ".com", ".bat", ".cmd")

def _normalize_name(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value).casefold()).strip()

def product_names(platform):
    """Names allowed for a platform; exact matches only (no substring/publisher guesses)."""
    pid = str(platform.get("id", "")).casefold()
    names = set(ALIASES.get(pid, set()))
    label = _normalize_name(platform.get("name", ""))
    if label:
        names.add(label)
    return {_normalize_name(n) for n in names if _normalize_name(n)}

def _publisher_matches(platform, publisher):
    expected = str(platform.get("publisher", "")).strip().casefold()
    # Product name is the primary identity. If a registry publisher is present, reject
    # an explicit conflict for known platforms, but tolerate blank publisher metadata.
    if not expected or not publisher:
        return True
    publisher = str(publisher).casefold()
    known = {
        "chatgpt": ("openai",), "gemini": ("google",), "claude": ("anthropic",),
        "deepseek": ("deepseek",), "perplexity": ("perplexity",), "copilot": ("microsoft",),
        "grok": ("xai", "x.ai"), "poe": ("quora",), "meta-ai": ("meta",),
        "arena": ("lmarena", "arena"), "huggingchat": ("hugging face", "huggingface"),
        "mistral": ("mistral",),
    }
    accepted = known.get(str(platform.get("id", "")).casefold(), (expected,))
    return any(token in publisher for token in accepted)

def _registry_executable(platform):
    try:
        import winreg
    except ImportError:
        return None
    names = product_names(platform)
    roots = (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER)
    access = winreg.KEY_READ
    views = (getattr(winreg, "KEY_WOW64_64KEY", 0), getattr(winreg, "KEY_WOW64_32KEY", 0))
    for root in roots:
        for view in views:
            try:
                key = winreg.OpenKey(root, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", 0, access | view)
            except OSError:
                continue
            try:
                for idx in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        sub = winreg.OpenKey(key, winreg.EnumKey(key, idx))
                        try:
                            def read(name):
                                try: return winreg.QueryValueEx(sub, name)[0]
                                except OSError: return ""
                            display_name, publisher = read("DisplayName"), read("Publisher")
                            if _normalize_name(display_name) not in names or not _publisher_matches(platform, publisher):
                                continue
                            icon = str(read("DisplayIcon")).split(",", 1)[0].strip().strip('"')
                            # Do not select an arbitrary EXE from InstallLocation: it may
                            # be an updater/helper unrelated to the app's actual entry point.
                            if _valid_exe(icon):
                                return os.path.expandvars(icon), f"Exact installed-product match: {display_name}"
                        finally:
                            sub.Close()
                    except OSError:
                        continue
            finally:
                key.Close()
    return None

@lru_cache(maxsize=1)
def _start_menu_shortcuts():
    """Index Start Menu links once; cards must not rescan the tree on every redraw."""
    appdata = os.environ.get("APPDATA", "")
    programdata = os.environ.get("PROGRAMDATA", r"C:\\ProgramData")
    roots = [Path(x) / "Microsoft/Windows/Start Menu/Programs" for x in (appdata, programdata) if x]
    found = {}
    for root in roots:
        try:
            for shortcut in root.rglob("*.lnk"):
                found.setdefault(_normalize_name(shortcut.stem), str(shortcut))
        except OSError:
            continue
    return found

def _start_menu_shortcut(platform):
    """Find an exact product-named shortcut. Return its .lnk path for ShellExecute."""
    shortcuts = _start_menu_shortcuts()
    for name in product_names(platform):
        if name in shortcuts:
            return shortcuts[name], f"Exact Start Menu shortcut match: {name}"
    return None

def detect(platform):
    """Return (state, launch_target, details). Targets can be EXEs or verified .lnk files."""
    configured = platform.get("executable", "")
    if configured:
        if _valid_exe(configured):
            return APP_INSTALLED, os.path.expandvars(os.path.expanduser(configured.strip().strip('"'))), "Configured executable exists"
        return DETECTION_REQUIRED, None, "Configured path is missing or is not an executable"
    if os.name != "nt" or not platform.get("auto_detect", True):
        return WEB_ONLY, None, "No verified desktop installation detected"
    found = _registry_executable(platform)
    if found:
        return APP_INSTALLED, found[0], found[1]
    shortcut = _start_menu_shortcut(platform)
    if shortcut:
        return APP_INSTALLED, shortcut[0], shortcut[1]
    return WEB_ONLY, None, "No exact installed-product or Start Menu match; using official website"

def protocol_registered(protocol):
    if os.name != "nt" or not protocol:
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, protocol) as key:
            winreg.QueryValueEx(key, "URL Protocol")
            return True
    except OSError:
        return False
