#!/usr/bin/env python3
import subprocess, time, json, os, requests
from bs4 import BeautifulSoup
from pathlib import Path
try: import usb.core
except: os.system("pip install pyusb requests[socks] beautifulsoup4 -q"); import usb.core

C={"g":"\033[32m","r":"\033[31m","y":"\033[33m","c":"\033[36m","n":"\033[0m"}
ST=Path.home()/"zyon_state.json"
RAW="https://raw.githubusercontent.com/badsoulr-tech/Zyon-Eternal/main/intelligence/knowledge.json"
PROXIES={'http':'socks5h://127.0.0.1:9050','https':'socks5h://127.0.0.1:9050'}

def out(m,t="i"):
    i={"i":"»","o":"✓","e":"✗","a":"◈","y":"?"}[t]; c={"i":C["c"],"o":C["g"],"e":C["r"],"a":C["y"],"y":C["y"]}[t]
    print(f"{c}{i}{C['n']} [{time.strftime('%H:%M:%S')}] {m}")

HW={(0x05c6,0x9008):"EDL 9008",(0x05c6,0x900e):"EDL 900E",
    (0x04e8,0x685d):"Download Mode",(0x04e8,0x6860):"Recovery",
    (0x18d1,0x4ee7):"ADB",(0x18d1,0x4ee1):"Fastboot",(0x0e8d,0x2000):"MTK Preloader"}

def eye():
    """Detecta USB via termux-usb (sem pyusb)."""
    try:
        r = subprocess.run(["termux-usb", "-l"], capture_output=True, text=True, timeout=10)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip().splitlines()
    except Exception as e:
        return [f"termux-usb falhou: {e}"]
    return []

def shell():
    for c in ["adb shell id","rish -c id"]:
        try:
            r=subprocess.run(c.split(),capture_output=True,text=True,timeout=3)
            if "uid=2000" in r.stdout or "uid=0" in r.stdout: return c.split()[0]
        except: pass
    return None

def run(c):
    out(f"Exec: {c}","a")
    try:
        r=subprocess.run(c,shell=True,capture_output=True,text=True,timeout=30)
        return r.returncode==0,(r.stderr or r.stdout).strip()
    except Exception as e: return False,str(e)

def deep(q):
    out(f"Tor -> Deep Web: {q}","a")
    try:
        url=f"http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/search/?q={q}"
        r=requests.get(url,proxies=PROXIES,timeout=20)
        soup=BeautifulSoup(r.text,'html.parser')
        return [a.get_text() for a in soup.find_all('a',href=True) if '/search/' not in a['href']][:3]
    except Exception as e: return [f"Deep falhou: {e}"]

def ai(st, deep_res):
    p=f"Android Unbrick. State: {st}. DeepWeb: {deep_res}. Give ONLY ONE shell command or WAIT."
    try:
        r=requests.get(f"https://text.pollinations.ai/{requests.utils.quote(p)}",timeout=15)
        a=r.text.strip().replace("`","").split("\n")[0]
        return a if a and len(a)<150 else None
    except: return None

if __name__=="__main__":
    print(f"\n{C['c']}ZYON ETERNAL ENGINE{C['n']}")
    st={"last":"boot","err":""}; cyc=0
    while True:
        cyc+=1; print(f"\n{C['c']}── CICLO {cyc} ──{C['n']}")
        d=eye()
        for x in d: out(x,"o")
        if not d: out("Nenhum dispositivo USB","i")
        s=shell(); out(f"Shell: {s or 'inativo'}","o" if s else "e")
        lk="?"
        if s:
            try:
                r=subprocess.run([s,"shell" if s=="adb" else "-c","getprop ro.boot.other.locked"],capture_output=True,text=True,timeout=3)
                lk=r.stdout.strip()
                if lk=="1": out("Bootloader TRAVADO","e")
            except: pass
        try:
            r=requests.get(RAW,timeout=10)
            if r.status_code==200: out(f"Knowledge: v{r.json().get('version','?')}","o")
        except: pass
        dr=[]
        if cyc%3==0: dr=deep("Samsung+F721B+unbrick+exploit")
        adv=ai({"usb":d,"shell":s,"bl":lk,"err":st["err"][:50]}, dr)
        if adv and adv.upper()!="WAIT":
            out(f"IA: {adv}","y")
            ok,res=run(adv)
            if ok: out("Sucesso","o"); st["err"]=""
            else: st["err"]=res; out(f"Falhou: {res[:50]}","e")
        else: out("IA: WAIT","i")
        ST.write_text(json.dumps(st,indent=2))
        time.sleep(45)
