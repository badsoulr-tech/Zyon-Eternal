#!/usr/bin/env python3
# language: python, file: zyon_pc.py, target: Windows/Linux + USB real
"""ZYON PC — Interface UnlockTool. Detecção USB real + qdl/mtk/adb/fastboot."""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import subprocess, json, threading, time, os, sys, urllib.parse, urllib.request
from pathlib import Path

try:
    import usb.core
except ImportError:
    os.system(f"{sys.executable} -m pip install pyusb requests --quiet")
    import usb.core

BASE = Path(__file__).parent
BIN = BASE / "bin"
KNOWLEDGE = BASE / "intelligence" / "knowledge.json"
RAW = "https://raw.githubusercontent.com/badsoulr-tech/Zyon-Eternal/main/intelligence/knowledge.json"

HW = {
    (0x05c6,0x9008):("EDL_9008","Qualcomm Emergency Download"),
    (0x05c6,0x900e):("EDL_900E","Qualcomm Semi-brick"),
    (0x05c6,0x901d):("DIAG","Qualcomm Diagnostic"),
    (0x0e8d,0x2000):("MTK","MediaTek Preloader"),
    (0x04e8,0x685d):("DOWNLOAD","Samsung Download Mode"),
    (0x04e8,0x6860):("RECOVERY","Samsung Recovery"),
    (0x18d1,0x4ee1):("FASTBOOT","Android Fastboot"),
    (0x18d1,0x4ee7):("ADB","Android ADB Interface"),
}

class ZyonPC(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ZYON PC — UnlockTool")
        self.geometry("1100x750")
        self.configure(bg="#0a0a0a")
        self.knowledge = self._load_k()
        self.devices = []
        self._build()
        self.after(500, self._auto)

    def _load_k(self):
        if KNOWLEDGE.exists():
            try: return json.loads(KNOWLEDGE.read_text())
            except: pass
        return {"patterns":[]}

    def _build(self):
        h = tk.Frame(self, bg="#0a0a0a"); h.pack(fill="x", padx=10, pady=8)
        tk.Label(h, text="ZYON UNLOCKTOOL PC", bg="#0a0a0a", fg="#0f0",
                 font=("Consolas",20,"bold")).pack(side="left")
        self.status = tk.Label(h, text="status: aguardando", bg="#0a0a0a",
                                fg="#888", font=("Consolas",10))
        self.status.pack(side="right")

        df = tk.LabelFrame(self, text="Dispositivos USB", bg="#0a0a0a",
                            fg="#0f0", font=("Consolas",10))
        df.pack(fill="x", padx=10, pady=4)
        self.dl = tk.Listbox(df, bg="#111", fg="#0f0",
                              font=("Consolas",10), height=4)
        self.dl.pack(fill="x", padx=4, pady=4)

        bf = tk.Frame(self, bg="#0a0a0a"); bf.pack(fill="x", padx=10, pady=4)
        buttons = [
            ("Escanear",   self._scan),
            ("Forçar EDL", self._edl),
            ("Fastboot",   self._fb),
            ("ADB",        self._adb),
            ("Flash QDL",  self._qdl),
            ("MTK",        self._mtk),
            ("Sync",       self._sync),
            ("IA",         self._ia),
        ]
        for i,(t,c) in enumerate(buttons):
            tk.Button(bf, text=t, command=c, width=13, bg="#222", fg="#0f0",
                      font=("Consolas",9)).grid(row=0, column=i, padx=2)

        lf = tk.LabelFrame(self, text="Log", bg="#0a0a0a",
                            fg="#0f0", font=("Consolas",10))
        lf.pack(fill="both", expand=True, padx=10, pady=4)
        self.log = scrolledtext.ScrolledText(lf, bg="#111", fg="#0f0",
                                              font=("Consolas",9), height=25)
        self.log.pack(fill="both", expand=True, padx=4, pady=4)
        for t,c in [("ok","#55ff55"),("err","#ff5555"),
                    ("warn","#ffff55"),("info","#55aaff")]:
            self.log.tag_config(t, foreground=c)

    def _log(self, m, tag="info"):
        self.log.insert("end", f"[{time.strftime('%H:%M:%S')}] {m}\n", tag)
        self.log.see("end")

    def _scan(self):
        self._log("escaneando USB...", "info")
        self.dl.delete(0, "end"); self.devices = []
        try:
            for d in usb.core.find(find_all=True):
                k = (d.idVendor, d.idProduct)
                if k in HW:
                    m, desc = HW[k]
                    line = f"{m:10s} {desc} [{hex(k[0])}:{hex(k[1])}] bus={d.bus} addr={d.address}"
                    self.dl.insert("end", line)
                    self.devices.append({"mode":m,"desc":desc,"vid":k[0],"pid":k[1]})
                    self._log(f"✓ {line}", "ok")
            if not self.devices:
                self._log("nenhum dispositivo em modo conhecido", "warn")
            self.status.config(text=f"dispositivos: {len(self.devices)}")
        except Exception as e:
            self._log(f"erro USB: {e}", "err")

    def _auto(self):
        self._scan(); self.after(3000, self._auto)

    def _edl(self):
        self._log("forçando EDL...", "info")
        for cmd in [["adb","reboot","edl"], ["fastboot","oem","edl"]]:
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                self._log(f"  {' '.join(cmd)} → {r.returncode}",
                          "ok" if r.returncode==0 else "err")
            except Exception as e:
                self._log(f"  {cmd[0]}: {e}", "warn")

    def _fb(self):
        self._log("$ fastboot devices", "info")
        exe = str(BIN/"fastboot.exe" if os.name=="nt" else BIN/"fastboot")
        try:
            r = subprocess.run([exe,"devices"] if Path(exe).exists() else ["fastboot","devices"],
                                capture_output=True, text=True, timeout=15)
            self._log(r.stdout or r.stderr, "ok" if r.returncode==0 else "err")
        except Exception as e:
            self._log(str(e), "err")

    def _adb(self):
        self._log("$ adb devices", "info")
        exe = str(BIN/"adb.exe" if os.name=="nt" else BIN/"adb")
        try:
            r = subprocess.run([exe,"devices"] if Path(exe).exists() else ["adb","devices"],
                                capture_output=True, text=True, timeout=15)
            self._log(r.stdout or r.stderr, "ok" if r.returncode==0 else "err")
        except Exception as e:
            self._log(str(e), "err")

    def _qdl(self):
        loader = filedialog.askopenfilename(
            title="Loader Firehose (.mbn/.elf)",
            filetypes=[("Firehose","*.mbn *.elf *.bin"),("Todos","*.*")])
        if not loader: return
        raw = filedialog.askopenfilename(title="rawprogram0.xml",
                                          filetypes=[("XML","*.xml")])
        if not raw: return
        exe = BIN/("qdl.exe" if os.name=="nt" else "qdl")
        cmd = [str(exe) if exe.exists() else "qdl",
               "--loader", loader, raw]
        self._log(f"$ {' '.join(cmd)}", "info")
        threading.Thread(target=self._run, args=(cmd,), daemon=True).start()

    def _mtk(self):
        exe = BIN/("mtk.exe" if os.name=="nt" else "mtk")
        if not exe.exists():
            self._log("mtk não encontrado em bin/", "err"); return
        cmd = [str(exe), "printgpt"]
        self._log(f"$ {' '.join(cmd)}", "info")
        threading.Thread(target=self._run, args=(cmd,), daemon=True).start()

    def _run(self, cmd):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            for line in (r.stdout + r.stderr).splitlines():
                self._log("  " + line, "ok" if r.returncode==0 else "err")
        except Exception as e:
            self._log(f"  erro: {e}", "err")

    def _sync(self):
        self._log("sync knowledge.json...", "info")
        try:
            with urllib.request.urlopen(RAW, timeout=15) as r:
                remote = json.loads(r.read())
            if remote.get("version") != self.knowledge.get("version"):
                KNOWLEDGE.parent.mkdir(parents=True, exist_ok=True)
                KNOWLEDGE.write_text(json.dumps(remote, indent=2))
                self.knowledge = remote
                self._log(f"  ✓ v{remote.get('version')}", "ok")
            else:
                self._log("  já atualizado", "warn")
        except Exception as e:
            self._log(f"  erro: {e}", "err")

    def _ia(self):
        st = {"devices":[d["mode"] for d in self.devices],
              "os":os.name, "kv":self.knowledge.get("version")}
        prompt = (f"Android unbrick PC state: {json.dumps(st)}. "
                  f"Give ONE shell command (qdl, mtk, adb, fastboot, heimdall) or WAIT.")
        self._log("consultando IA...", "info")
        def ask():
            try:
                url = f"https://text.pollinations.ai/{urllib.parse.quote(prompt)}"
                with urllib.request.urlopen(url, timeout=20) as r:
                    ans = r.read().decode().strip().replace("`","").split("\n")[0]
                self._log(f"  IA: {ans}", "warn")
                self._log(f"  rodando: {ans}", "info")
                p = subprocess.run(ans, shell=True, capture_output=True, text=True, timeout=60)
                for l in (p.stdout + p.stderr).splitlines()[:30]:
                    self._log("  " + l, "ok" if p.returncode==0 else "err")
            except Exception as e:
                self._log(f"  erro IA: {e}", "err")
        threading.Thread(target=ask, daemon=True).start()

if __name__ == "__main__":
    ZyonPC().mainloop()
