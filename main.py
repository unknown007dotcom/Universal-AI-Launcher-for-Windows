"""AI HUB — lightweight cross-platform authoring, Windows-first launcher."""
import os, sys, socket, threading, tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox, filedialog, simpledialog
from config_manager import ConfigManager
from detector import detect, APP_INSTALLED, WEB_ONLY, DETECTION_REQUIRED
from launcher import launch

BG="#0d111b"; PANEL="#151c2a"; CARD="#1a2333"; TEXT="#f3f6fc"; MUTED="#9aa7ba"; ACCENT="#8b7cff"; GREEN="#65d6a6"
LOGO_IDS={"chatgpt","gemini","claude","deepseek","perplexity","copilot","grok","poe","meta-ai","arena","huggingchat","mistral"}

def resource_path(relative):
    base=getattr(sys,"_MEIPASS",Path(__file__).resolve().parent)
    return Path(base)/relative

def acquire_instance():
    if os.name != "nt":
        s=socket.socket();
        try: s.bind(("127.0.0.1", 47831)); return s
        except OSError: return None
    try:
        import ctypes
        h=ctypes.windll.kernel32.CreateMutexW(None, True, "Local\\AIHub-UniversalLauncher")
        if ctypes.windll.kernel32.GetLastError()==183:
            hwnd=ctypes.windll.user32.FindWindowW(None, "AI HUB")
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                ctypes.windll.user32.SetForegroundWindow(hwnd)
            return None
        return h
    except Exception: return True

class App:
    def __init__(self, root):
        self.root=root; self.cfg=ConfigManager(); self.logo_images={}; self.search=tk.StringVar(); self.search.trace_add("write",lambda *_:self.render())
        self.theme=self.cfg.data.get("theme","dark"); self.root.title("AI HUB"); self.root.geometry("1040x740"); self.root.minsize(760,560)
        self.root.configure(bg=BG); self.style=ttk.Style(); self.style.theme_use("clam")
        self.root.protocol("WM_DELETE_WINDOW",self.root.destroy); self.build(); self.render()
        self.root.bind("<Control-f>",lambda e:(self.entry.focus_set(),"break")); self.root.bind("<Return>",lambda e:self.launch_selected())
    def build(self):
        top=tk.Frame(self.root,bg=BG); top.pack(fill="x",padx=34,pady=(24,18))
        brand=tk.Frame(top,bg=BG); brand.pack(side="left")
        tk.Label(brand,text="✦",font=("Segoe UI",25,"bold"),fg=ACCENT,bg=BG).pack(side="left",padx=(0,11))
        tk.Label(brand,text="AI HUB",font=("Segoe UI",21,"bold"),fg=TEXT,bg=BG).pack(side="left")
        tk.Label(top,text="YOUR AI WORKSPACE",font=("Segoe UI",9,"bold"),fg=MUTED,bg=BG).pack(side="left",padx=18,pady=11)
        tk.Button(top,text="⚙  Settings",command=self.settings,bg=PANEL,fg=TEXT,relief="flat",padx=15,pady=9,cursor="hand2").pack(side="right")
        tk.Label(self.root,text="One place for every idea.",font=("Segoe UI",26,"bold"),fg=TEXT,bg=BG).pack(anchor="w",padx=36)
        tk.Label(self.root,text="Choose an AI assistant to continue.",font=("Segoe UI",11),fg=MUTED,bg=BG).pack(anchor="w",padx=38,pady=(4,18))
        bar=tk.Frame(self.root,bg=PANEL); bar.pack(fill="x",padx=36,pady=(0,20))
        tk.Label(bar,text="⌕",font=("Segoe UI",19),fg=MUTED,bg=PANEL).pack(side="left",padx=(13,7))
        self.entry=tk.Entry(bar,textvariable=self.search,bd=0,bg=PANEL,fg=TEXT,insertbackground=TEXT,font=("Segoe UI",12)); self.entry.pack(side="left",fill="x",expand=True,ipady=13)
        tk.Button(bar,text="＋  Add AI",command=self.add_dialog,bg=ACCENT,fg="white",relief="flat",font=("Segoe UI",10,"bold"),padx=15,pady=9).pack(side="right",padx=8,pady=7)
        row=tk.Frame(self.root,bg=BG); row.pack(fill="x",padx=36,pady=(0,10))
        tk.Label(row,text="AI LIBRARY",font=("Segoe UI",10,"bold"),fg=MUTED,bg=BG).pack(side="left")
        self.filter=tk.StringVar(value="All");
        for label in ("All","Favorites"):
            tk.Radiobutton(row,text=label,value=label,variable=self.filter,command=self.render,bg=BG,fg=MUTED,selectcolor=PANEL,activebackground=BG,activeforeground=TEXT).pack(side="right",padx=5)
        self.canvas=tk.Canvas(self.root,bg=BG,highlightthickness=0); self.scroll=ttk.Scrollbar(self.root,orient="vertical",command=self.canvas.yview)
        self.body=tk.Frame(self.canvas,bg=BG); self.body.bind("<Configure>",lambda e:self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0,0),window=self.body,anchor="nw",tags="body"); self.canvas.configure(yscrollcommand=self.scroll.set)
        self.canvas.pack(side="left",fill="both",expand=True,padx=(36,0)); self.scroll.pack(side="right",fill="y",padx=(0,25))
        self.canvas.bind("<Configure>",lambda e:self.canvas.itemconfigure("body",width=e.width)); self.canvas.bind_all("<MouseWheel>",lambda e:self.canvas.yview_scroll(-1*(e.delta//120),"units"))
        self.footer=tk.Label(self.root,text="Ready  ·  Apps are detected conservatively; web is the safe fallback.",anchor="w",font=("Segoe UI",9),fg=MUTED,bg=BG); self.footer.pack(fill="x",padx=36,pady=13)
    def render(self):
        for w in self.body.winfo_children(): w.destroy()
        data=self.cfg.data["platforms"]; query=self.search.get().strip().casefold(); favorites=self.filter.get()=="Favorites"
        data=[p for p in data if p.get("enabled",True) and (not favorites or p.get("favorite")) and (query in p["name"].casefold() or query in p.get("category","").casefold())]
        if not data: tk.Label(self.body,text="No matching platforms. Add an AI platform to get started.",fg=MUTED,bg=BG,font=("Segoe UI",11)).pack(pady=35); return
        for idx,p in enumerate(data):
            state,_,_=detect(p); color=GREEN if state==APP_INSTALLED else ("#f3ba68" if state==DETECTION_REQUIRED else MUTED)
            card=tk.Frame(self.body,bg=CARD,highlightbackground="#263247",highlightthickness=1); card.grid(row=idx//3,column=idx%3,sticky="nsew",padx=(0,12),pady=(0,12)); self.body.grid_columnconfigure(idx%3,weight=1)
            head=tk.Frame(card,bg=CARD); head.pack(fill="x",padx=15,pady=(14,7))
            logo_file=resource_path(f"assets/icons/{p.get('id','')}.png")
            if p.get("id") in LOGO_IDS and logo_file.is_file():
                image=self.logo_images.get(p["id"])
                if image is None:
                    image=tk.PhotoImage(file=str(logo_file)); self.logo_images[p["id"]]=image
                tk.Label(head,image=image,bg=CARD,width=46,height=46).pack(side="left",padx=(0,5))
            else:
                tk.Label(head,text=p.get("icon","✦"),font=("Segoe UI",24,"bold"),fg=ACCENT,bg=CARD,width=2).pack(side="left")
            tk.Button(head,text="★" if p.get("favorite") else "☆",command=lambda x=p:self.favorite(x),fg="#f3ba68",bg=CARD,relief="flat",font=("Segoe UI",16)).pack(side="right")
            tk.Label(card,text=p["name"],font=("Segoe UI",13,"bold"),fg=TEXT,bg=CARD,anchor="w").pack(fill="x",padx=16)
            tk.Label(card,text=state,font=("Segoe UI",8,"bold"),fg=color,bg=CARD,anchor="w").pack(fill="x",padx=16,pady=(5,12))
            bottom=tk.Frame(card,bg=CARD); bottom.pack(fill="x",padx=13,pady=(0,13))
            tk.Button(bottom,text="Launch  ↗",command=lambda x=p:self.launch_one(x),bg=ACCENT,fg="white",relief="flat",font=("Segoe UI",9,"bold"),padx=10,pady=7).pack(side="left",fill="x",expand=True)
            tk.Button(bottom,text="⋯",command=lambda x=p:self.context(x),bg="#273247",fg=TEXT,relief="flat",font=("Segoe UI",13),width=3).pack(side="right",padx=(7,0))
    def favorite(self,p): p["favorite"]=not p.get("favorite"); self.cfg.save(); self.render()
    def launch_one(self,p):
        try:
            state,exe,detail=detect(p)
            def choose():
                ans=messagebox.askyesnocancel("Choose launch target",f"Launch {p['name']} website?\n\nYes: website   No: desktop app"); return "web" if ans is True else "app" if ans is False else "cancel"
            ok,kind,msg=launch(p,self.cfg.data.get("launch_preference","APP FIRST"),choose)
            if kind=="APP_FAILED" and messagebox.askyesno("App could not open",f"{msg}\n\nOpen the website instead?"): from launcher import open_website; open_website(p); ok=True; kind="WEB"
            if ok:
                self.cfg.record_launch(p["id"]); self.footer.config(text=f"Opened {p['name']} · {kind}"); self.root.after(200,self.entry.focus_set)
            else: self.footer.config(text=f"Unable to launch {p['name']}: {msg}")
        except Exception as e: messagebox.showerror("Launch failed",str(e))
    def launch_selected(self):
        matches=[p for p in self.cfg.data["platforms"] if self.search.get().casefold() in p["name"].casefold()]
        if matches: self.launch_one(matches[0])
    def context(self,p):
        m=tk.Menu(self.root,tearoff=0); m.add_command(label="Edit platform…",command=lambda:self.edit_dialog(p)); m.add_command(label="Move up",command=lambda:self.move(p,-1)); m.add_command(label="Move down",command=lambda:self.move(p,1)); m.add_separator(); m.add_command(label="Delete",command=lambda:self.delete(p)); m.tk_popup(self.root.winfo_pointerx(),self.root.winfo_pointery())
    def move(self,p,d):
        a=self.cfg.data["platforms"]; i=a.index(p); j=max(0,min(len(a)-1,i+d)); a.insert(j,a.pop(i)); self.cfg.save(); self.render()
    def delete(self,p):
        if messagebox.askyesno("Delete platform",f"Remove {p['name']} from your library?"): self.cfg.remove_platform(p["id"]); self.render()
    def add_dialog(self): self.edit_dialog({"id":"custom","name":"","url":"https://","icon":"✦","category":"General","executable":"","publisher":"","auto_detect":True,"favorite":False,"preference":""},True)
    def edit_dialog(self,p,new=False):
        win=tk.Toplevel(self.root); win.title("Add AI platform" if new else "Edit platform"); win.configure(bg=BG); win.resizable(False,False); win.transient(self.root); win.grab_set()
        fields={}
        for label,key in (("Name","name"),("Website URL","url"),("Icon (emoji or text)","icon"),("Category","category"),("Executable path (optional)","executable"),("Publisher (for conservative detection)","publisher")):
            tk.Label(win,text=label,fg=MUTED,bg=BG,font=("Segoe UI",9)).pack(anchor="w",padx=22,pady=(11,2)); ent=tk.Entry(win,width=48,bg=PANEL,fg=TEXT,insertbackground=TEXT,relief="flat"); ent.insert(0,p.get(key,"")); ent.pack(padx=22,ipady=7); fields[key]=ent
        def save():
            vals={k:e.get().strip() for k,e in fields.items()};
            if not vals["name"] or not vals["url"]: messagebox.showwarning("Required", "Name and URL are required",parent=win); return
            if not vals["url"].startswith(("https://","http://")): messagebox.showwarning("Invalid URL", "Use an http or https URL",parent=win); return
            p.update(vals)
            if new: self.cfg.add_platform(p)
            else: self.cfg.save()
            self.render(); win.destroy()
        tk.Button(win,text="Save platform",command=save,bg=ACCENT,fg="white",relief="flat",padx=18,pady=9).pack(pady=18)
    def settings(self):
        win=tk.Toplevel(self.root); win.title("AI HUB Settings"); win.configure(bg=BG); win.geometry("440x460"); win.transient(self.root)
        tk.Label(win,text="Settings",font=("Segoe UI",20,"bold"),fg=TEXT,bg=BG).pack(anchor="w",padx=24,pady=20)
        tk.Label(win,text="Default launch behavior",fg=MUTED,bg=BG).pack(anchor="w",padx=24)
        pref=tk.StringVar(value=self.cfg.data.get("launch_preference","APP FIRST")); cb=ttk.Combobox(win,textvariable=pref,values=["APP FIRST","WEB FIRST","ASK EVERY TIME"],state="readonly"); cb.pack(fill="x",padx=24,pady=8)
        tk.Label(win,text="Appearance",fg=MUTED,bg=BG).pack(anchor="w",padx=24,pady=(12,0)); theme=tk.StringVar(value=self.theme); ttk.Combobox(win,textvariable=theme,values=["dark","light"],state="readonly").pack(fill="x",padx=24,pady=8)
        def set_theme(): self.theme=theme.get(); self.cfg.data["theme"]=self.theme; self.cfg.data["launch_preference"]=pref.get(); self.cfg.save(); messagebox.showinfo("Appearance", "Theme preference saved. Restart AI HUB to apply it.",parent=win)
        tk.Button(win,text="Save preferences",command=set_theme,bg=ACCENT,fg="white",relief="flat",padx=12,pady=8).pack(anchor="w",padx=24,pady=12)
        for title,cmd in (("Export library…",self.export),("Import library…",self.import_config),("Restore default library",self.restore)):
            tk.Button(win,text=title,command=cmd,bg=PANEL,fg=TEXT,relief="flat",anchor="w",padx=12,pady=9).pack(fill="x",padx=24,pady=4)
        tk.Label(win,text="Synaptics: Control Panel → Advanced → Tap Zones → Top Right → Run…\nSelect AIHub.exe. Repeated launches focus the existing window.",wraplength=390,fg=MUTED,bg=BG,justify="left").pack(anchor="w",padx=24,pady=15)
    def export(self):
        path=filedialog.asksaveasfilename(defaultextension=".json",filetypes=[("JSON","*.json")]);
        if path: self.cfg.export_to(path)
    def import_config(self):
        path=filedialog.askopenfilename(filetypes=[("JSON","*.json")]);
        if path:
            try: self.cfg.import_from(path); self.render()
            except Exception as e: messagebox.showerror("Import failed",str(e))
    def restore(self):
        if messagebox.askyesno("Restore defaults","Replace your library with the default platforms?"): self.cfg.restore_defaults(); self.render()

def main():
    lock=acquire_instance()
    if lock is None: return
    root=tk.Tk(); app=App(root)
    def focus():
        try: root.deiconify(); root.lift(); root.attributes("-topmost",True); root.after(300,lambda:root.attributes("-topmost",False)); app.entry.focus_set()
        except tk.TclError: pass
    root.after(100,focus); root.mainloop()
if __name__=="__main__": main()
