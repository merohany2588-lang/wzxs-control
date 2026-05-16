#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量SRT字幕生成工具 v5.4 - 防OOM稳定版 + 内存释放 + 低内存模式 + OOM自动重试
原理：你手动怎么跑的，就让程序照样跑，只是自动循环
"""
import sys, os, subprocess, threading, time, json, gc
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox

try:
    import psutil
except ImportError:
    subprocess.check_call([sys.executable,"-m","pip","install","--quiet","psutil"])
    import psutil

try:
    import pynvml; pynvml.nvmlInit(); _GPU=True
except: _GPU=False

CONFIG = os.path.join(os.path.expanduser("~"), ".batchsrt5.json")
VIDEO_EXT = {".mp4",".mkv",".avi",".mov",".wmv",".flv",".webm",".m4v",".ts",".rmvb"}
SEARCH = [
    r"E:\软件\PotPlayer\Engine\Faster-Whisper-XXL\faster-whisper-xxl.exe",
    r"C:\Program Files\DAUM\PotPlayer\Engine\Faster-Whisper-XXL\faster-whisper-xxl.exe",
    r"C:\Program Files (x86)\DAUM\PotPlayer\Engine\Faster-Whisper-XXL\faster-whisper-xxl.exe",
    r"D:\PotPlayer\Engine\Faster-Whisper-XXL\faster-whisper-xxl.exe",
]
C={"bg":"#0d1117","bg2":"#161b22","bg3":"#21262d","bg4":"#2d333b",
   "accent":"#f78166","blue":"#58a6ff","green":"#3fb950",
   "yellow":"#d29922","red":"#f85149","text":"#e6edf3","text2":"#8b949e"}

# ── OOM 重试参数（可在此处调整）────────────────────────────────────────────────
OOM_KEYWORDS     = ("mkl_malloc", "failed to allocate", "out of memory", "cudaMalloc")
OOM_MAX_RETRIES  = 3      # OOM 最多重试次数
OOM_RETRY_WAIT   = 30     # 每次重试前等待秒数
VRAM_MIN_FREE_MB = 2048   # 启动任务前要求的最小空闲显存（MB）
VRAM_WAIT_TIMEOUT= 120    # 等待显存的最长秒数

def lcfg():
    try:
        with open(CONFIG,"r",encoding="utf-8") as f: return json.load(f)
    except: return {}

def scfg(d):
    try:
        with open(CONFIG,"w",encoding="utf-8") as f: json.dump(d,f,ensure_ascii=False,indent=2)
    except: pass

def find_exe():
    for p in SEARCH:
        if os.path.isfile(p): return p
    return ""

def get_gpu():
    if not _GPU: return None
    try:
        h=pynvml.nvmlDeviceGetHandleByIndex(0)
        u=pynvml.nvmlDeviceGetUtilizationRates(h)
        m=pynvml.nvmlDeviceGetMemoryInfo(h)
        return u.gpu, m.used//(1024*1024), m.total//(1024*1024)
    except: return None


class App:
    def __init__(self, root):
        self.root=root
        self.root.title("批量SRT字幕生成 v5.4 · 防OOM稳定版")
        self.root.geometry("980x840")
        self.root.configure(bg=C["bg"])
        try:
            from ctypes import windll; windll.shcore.SetProcessDpiAwareness(1)
        except: pass

        self.videos=[]
        self.proc=None
        self.running=False
        self.stop_ev=threading.Event()

        cfg=lcfg()
        exe0=cfg.get("exe","") or find_exe()
        self.v_exe   =tk.StringVar(value=exe0)
        self.v_vdir  =tk.StringVar(value=cfg.get("vdir",""))
        self.v_skip  =tk.BooleanVar(value=cfg.get("skip",True))
        self.v_lowmem=tk.BooleanVar(value=cfg.get("lowmem",False))
        default_cmd = cfg.get("cmd_tpl",
            '--model large-v3-turbo '
            '--output_format srt --device cuda --beam_size 5 '
            '--condition_on_previous_text False '
            '--vad_filter True '
            '--no_speech_threshold 0.45 '
            '--compression_ratio_threshold 2.6 '
            '--temperature 0 '
            '--compute_type int8')
        self.v_cmd=tk.StringVar(value=default_cmd)

        self._style()
        self._ui()
        threading.Thread(target=self._monitor,daemon=True).start()

        self._log("🚀 v5.4 防OOM稳定版启动","info")
        self._log("📌 使用说明：","info")
        self._log("  1. 选择引擎 EXE（faster-whisper-xxl.exe）","tip")
        self._log("  2. 先点「测试单个」确认参数正确","tip")
        self._log("  3. 参数正确后再「开始批量」","tip")
        self._log("⚡ 防中断：condition_on_previous_text=False + vad_filter","success")
        self._log("🧠 防OOM：compute_type=int8 + 启动前等显存 + mkl_malloc自动重试","success")
        self._log("🧹 v5.4：任务后主动释放内存 · OOM自动重试3次 · 低内存工作模式","success")
        if exe0 and os.path.isfile(exe0):
            self._log(f"✅ 自动找到引擎: {exe0}","success")
        else:
            self._log("⚠️ 未找到引擎，请手动选择","warn")

    def _style(self):
        s=ttk.Style(); s.theme_use("clam")
        base=s.layout("Horizontal.TProgressbar")
        for n,col in [("m",C["accent"]),("c",C["blue"]),("r",C["green"]),
                       ("g",C["accent"]),("v",C["yellow"])]:
            sn=f"{n}.Horizontal.TProgressbar"
            s.layout(sn,base)
            s.configure(sn,background=col,troughcolor=C["bg3"],borderwidth=0,relief="flat")

    def _ui(self):
        hdr=tk.Frame(self.root,bg=C["bg2"],height=50)
        hdr.pack(fill=tk.X); hdr.pack_propagate(False)
        tk.Label(hdr,text="批量SRT字幕生成  v5.4",font=("Segoe UI",13,"bold"),
                 bg=C["bg2"],fg=C["accent"]).pack(side=tk.LEFT,padx=16,pady=10)
        self._res={}
        rb=tk.Frame(hdr,bg=C["bg2"]); rb.pack(side=tk.RIGHT,padx=12)
        for k,l,col in [("c","CPU",C["blue"]),("r","RAM",C["green"]),
                          ("g","GPU",C["accent"]),("v","VRAM",C["yellow"])]:
            f=tk.Frame(rb,bg=C["bg2"]); f.pack(side=tk.LEFT,padx=6,pady=8)
            tk.Label(f,text=l,font=("Consolas",8),bg=C["bg2"],fg=C["text2"]).pack()
            bar=ttk.Progressbar(f,length=64,mode="determinate",style=f"{k}.Horizontal.TProgressbar")
            bar.pack()
            lbl=tk.Label(f,text="--",font=("Consolas",8),bg=C["bg2"],fg=col,width=7); lbl.pack()
            self._res[k]=(bar,lbl,col)

        body=tk.Frame(self.root,bg=C["bg"])
        body.pack(fill=tk.BOTH,expand=True,padx=12,pady=8)
        left=tk.Frame(body,bg=C["bg"]); right=tk.Frame(body,bg=C["bg"])
        left.pack(side=tk.LEFT,fill=tk.BOTH,expand=True,padx=(0,8))
        right.pack(side=tk.RIGHT,fill=tk.BOTH,expand=True,padx=(8,0))
        self._left(left); self._right(right)

    def _lf(self,p,t):
        return tk.LabelFrame(p,text=f"  {t}  ",font=("Segoe UI",9,"bold"),
            bg=C["bg2"],fg=C["text2"],bd=1,relief="groove",labelanchor="nw")

    def _left(self,p):
        # ── 引擎 ──
        f1=self._lf(p,"🔧  引擎路径"); f1.pack(fill=tk.X,pady=(0,8))
        row=tk.Frame(f1,bg=C["bg2"]); row.pack(fill=tk.X,padx=8,pady=6)
        tk.Entry(row,textvariable=self.v_exe,bg=C["bg3"],fg=C["text"],
                 insertbackground=C["text"],relief="flat",font=("Segoe UI",9),bd=4
                 ).pack(side=tk.LEFT,fill=tk.X,expand=True,padx=(0,6))
        tk.Button(row,text="选择EXE",command=self._pick_exe,
                  bg=C["bg4"],fg=C["text"],relief="flat",font=("Segoe UI",9),
                  cursor="hand2",padx=8).pack(side=tk.LEFT,padx=(0,4))
        tk.Button(row,text="自动查找",command=self._auto_find,
                  bg=C["bg4"],fg=C["blue"],relief="flat",font=("Segoe UI",9),
                  cursor="hand2",padx=8).pack(side=tk.LEFT,padx=(0,4))
        tk.Button(row,text="查看帮助",command=self._show_help,
                  bg=C["bg4"],fg=C["yellow"],relief="flat",font=("Segoe UI",9),
                  cursor="hand2",padx=8).pack(side=tk.LEFT)

        # ── 命令参数 ──
        f2=self._lf(p,"⚙  命令参数  （直接照着手动能跑的参数填，{INPUT}=当前文件）")
        f2.pack(fill=tk.X,pady=(0,8))
        tk.Label(f2,text="  exe路径 {INPUT} [下面的参数] --output_dir [视频所在目录]",
                 font=("Segoe UI",8),bg=C["bg2"],fg=C["text2"]).pack(anchor="w",padx=8)
        self.e_cmd=tk.Entry(f2,textvariable=self.v_cmd,bg=C["bg3"],fg=C["text"],
                  insertbackground=C["text"],relief="flat",font=("Consolas",9),bd=4)
        self.e_cmd.pack(fill=tk.X,padx=8,pady=(2,4))

        # 预设按钮
        pb=tk.Frame(f2,bg=C["bg2"]); pb.pack(fill=tk.X,padx=8,pady=(0,4))
        tk.Label(pb,text="快速预设:",font=("Segoe UI",8),
                 bg=C["bg2"],fg=C["text2"]).pack(side=tk.LEFT,padx=(0,6))
        _SAFE = ('--condition_on_previous_text False '
                 '--vad_filter True '
                 '--no_speech_threshold 0.45 '
                 '--compression_ratio_threshold 2.6 '
                 '--temperature 0 '
                 '--compute_type int8')
        presets=[
            ("🛡 防中断·自动语言",
             f"--model large-v3-turbo --output_format srt --device cuda --beam_size 5 {_SAFE}"),
            ("🇨🇳 中文专用",
             f"--model large-v3-turbo --language zh --output_format srt --device cuda --beam_size 5 {_SAFE}"),
            ("🇬🇧 英文专用",
             f"--model large-v3-turbo --language en --output_format srt --device cuda --beam_size 5 {_SAFE}"),
            ("⚡ 极速(beam=1)",
             f"--model large-v3-turbo --output_format srt --device cuda --beam_size 1 {_SAFE}"),
            ("🧠 最高质量(large-v3)",
             f"--model large-v3 --output_format srt --device cuda --beam_size 5 {_SAFE}"),
            ("💻 CPU模式",
             f"--model large-v3-turbo --output_format srt --device cpu --beam_size 3 {_SAFE}"),
        ]
        for name,val in presets:
            tk.Button(pb,text=name,command=lambda v=val:self.v_cmd.set(v),
                      bg=C["bg3"],fg=C["text"],relief="flat",
                      font=("Segoe UI",8),cursor="hand2",padx=6,pady=2
                      ).pack(side=tk.LEFT,padx=(0,4))

        # ── 低内存工作模式 ──
        opt_row=tk.Frame(f2,bg=C["bg2"]); opt_row.pack(fill=tk.X,padx=8,pady=(0,6))
        tk.Checkbutton(opt_row,
            text="🔋 低内存工作模式（启动前等显存≥2GB · OOM自动重试3次 · 冷却15s · 任务后强制释放）",
            variable=self.v_lowmem,
            bg=C["bg2"],fg=C["green"],selectcolor=C["bg3"],
            activebackground=C["bg2"],font=("Segoe UI",9),cursor="hand2"
        ).pack(side=tk.LEFT)

        # ── 视频目录 ──
        f3=self._lf(p,"📁  视频目录"); f3.pack(fill=tk.X,pady=(0,8))
        row2=tk.Frame(f3,bg=C["bg2"]); row2.pack(fill=tk.X,padx=8,pady=6)
        tk.Entry(row2,textvariable=self.v_vdir,bg=C["bg3"],fg=C["text"],
                 insertbackground=C["text"],relief="flat",font=("Segoe UI",9),bd=4
                 ).pack(side=tk.LEFT,fill=tk.X,expand=True,padx=(0,6))
        tk.Button(row2,text="选择目录",command=self._pick_dir,
                  bg=C["bg4"],fg=C["text"],relief="flat",font=("Segoe UI",9),
                  cursor="hand2",padx=8).pack(side=tk.LEFT,padx=(0,4))
        tk.Button(row2,text="扫描视频",command=self._scan,
                  bg=C["bg4"],fg=C["green"],relief="flat",font=("Segoe UI",9),
                  cursor="hand2",padx=8).pack(side=tk.LEFT)
        tk.Checkbutton(f3,text="跳过已有.srt字幕文件",variable=self.v_skip,
                       bg=C["bg2"],fg=C["text2"],selectcolor=C["bg3"],
                       activebackground=C["bg2"],font=("Segoe UI",9),
                       cursor="hand2").pack(anchor="w",padx=8,pady=(0,4))

        # ── 文件列表 ──
        f4=self._lf(p,"📋  文件列表"); f4.pack(fill=tk.BOTH,expand=True,pady=(0,8))
        tb=tk.Frame(f4,bg=C["bg2"]); tb.pack(fill=tk.X,padx=8,pady=(4,2))
        tk.Button(tb,text="➕ 添加文件",command=self._add_files,
                  bg=C["bg3"],fg=C["text"],relief="flat",font=("Segoe UI",9),
                  cursor="hand2",padx=8,pady=2).pack(side=tk.LEFT,padx=(0,4))
        tk.Button(tb,text="🗑 清空",command=self._clear,
                  bg=C["bg3"],fg=C["red"],relief="flat",font=("Segoe UI",9),
                  cursor="hand2",padx=8,pady=2).pack(side=tk.LEFT)
        self.lbl_n=tk.Label(tb,text="0 个文件",font=("Segoe UI",9),
                             bg=C["bg2"],fg=C["text2"]); self.lbl_n.pack(side=tk.RIGHT)
        fr=tk.Frame(f4,bg=C["bg3"]); fr.pack(fill=tk.BOTH,expand=True,padx=8,pady=(0,8))
        sb=tk.Scrollbar(fr,bg=C["bg4"],troughcolor=C["bg3"],width=10); sb.pack(side=tk.RIGHT,fill=tk.Y)
        self.lb=tk.Listbox(fr,bg=C["bg3"],fg=C["text"],selectbackground=C["bg4"],
                            font=("Consolas",9),relief="flat",height=8,
                            yscrollcommand=sb.set,activestyle="none")
        self.lb.pack(side=tk.LEFT,fill=tk.BOTH,expand=True)
        sb.config(command=self.lb.yview)

        # ── 进度 ──
        pf=tk.Frame(p,bg=C["bg"]); pf.pack(fill=tk.X,pady=(0,4))
        self.lbl_prog=tk.Label(pf,text="等待开始",font=("Segoe UI",9),
                                bg=C["bg"],fg=C["text2"]); self.lbl_prog.pack(side=tk.LEFT)
        self.lbl_pct=tk.Label(pf,text="",font=("Consolas",10,"bold"),
                               bg=C["bg"],fg=C["accent"]); self.lbl_pct.pack(side=tk.RIGHT)
        self.prog=ttk.Progressbar(p,mode="determinate",style="m.Horizontal.TProgressbar")
        self.prog.pack(fill=tk.X,pady=(0,6))
        self.lbl_cur=tk.Label(p,text="",font=("Segoe UI",9),
                               bg=C["bg"],fg=C["yellow"]); self.lbl_cur.pack(fill=tk.X)

        # ── 按钮 ──
        bf=tk.Frame(p,bg=C["bg"]); bf.pack(fill=tk.X,pady=(4,0))
        self.btn_test=tk.Button(bf,text="🧪 测试单个文件",command=self._test_one,
            bg=C["bg4"],fg=C["yellow"],relief="flat",
            font=("Segoe UI",11),cursor="hand2",pady=10,padx=10)
        self.btn_test.pack(side=tk.LEFT,padx=(0,6))
        self.btn_start=tk.Button(bf,text="▶  开始批量生成",command=self._start,
            bg=C["accent"],fg="white",relief="flat",
            font=("Segoe UI",12,"bold"),cursor="hand2",pady=10)
        self.btn_start.pack(side=tk.LEFT,fill=tk.X,expand=True,padx=(0,6))
        self.btn_stop=tk.Button(bf,text="⏹ 停止",command=self._stop,
            bg=C["bg3"],fg=C["red"],relief="flat",
            font=("Segoe UI",12),cursor="hand2",pady=10,
            state="disabled",width=8)
        self.btn_stop.pack(side=tk.LEFT)

    def _right(self,p):
        lf=self._lf(p,"📝  运行日志"); lf.pack(fill=tk.BOTH,expand=True)
        tb=tk.Frame(lf,bg=C["bg2"]); tb.pack(fill=tk.X,padx=8,pady=(4,2))
        tk.Button(tb,text="清空",command=self._clrlog,bg=C["bg3"],fg=C["text2"],
                  relief="flat",font=("Segoe UI",8),cursor="hand2",padx=6,pady=2
                  ).pack(side=tk.RIGHT)
        self.log_w=scrolledtext.ScrolledText(lf,bg=C["bg3"],fg=C["text"],
            font=("Consolas",9),relief="flat",wrap=tk.WORD,state="disabled")
        self.log_w.pack(fill=tk.BOTH,expand=True,padx=8,pady=(0,8))
        for t,fg in [("info",C["text"]),("tip",C["text2"]),("success",C["green"]),
                     ("warn",C["yellow"]),("error",C["red"]),("cur",C["blue"])]:
            self.log_w.tag_config(t,foreground=fg)

    # ── 事件 ─────────────────────────────────────────────────────────────────
    def _pick_exe(self):
        p=filedialog.askopenfilename(title="选择 faster-whisper-xxl.exe",
            filetypes=[("EXE","*.exe"),("所有文件","*.*")])
        if p: self.v_exe.set(p); self._log(f"✅ 引擎: {p}","success")

    def _auto_find(self):
        p=find_exe()
        if p: self.v_exe.set(p); self._log(f"✅ 自动找到: {p}","success")
        else: self._log("❌ 未找到，请手动选择","warn")

    def _show_help(self):
        exe=self.v_exe.get()
        if not exe or not os.path.isfile(exe):
            messagebox.showwarning("提示","请先选择引擎路径"); return
        self._log("─"*50,"tip")
        self._log("📋 exe --help 输出 (复制给AI看参数):","cur")
        def _run():
            try:
                r=subprocess.run([exe,"--help"],capture_output=True,text=True,
                    encoding="utf-8",errors="replace",timeout=15,
                    creationflags=(subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0))
                out=(r.stdout+r.stderr).strip()
                for line in out.splitlines():
                    self._log(f"  {line}","tip")
            except Exception as e:
                self._log(f"❌ {e}","error")
        threading.Thread(target=_run,daemon=True).start()

    def _pick_dir(self):
        d=filedialog.askdirectory(title="选择视频目录")
        if d: self.v_vdir.set(d); self._scan()

    def _scan(self):
        d=self.v_vdir.get()
        if not d or not os.path.isdir(d): messagebox.showwarning("提示","请先选择视频目录"); return
        self._clear()
        for f in sorted(Path(d).rglob("*")):
            if f.suffix.lower() in VIDEO_EXT: self._add(str(f))
        self._log(f"🔍 扫描到 {len(self.videos)} 个视频","info")

    def _add_files(self):
        fs=filedialog.askopenfilenames(title="选择视频",
            filetypes=[("视频"," ".join(f"*{e}" for e in VIDEO_EXT)),("所有","*.*")])
        for f in fs:
            if f not in self.videos: self._add(f)

    def _add(self,path):
        self.videos.append(path)
        srt=Path(path).with_suffix(".srt")
        mark=" ✓" if srt.exists() else ""
        idx=self.lb.size()
        self.lb.insert(tk.END,f"  {Path(path).name}{mark}")
        if mark: self.lb.itemconfig(idx,fg=C["text2"])
        self.lbl_n.config(text=f"{len(self.videos)} 个文件")

    def _clear(self):
        self.videos.clear(); self.lb.delete(0,tk.END)
        self.lbl_n.config(text="0 个文件")

    def _clrlog(self):
        self.log_w.config(state="normal"); self.log_w.delete("1.0",tk.END)
        self.log_w.config(state="disabled")

    def _log(self,msg,level="info"):
        def _do():
            ts=datetime.now().strftime("%H:%M:%S")
            self.log_w.config(state="normal")
            self.log_w.insert(tk.END,f"[{ts}] {msg}\n",level)
            self.log_w.see(tk.END)
            self.log_w.config(state="disabled")
        self.root.after(0,_do)

    # ── 资源监控 ──────────────────────────────────────────────────────────────
    def _monitor(self):
        while True:
            try:
                cpu=psutil.cpu_percent(interval=1); ram=psutil.virtual_memory().percent
                gd=get_gpu()
                def _u(c=cpu,r=ram,g=gd):
                    self._ur("c",c,f"{c:.0f}%"); self._ur("r",r,f"{r:.0f}%")
                    if g: gu,gm,gt=g; self._ur("g",gu,f"{gu}%"); self._ur("v",gm/gt*100 if gt else 0,f"{gm}M")
                    else: self._ur("g",0,"N/A"); self._ur("v",0,"N/A")
                self.root.after(0,_u)
            except: pass
            time.sleep(2)

    def _ur(self,k,pct,t):
        bar,lbl,base=self._res[k]; bar["value"]=min(pct,100)
        lbl.config(text=t,fg=C["red"] if pct>90 else(C["yellow"] if pct>75 else base))

    # ── 内存释放（gc + 管道清理 + Windows工作集归还）────────────────────────────
    def _release_memory(self):
        """
        显式释放 Python 堆内存，并尝试将工作集归还给 OS。
        不影响任何推理精度，仅释放已结束进程残留的缓冲区与 Python 对象。
        """
        collected = gc.collect()
        if sys.platform == "win32":
            try:
                import ctypes
                handle = ctypes.windll.kernel32.GetCurrentProcess()
                ctypes.windll.kernel32.SetProcessWorkingSetSize(handle, -1, -1)
            except Exception:
                pass
        mem = psutil.virtual_memory()
        ram_msg = (f"RAM {mem.percent:.0f}%"
                   f" ({mem.used//1048576}MB/{mem.total//1048576}MB)")
        vram_msg = ""
        if _GPU:
            gd = get_gpu()
            if gd:
                _, gm, gt = gd
                free = gt - gm
                vram_msg = f"  ·  VRAM已用{gm}MB 空闲{free}MB/{gt}MB"
        self._log(f"🧹 内存已释放 (GC:{collected}对象) · {ram_msg}{vram_msg}","tip")

    # ── 启动前等待显存就绪 ────────────────────────────────────────────────────
    def _wait_vram(self, min_free_mb=VRAM_MIN_FREE_MB, timeout=VRAM_WAIT_TIMEOUT):
        """
        轮询显卡空闲显存，直到 free_vram >= min_free_mb 或超时。
        目的：防止上一个进程虽已退出，但 CUDA 驱动层尚未回收显存，
              导致下一个进程在模型初始化时 mkl_malloc 失败。
        不涉及任何推理参数，不影响精度。
        """
        if not _GPU:
            return  # 无 NVML，无法检测，直接放行
        deadline = time.time() + timeout
        poll_interval = 5
        first = True
        while time.time() < deadline:
            if self.stop_ev.is_set():
                return
            gd = get_gpu()
            if gd:
                _, gm, gt = gd
                free = gt - gm
                if free >= min_free_mb:
                    if not first:
                        self._log(f"✅ 显存空闲 {free}MB ≥ {min_free_mb}MB，可以启动","tip")
                    return
                self._log(
                    f"⏳ 等待显存释放… 空闲 {free}MB < 需要 {min_free_mb}MB"
                    f"（已等 {int(deadline - time.time() - timeout + (time.time() - deadline + timeout)):.0f}s）",
                    "warn")
                first = False
            time.sleep(poll_interval)
        self._log(f"⚠️ 等待显存超时（{timeout}s），强制继续","warn")

    # ── 测试单个 ──────────────────────────────────────────────────────────────
    def _test_one(self):
        exe=self.v_exe.get()
        if not exe or not os.path.isfile(exe):
            messagebox.showerror("错误","请先选择引擎路径"); return
        vpath=filedialog.askopenfilename(title="选一个视频文件测试",
            filetypes=[("视频"," ".join(f"*{e}" for e in VIDEO_EXT)),("所有","*.*")])
        if not vpath: return
        self.btn_test.config(state="disabled"); self.btn_start.config(state="disabled")
        threading.Thread(target=self._run_one,args=(exe,vpath,True),daemon=True).start()

    # ── 批量 ──────────────────────────────────────────────────────────────────
    def _start(self):
        exe=self.v_exe.get()
        if not exe or not os.path.isfile(exe):
            messagebox.showerror("错误","请先选择引擎路径"); return
        if not self.videos:
            messagebox.showwarning("提示","请先扫描/添加视频文件"); return
        self.running=True; self.stop_ev.clear()
        self.btn_start.config(state="disabled")
        self.btn_test.config(state="disabled")
        self.btn_stop.config(state="normal")
        scfg({"exe":self.v_exe.get(),"vdir":self.v_vdir.get(),
              "cmd_tpl":self.v_cmd.get(),"skip":self.v_skip.get(),
              "lowmem":self.v_lowmem.get()})
        threading.Thread(target=self._batch_worker,daemon=True).start()

    def _stop(self):
        self.stop_ev.set()
        if self.proc:
            try: self.proc.terminate()
            except: pass
        self._log("⏹ 停止","warn")
        self.btn_stop.config(state="disabled")

    def _batch_worker(self):
        exe     = self.v_exe.get()
        skip    = self.v_skip.get()
        lowmem  = self.v_lowmem.get()
        # 低内存模式冷却15s，普通模式5s
        cooldown = 15 if lowmem else 5
        done=skipped=errors=0; total=len(self.videos)
        t0=time.time()

        if lowmem:
            self._log("🔋 低内存工作模式已启用：启动前等显存 · OOM重试3次 · 冷却15s","warn")

        for i,vpath in enumerate(self.videos):
            if self.stop_ev.is_set(): break

            srt=Path(vpath).with_suffix(".srt")
            if skip and srt.exists():
                self._log(f"⏭ 跳过 {Path(vpath).name}","tip")
                skipped+=1
                self.root.after(0,lambda ii=i:self.lb.itemconfig(ii,fg=C["text2"]))
                self._upd(i+1,total,f"跳过 {Path(vpath).name}")
                continue

            self.root.after(0,lambda ii=i:(
                self.lb.selection_clear(0,tk.END),
                self.lb.selection_set(ii), self.lb.see(ii),
                self.lb.itemconfig(ii,fg=C["yellow"])
            ))
            self._log(f"\n🔄 [{i+1}/{total}] {Path(vpath).name}","cur")

            # ── OOM 自动重试循环 ─────────────────────────────────────────────
            ok = False
            for attempt in range(OOM_MAX_RETRIES + 1):
                if self.stop_ev.is_set(): break
                if attempt > 0:
                    self._log(f"♻️  第 {attempt}/{OOM_MAX_RETRIES} 次重试（mkl_malloc OOM）","warn")

                # 启动前等显存（每次尝试都等，包括重试）
                self._wait_vram(min_free_mb=VRAM_MIN_FREE_MB, timeout=VRAM_WAIT_TIMEOUT)
                if self.stop_ev.is_set(): break

                ok, is_oom = self._run_one(exe, vpath, False, i, total)

                if ok:
                    break  # 成功，不再重试

                if is_oom and attempt < OOM_MAX_RETRIES:
                    # OOM：释放内存后再等一轮再重试
                    self._release_memory()
                    self._log(f"⏳ OOM冷却 {OOM_RETRY_WAIT}s 后重试…","warn")
                    time.sleep(OOM_RETRY_WAIT)
                else:
                    break  # 非OOM失败 或 已达最大重试次数

            if ok:
                done+=1
                self.root.after(0,lambda ii=i:self.lb.itemconfig(ii,fg=C["green"]))
            else:
                errors+=1
                self.root.after(0,lambda ii=i:self.lb.itemconfig(ii,fg=C["red"]))
            self._upd(i+1,total,f"{'✅' if ok else '❌'} {Path(vpath).name}")

            # 任务后主动释放内存
            self._release_memory()

            # 任务间冷却
            if i < total - 1 and not self.stop_ev.is_set():
                self._log(f"⏳ 冷却 {cooldown}s，等待显存/内存释放…","tip")
                time.sleep(cooldown)

        elapsed=time.time()-t0
        self._log("─"*50,"tip")
        self._log(f"🎉 完成！✅{done} 成功  ⏭{skipped} 跳过  ❌{errors} 失败  "
                  f"耗时 {elapsed/60:.1f} 分钟","success")
        if done>0:
            self._log(f"⚡ 平均 {elapsed/done:.0f} 秒/个（含模型加载）","tip")
        self._release_memory()
        self.root.after(0,self._done_ui)

    def _run_one(self, exe, vpath, is_test, list_idx=-1, total=1):
        """
        核心执行函数。
        返回 (ok: bool, is_oom: bool)：
          ok     = True 表示成功
          is_oom = True 表示失败原因是 mkl_malloc / CUDA OOM，可以重试
        is_test=True 时由测试路径调用，忽略 is_oom 返回值。
        """
        vf=Path(vpath)
        out_dir=str(vf.parent)
        extra_args=self.v_cmd.get().strip().split()
        cmd=[exe, str(vpath)] + extra_args
        if "--output_dir" not in cmd and "--output-dir" not in cmd:
            cmd += ["--output_dir", out_dir]

        self._log(f"  $ {os.path.basename(exe)} \"{vf.name}\" {' '.join(extra_args[:6])}…","tip")
        self.root.after(0,self.lbl_cur.config,{"text":f"▶ {vf.name}  →  {out_dir}"})

        t0=time.time()
        beat_stop=threading.Event()
        def _beat():
            spin=["⣾","⣽","⣻","⢿","⡿","⣟","⣯","⣷"]; si=0
            while not beat_stop.is_set():
                time.sleep(3)
                if beat_stop.is_set(): break
                el=time.time()-t0
                self.root.after(0,self.lbl_cur.config,
                    {"text":f"{spin[si%8]} 运行中… {el:.0f}s  {vf.name}"})
                si+=1
        threading.Thread(target=_beat,daemon=True).start()

        output_lines = []   # 用于 OOM 关键词检测
        try:
            self.proc=subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
                creationflags=(subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0),
            )
            for line in self.proc.stdout:
                line=line.rstrip()
                if line:
                    self._log(f"    {line}","tip")
                    output_lines.append(line)
            # 显式关闭管道，立即释放读缓冲区
            try: self.proc.stdout.close()
            except Exception: pass
            self.proc.wait()
            ret=self.proc.returncode
            self.proc=None
        except Exception as e:
            self._log(f"❌ 启动失败: {e}","error")
            beat_stop.set()
            self.proc=None
            gc.collect()
            return (False, False)
        finally:
            beat_stop.set()
            gc.collect()  # 子进程结束后立即清理残留对象

        elapsed=time.time()-t0
        srt_out=Path(out_dir)/(vf.stem+".srt")

        # 检测是否为 OOM 导致的失败（mkl_malloc / cudaMalloc 等）
        all_output = "\n".join(output_lines).lower()
        is_oom = ret != 0 and any(kw.lower() in all_output for kw in OOM_KEYWORDS)

        if ret==0 or srt_out.exists():
            self._log(f"✅ 完成  耗时 {elapsed:.0f}s  → {srt_out.name}","success")
            if is_test:
                messagebox.showinfo("测试成功",
                    f"✅ 参数正确！\n耗时 {elapsed:.0f}s\n生成: {srt_out}")
                self._release_memory()
                self.root.after(0,self._done_ui)
            return (True, False)
        else:
            if is_oom:
                self._log(f"❌ OOM失败（mkl_malloc）返回码={ret}  耗时 {elapsed:.0f}s","error")
            else:
                self._log(f"❌ 失败 返回码={ret}  耗时 {elapsed:.0f}s","error")
            if is_test:
                detail = "（检测到 mkl_malloc OOM，请稍后重试或减少其他程序显存占用）" if is_oom else ""
                messagebox.showerror("测试失败",
                    f"返回码={ret}{detail}\n\n请点「查看帮助」确认支持的参数，\n"
                    f"然后修改命令参数栏后重试。")
                self._release_memory()
                self.root.after(0,self._done_ui)
            return (False, is_oom)

    def _upd(self,cur,total,msg):
        def _do():
            pct=int(cur/total*100) if total else 0
            self.prog["value"]=pct
            self.lbl_prog.config(text=f"{msg}  [{cur}/{total}]")
            self.lbl_pct.config(text=f"{pct}%")
        self.root.after(0,_do)

    def _done_ui(self):
        self.running=False
        self.btn_start.config(state="normal")
        self.btn_test.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.lbl_cur.config(text="")
        self.lbl_prog.config(text="处理完成")


def main():
    root=tk.Tk()
    app=App(root)
    root.protocol("WM_DELETE_WINDOW",lambda:(
        scfg({"exe":app.v_exe.get(),"vdir":app.v_vdir.get(),
              "cmd_tpl":app.v_cmd.get(),"skip":app.v_skip.get(),
              "lowmem":app.v_lowmem.get()}),
        root.destroy()))
    root.mainloop()

if __name__=="__main__":
    main()
