"""Local JSON configuration and platform library for AI HUB."""
from __future__ import annotations
import json, os, tempfile
from pathlib import Path
from copy import deepcopy

APP_NAME = "AIHub"
DEFAULT_PLATFORMS = [
    ("chatgpt", "ChatGPT", "https://chatgpt.com", "OpenAI", "🤖"),
    ("gemini", "Google Gemini", "https://gemini.google.com", "Google", "✦"),
    ("claude", "Claude", "https://claude.ai", "Anthropic", "◈"),
    ("deepseek", "DeepSeek", "https://chat.deepseek.com", "DeepSeek", "◉"),
    ("perplexity", "Perplexity", "https://www.perplexity.ai", "Perplexity AI, Inc.", "⌕"),
    ("copilot", "Microsoft Copilot", "https://copilot.microsoft.com", "Microsoft", "◎"),
    ("grok", "Grok", "https://grok.com", "xAI", "✳"),
    ("poe", "Poe", "https://poe.com", "Quora, Inc.", "P"),
    ("meta-ai", "Meta AI", "https://www.meta.ai", "Meta Platforms", "∞"),
    ("arena", "Arena.ai", "https://arena.ai", "LMArena", "A"),
    ("huggingchat", "HuggingChat", "https://huggingface.co/chat", "Hugging Face", "🤗"),
    ("mistral", "Mistral Le Chat", "https://chat.mistral.ai", "Mistral AI", "M"),
]

def user_data_dir() -> Path:
    base = os.environ.get("APPDATA") if os.name == "nt" else os.environ.get("XDG_CONFIG_HOME")
    return Path(base or (Path.home() / ("AppData/Roaming" if os.name == "nt" else ".config"))) / APP_NAME

def default_config():
    return {"version": 1, "theme": "dark", "launch_preference": "APP FIRST", "remember_last": True,
            "start_minimized": False, "platforms": [
        {"id": i, "name": n, "url": u, "publisher": p, "icon": icon, "category": "General",
         "favorite": False, "enabled": True, "auto_detect": True, "executable": "", "protocol": "", "preference": ""}
        for i,n,u,p,icon in DEFAULT_PLATFORMS], "recent": [], "history": []}

class ConfigManager:
    def __init__(self, path=None):
        self.path = Path(path) if path else user_data_dir() / "config.json"
        self.data = self.load()
    def load(self):
        try:
            with self.path.open(encoding="utf-8") as f: data = json.load(f)
            if not isinstance(data, dict) or not isinstance(data.get("platforms"), list): raise ValueError("Invalid config")
            merged = default_config(); merged.update(data)
            merged["platforms"] = [self._normalize(p) for p in data["platforms"] if isinstance(p, dict)]
            return merged
        except FileNotFoundError: return default_config()
        except (OSError, ValueError, json.JSONDecodeError): return default_config()
    @staticmethod
    def _normalize(p):
        d = {"id":"custom", "name":"New AI", "url":"", "publisher":"", "icon":"✦", "category":"General", "favorite":False, "enabled":True, "auto_detect":True, "executable":"", "protocol":"", "preference":""}
        d.update(p); return d
    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix="config-", suffix=".tmp", dir=str(self.path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f: json.dump(self.data, f, indent=2, ensure_ascii=False); f.flush(); os.fsync(f.fileno())
            os.replace(tmp, self.path)
        finally:
            if os.path.exists(tmp): os.unlink(tmp)
    def export_to(self, path):
        with open(path, "w", encoding="utf-8") as f: json.dump(self.data, f, indent=2, ensure_ascii=False)
    def import_from(self, path):
        with open(path, encoding="utf-8") as f: candidate=json.load(f)
        if not isinstance(candidate, dict) or not isinstance(candidate.get("platforms"), list): raise ValueError("Not a valid AI HUB configuration")
        candidate.setdefault("version", 1); candidate["platforms"]=[self._normalize(p) for p in candidate["platforms"] if isinstance(p,dict)]
        self.data=candidate; self.save()
    def restore_defaults(self): self.data=default_config(); self.save()
    def platform(self, platform_id): return next((p for p in self.data["platforms"] if p["id"]==platform_id), None)
    def add_platform(self, platform):
        platform=self._normalize(platform)
        ids={p["id"] for p in self.data["platforms"]}
        base=platform["id"] or "custom"; i=2
        while platform["id"] in ids: platform["id"]=f"{base}-{i}"; i+=1
        self.data["platforms"].append(platform); self.save(); return platform
    def remove_platform(self, platform_id): self.data["platforms"]=[p for p in self.data["platforms"] if p["id"]!=platform_id]; self.save()
    def record_launch(self, platform_id):
        self.data["recent"]=[platform_id]+[x for x in self.data.get("recent",[]) if x!=platform_id]; self.data["recent"]=self.data["recent"][:8]
        self.data.setdefault("history",[]).insert(0,{"id":platform_id,"time":__import__("datetime").datetime.now().astimezone().isoformat(timespec="seconds")}); self.data["history"]=self.data["history"][:200]; self.save()
