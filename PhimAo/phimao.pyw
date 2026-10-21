"""Phím ảo nhỏ: luôn nổi trên cùng, không cướp focus, kéo giãn được, tự chọn phím.
Chuột phải lên bảng phím -> menu (chọn phím, số cột, độ mờ, bàn phím mới, thoát).
Mỗi bàn phím là 1 profile, có icon riêng trên taskbar.
  phimao.pyw          -> mở tất cả bàn phím
  phimao.pyw <tên>    -> mở riêng bàn phím <tên>
"""
import ctypes
import glob
import json
import os
import subprocess
import sys
import tkinter as tk
from tkinter import simpledialog
from ctypes import wintypes

from PIL import Image, ImageDraw, ImageFont, ImageTk

user32 = ctypes.WinDLL("user32", use_last_error=True)
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
PROFILE = sys.argv[1] if len(sys.argv) > 1 else "1"
COLORS = ["#1a73e8", "#d93025", "#188038", "#f9ab00", "#9334e6", "#e8710a", "#007b83", "#5f6368"]


def config_path(name):
    return os.path.join(HERE, "phimao.json" if name == "1" else f"phimao_{name}.json")


def all_profiles():
    names = ["1"]
    for p in sorted(glob.glob(os.path.join(HERE, "phimao_*.json"))):
        names.append(os.path.basename(p)[7:-5])
    return names


def launch(name):
    subprocess.Popen([sys.executable, os.path.abspath(__file__), name], cwd=HERE)


CONFIG = config_path(PROFILE)

# ---- Danh mục phím: tên hiển thị -> mã VK ----
VK = {
    "Esc": 0x1B, "Tab": 0x09, "Enter": 0x0D, "Space": 0x20, "Backspace": 0x08,
    "Delete": 0x2E, "Insert": 0x2D, "Home": 0x24, "End": 0x23,
    "PgUp": 0x21, "PgDn": 0x22, "←": 0x25, "↑": 0x26, "→": 0x27, "↓": 0x28,
    "PrtSc": 0x2C, "CapsLock": 0x14, "Menu": 0x5D,
    "Vol-": 0xAE, "Vol+": 0xAF, "Mute": 0xAD, "Play/Pause": 0xB3,
    "Next": 0xB0, "Prev": 0xB1,
}
for i in range(1, 13):
    VK[f"F{i}"] = 0x6F + i
for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
    VK[c] = ord(c)
for i in range(10):
    VK[f"Num{i}"] = 0x60 + i
VK.update({"Num+": 0x6B, "Num-": 0x6D, "Num*": 0x6A, "Num/": 0x6F, "Num.": 0x6E})
VK.update({"`": 0xC0, "-": 0xBD, "=": 0xBB, "[": 0xDB, "]": 0xDD, "\\": 0xDC,
           ";": 0xBA, "'": 0xDE, ",": 0xBC, ".": 0xBE, "/": 0xBF})

MODS = {"Ctrl": 0x11, "Shift": 0x10, "Alt": 0x12, "Win": 0x5B}
EXTENDED = {0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x2D, 0x2E, 0x5B, 0x5D, 0x6F}

# Layout bàn phím cho màn hình chọn phím: (tên, x, y, rộng, cao) theo đơn vị phím
def _layout():
    keys = []

    def row(y, x, items):
        for it in items:
            name, w = (it, 1) if isinstance(it, str) else it
            if name:
                keys.append((name, x, y, w, 1))
            x += w

    row(0, 0, ["Esc", ("", 1)] + [f"F{i}" for i in range(1, 5)] + [("", 0.5)]
        + [f"F{i}" for i in range(5, 9)] + [("", 0.5)] + [f"F{i}" for i in range(9, 13)])
    row(1.25, 0, list("`1234567890-=") + [("Backspace", 2)])
    row(2.25, 0, [("Tab", 1.5)] + list("QWERTYUIOP[]") + [("\\", 1.5)])
    row(3.25, 0, [("CapsLock", 1.75)] + list("ASDFGHJKL;'") + [("Enter", 2.25)])
    row(4.25, 0, [("Shift", 2.25)] + list("ZXCVBNM,./"))
    row(5.25, 0, [("Ctrl", 1.5), ("Win", 1.25), ("Alt", 1.25), ("Space", 6.25), ("Menu", 1.25)])
    nx = 15.5
    row(0, nx, ["PrtSc"])
    row(1.25, nx, ["Insert", "Home", "PgUp"])
    row(2.25, nx, ["Delete", "End", "PgDn"])
    row(4.25, nx + 1, ["↑"])
    row(5.25, nx, ["←", "↓", "→"])
    px = 19
    row(1.25, px, ["Num/", "Num*", "Num-"])
    row(2.25, px, ["Num7", "Num8", "Num9"])
    keys.append(("Num+", px + 3, 1.25, 1, 2))
    row(3.25, px, ["Num4", "Num5", "Num6"])
    row(4.25, px, ["Num1", "Num2", "Num3"])
    row(5.25, px, [("Num0", 2), "Num."])
    return keys


LAYOUT = _layout()
EXTRA = {
    "Tổ hợp": ["Ctrl+C", "Ctrl+V", "Ctrl+X", "Ctrl+Z", "Ctrl+Y", "Ctrl+A", "Ctrl+S",
               "Ctrl+F", "Ctrl+W", "Ctrl+T", "Alt+Tab", "Alt+F4", "Win+D", "Win+E",
               "Win+Shift+S", "Ctrl+Shift+Esc"],
    "Media": ["Vol-", "Vol+", "Mute", "Play/Pause", "Prev", "Next"],
}
ALL_ORDER = [k[0] for k in LAYOUT] + [k for v in EXTRA.values() for k in v]

DEFAULT = {
    "keys": ["Esc", "Tab", "Enter", "Backspace", "Ctrl+C", "Ctrl+V", "Ctrl+Z",
             "←", "↑", "↓", "→", "Ctrl", "Shift", "Alt"],
    "cols": 4,
    "geometry": "420x220+900+500",
    "alpha": 0.95,
}


def key_event(vk, up=False):
    flags = 0x0001 if vk in EXTENDED else 0
    if up:
        flags |= 0x0002
    user32.keybd_event(vk, user32.MapVirtualKeyW(vk, 0), flags, 0)


def parse_combo(name):
    """'Ctrl+Shift+S' -> ([0x11, 0x10], 0x53); None nếu không hợp lệ."""
    parts = [p.strip() for p in name.split("+")] if name != "Num+" else ["Num+"]
    mods, main = [], None
    for p in parts:
        cap = p[:1].upper() + p[1:].lower() if len(p) > 1 else p.upper()
        if cap in MODS:
            mods.append(MODS[cap])
        else:
            hit = next((k for k in VK if k.lower() == p.lower()), None)
            if hit is None:
                return None
            main = VK[hit]
    if main is None and len(mods) == 1 and len(parts) == 1:
        return mods, None
    return (mods, main) if main is not None else None


def load_cfg():
    try:
        with open(CONFIG, encoding="utf-8") as f:
            return {**DEFAULT, **json.load(f)}
    except Exception:
        return dict(DEFAULT)


class App:
    def __init__(self):
        self.cfg = load_cfg()
        self.sticky = {}  # vk -> button
        # AppID riêng -> mỗi bàn phím 1 icon taskbar, không bị gộp nhóm
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f"PhimAo.{PROFILE}")
        self.root = tk.Tk()
        self.root.title(f"Phím ảo {PROFILE}")
        self.root.geometry(self.cfg["geometry"])
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", self.cfg["alpha"])
        self.set_icon()
        self.root.configure(bg="#5f6368")
        self.root.minsize(30, 20)
        self.root.overrideredirect(not self.cfg.get("titlebar", False))
        self.frame = tk.Frame(self.root, bg="#202124", cursor="arrow")
        self.frame.pack(fill="both", expand=True, padx=2, pady=2)
        # viền xám: kéo cạnh/góc để đổi size, kéo giữa cạnh để di chuyển
        self.root.bind("<ButtonPress-1>", self.drag_start)
        self.root.bind("<B1-Motion>", self.drag_move)
        self.root.bind("<ButtonRelease-1>", self.drag_end)
        self.root.bind("<Motion>", self.hover)
        # chuột phải: click = menu, giữ + kéo = di chuyển bảng phím
        self.root.bind("<ButtonPress-3>", self.rmove_start)
        self.root.bind("<B3-Motion>", self.rmove)
        self.root.bind("<ButtonRelease-3>", self.rmove_end)
        # nút kéo size ở góc dưới phải
        self.grip = tk.Label(self.root, text="◢", fg="#e8eaed", bg="#5f6368",
                             font=("Segoe UI", 6), cursor="size_nw_se", bd=0)
        self.grip.place(relx=1, rely=1, anchor="se", width=10, height=10)
        self.grip.bind("<ButtonPress-1>", lambda e: self.drag_start(e, "se"))
        self.grip.bind("<B1-Motion>", self.drag_move)
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="Chọn phím...", command=self.open_picker)
        cols = tk.Menu(self.menu, tearoff=0)
        for n in range(1, 13):
            cols.add_command(label=str(n), command=lambda n=n: self.set_cfg("cols", n))
        self.menu.add_cascade(label="Số cột", menu=cols)
        alpha = tk.Menu(self.menu, tearoff=0)
        for a in (1.0, 0.9, 0.8, 0.7, 0.6, 0.5):
            alpha.add_command(label=f"{int(a * 100)}%", command=lambda a=a: self.set_alpha(a))
        self.menu.add_cascade(label="Độ mờ", menu=alpha)
        self.menu.add_command(label="Hiện/ẩn thanh tiêu đề", command=self.toggle_titlebar)
        color = tk.Menu(self.menu, tearoff=0)
        for c in COLORS:
            color.add_command(label="■■■■", foreground=c, command=lambda c=c: self.set_color(c))
        self.menu.add_cascade(label="Màu icon", menu=color)
        self.menu.add_separator()
        self.menu.add_command(label="Bàn phím mới...", command=self.new_profile)
        if PROFILE != "1":
            self.menu.add_command(label="Xóa bàn phím này", command=self.delete_profile)
        self.menu.add_separator()
        self.menu.add_command(label="Thoát", command=self.quit)
        self.root.bind("<Configure>", self.on_resize)
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self.build()
        self.root.after(100, self.no_activate)

    # Không cho cửa sổ nhận focus -> phím gửi vào app đang gõ; vẫn hiện trên taskbar
    def no_activate(self):
        hwnd = user32.GetParent(self.root.winfo_id())
        GWL_STYLE, GWL_EXSTYLE = -16, -20
        WS_EX_NOACTIVATE, WS_EX_TOPMOST, WS_EX_APPWINDOW, WS_EX_TOOLWINDOW = 0x08000000, 0x8, 0x40000, 0x80
        WS_MINIMIZEBOX, WS_SYSMENU = 0x20000, 0x80000
        user32.GetWindowLongW.restype = ctypes.c_long
        ex = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ex = (ex | WS_EX_NOACTIVATE | WS_EX_TOPMOST | WS_EX_APPWINDOW) & ~WS_EX_TOOLWINDOW
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex)
        st = user32.GetWindowLongW(hwnd, GWL_STYLE)
        user32.SetWindowLongW(hwnd, GWL_STYLE, st | WS_MINIMIZEBOX | WS_SYSMENU)
        user32.ShowWindow(hwnd, 0)  # ẩn/hiện lại để taskbar cập nhật
        user32.ShowWindow(hwnd, 4)  # SW_SHOWNOACTIVATE

    def set_icon(self):
        size = 64
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((2, 2, size - 3, size - 3), radius=12, fill=self.cfg.get("color", COLORS[0]))
        text = PROFILE[:2].upper()
        try:
            font = ImageFont.truetype("segoeuib.ttf", 40 if len(text) == 1 else 30)
        except OSError:
            font = ImageFont.load_default()
        d.text((size / 2, size / 2), text, fill="white", font=font, anchor="mm")
        self._icon = ImageTk.PhotoImage(img)
        self.root.iconphoto(True, self._icon)

    def set_color(self, c):
        self.cfg["color"] = c
        self.save()
        self.set_icon()

    def new_profile(self):
        name = simpledialog.askstring("Bàn phím mới", "Tên bàn phím (1-2 ký tự hiện trên icon):",
                                      parent=self.root)
        if not name:
            return
        name = "".join(ch for ch in name.strip() if ch not in '\\/:*?"<>|')
        if not name or name in all_profiles():
            return
        cfg = dict(self.cfg)
        x, y = self.root.winfo_x(), self.root.winfo_y()
        cfg["geometry"] = f"{self.root.winfo_width()}x{self.root.winfo_height()}+{x}+{max(0, y - self.root.winfo_height() - 10)}"
        cfg["color"] = COLORS[len(all_profiles()) % len(COLORS)]
        with open(config_path(name), "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        launch(name)

    def delete_profile(self):
        self.root.destroy()
        try:
            os.remove(CONFIG)
        except OSError:
            pass

    def rmove_start(self, e):
        self.rdrag = (e.x_root, e.y_root, self.root.winfo_x(), self.root.winfo_y(), False)

    def rmove(self, e):
        if not getattr(self, "rdrag", None):
            return
        x0, y0, x, y, moved = self.rdrag
        dx, dy = e.x_root - x0, e.y_root - y0
        if moved or abs(dx) + abs(dy) > 4:
            self.rdrag = (x0, y0, x, y, True)
            self.root.geometry(f"+{x + dx}+{y + dy}")

    def rmove_end(self, e):
        moved = getattr(self, "rdrag", None) and self.rdrag[4]
        self.rdrag = None
        if moved:
            self.save()
        else:
            self.popup(e)

    CURSORS = {"n": "sb_v_double_arrow", "s": "sb_v_double_arrow", "e": "sb_h_double_arrow",
               "w": "sb_h_double_arrow", "ne": "size_ne_sw", "sw": "size_ne_sw",
               "nw": "size_nw_se", "se": "size_nw_se", "": "fleur"}

    def edges_at(self, e):
        """Cạnh nào đang trỏ vào: 'n','se',... hoặc '' (giữa cạnh -> di chuyển)."""
        x = e.x_root - self.root.winfo_rootx()
        y = e.y_root - self.root.winfo_rooty()
        w, h = self.root.winfo_width(), self.root.winfo_height()
        m = 8  # vùng góc
        v = "n" if y < m else "s" if y > h - m else ""
        hz = "w" if x < m else "e" if x > w - m else ""
        return v + hz

    def hover(self, e):
        if e.widget is self.root and not getattr(self, "drag", None):
            self.root.configure(cursor=self.CURSORS[self.edges_at(e)])

    def drag_start(self, e, edges=None):
        if edges is None:
            if e.widget is not self.root:
                return
            edges = self.edges_at(e)
        self.drag = (edges, e.x_root, e.y_root, self.root.winfo_x(), self.root.winfo_y(),
                     self.root.winfo_width(), self.root.winfo_height())

    def drag_end(self, e):
        if getattr(self, "drag", None):
            self.drag = None
            self.save()

    def drag_move(self, e):
        if not getattr(self, "drag", None):
            return
        edges, x0, y0, x, y, w, h = self.drag
        dx, dy = e.x_root - x0, e.y_root - y0
        if not edges:
            self.root.geometry(f"+{x + dx}+{y + dy}")
            return
        if "e" in edges:
            w = max(30, w + dx)
        if "s" in edges:
            h = max(20, h + dy)
        if "w" in edges:
            nw = max(30, w - dx)
            x, w = x + w - nw, nw
        if "n" in edges:
            nh = max(20, h - dy)
            y, h = y + h - nh, nh
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def toggle_titlebar(self):
        self.cfg["titlebar"] = not self.cfg.get("titlebar", False)
        self.root.overrideredirect(not self.cfg["titlebar"])
        self.save()
        self.root.after(50, self.no_activate)

    def build(self):
        for w in self.frame.winfo_children():
            w.destroy()
        self.buttons, self.sticky = [], {}
        cols = max(1, self.cfg["cols"])
        keys = self.cfg["keys"]
        # ô đầu tiên: nút kéo di chuyển, to bằng 1 phím
        mover = tk.Label(self.frame, text="✥", bg="#5f6368", fg="white",
                         relief="raised", bd=1, cursor="fleur")
        mover.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        mover.bind("<ButtonPress-1>", lambda e: self.drag_start(e, ""))
        self.buttons.append(mover)
        for i, name in enumerate(keys, start=1):
            b = tk.Label(self.frame, text=name, bg="#3c4043", fg="white",
                         relief="raised", bd=1, cursor="arrow")
            b.grid(row=i // cols, column=i % cols, sticky="nsew", padx=1, pady=1)
            b.bind("<ButtonPress-1>", lambda e, n=name, b=b: self.press(n, b))
            b.bind("<ButtonRelease-1>", lambda e, b=b: self.release(b))
            self.buttons.append(b)
        rows = (len(keys) + 1 + cols - 1) // cols
        for c in range(12):
            self.frame.columnconfigure(c, weight=1 if c < cols else 0, uniform="k" if c < cols else "")
        for r in range(max(rows, 1) + 12):
            self.frame.rowconfigure(r, weight=1 if r < rows else 0, uniform="r" if r < rows else "")
        self.on_resize()

    def on_resize(self, _=None):
        if not getattr(self, "buttons", None):
            return
        cols = max(1, self.cfg["cols"])
        rows = (len(self.buttons) + cols - 1) // cols
        h = self.root.winfo_height() / max(rows, 1)
        w = self.root.winfo_width() / cols
        # mỗi nút tự tính cỡ chữ theo độ dài chữ của nó, phủ gần hết nút
        for b in self.buttons:
            n = max(len(b["text"]), 1)
            size = int(max(4, min(h * 0.75, (w - 6) / (n * 0.62))))
            b.configure(font=("Segoe UI", -size, "bold"))

    def press(self, name, btn):
        parsed = parse_combo(name)
        if not parsed:
            return
        mods, main = parsed
        if main is None:  # phím giữ: bật/tắt
            vk = mods[0]
            if vk in self.sticky:
                del self.sticky[vk]
                btn.configure(bg="#3c4043")
            else:
                self.sticky[vk] = btn
                btn.configure(bg="#1a73e8")
            return
        btn.configure(relief="sunken", bg="#5f6368")
        allmods = list(dict.fromkeys(list(self.sticky) + mods))
        for m in allmods:
            key_event(m)
        key_event(main)
        key_event(main, up=True)
        for m in reversed(allmods):
            key_event(m, up=True)
        for b in self.sticky.values():
            b.configure(bg="#3c4043")
        self.sticky.clear()

    def release(self, btn):
        if btn not in self.sticky.values():
            btn.configure(relief="raised", bg="#3c4043")

    def popup(self, e):
        self.menu.tk_popup(e.x_root, e.y_root)

    def set_cfg(self, k, v):
        self.cfg[k] = v
        self.save()
        self.build()

    def set_alpha(self, a):
        self.cfg["alpha"] = a
        self.root.attributes("-alpha", a)
        self.save()

    def save(self):
        self.cfg["geometry"] = self.root.geometry()
        with open(CONFIG, "w", encoding="utf-8") as f:
            json.dump(self.cfg, f, ensure_ascii=False, indent=2)

    def quit(self):
        self.save()
        self.root.destroy()

    def open_picker(self):
        U = 42  # px mỗi đơn vị phím
        OFF, ON = "#3c4043", "#1a73e8"
        top = tk.Toplevel(self.root)
        top.title("Chọn phím - bấm vào phím để chọn/bỏ")
        top.attributes("-topmost", True)
        top.configure(bg="#202124")
        top.resizable(False, False)

        chosen = list(self.cfg["keys"])
        picked = set(chosen)

        kb = tk.Frame(top, bg="#202124", width=int(23 * U) + 16, height=int(6.25 * U) + 16)
        kb.pack(padx=8, pady=8)

        def toggle(name, lbl):
            if name in picked:
                picked.discard(name)
                lbl.configure(bg=OFF)
            else:
                picked.add(name)
                lbl.configure(bg=ON)

        for name, x, y, w, h in LAYOUT:
            text = name[3:] if name.startswith("Num") and len(name) == 4 else name
            lbl = tk.Label(kb, text=text, fg="white", bg=ON if name in picked else OFF,
                           relief="raised", bd=1, font=("Segoe UI", 9, "bold"))
            lbl.place(x=8 + x * U, y=8 + y * U, width=w * U - 3, height=h * U - 3)
            lbl.bind("<Button-1>", lambda e, n=name, l=lbl: toggle(n, l))

        extra = tk.Frame(top, bg="#202124")
        extra.pack(fill="x", padx=8)
        for cat, items in EXTRA.items():
            tk.Label(extra, text=cat, fg="#bdc1c6", bg="#202124",
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(6, 2))
            row = tk.Frame(extra, bg="#202124")
            row.pack(anchor="w")
            for i, name in enumerate(items):
                lbl = tk.Label(row, text=name, fg="white", bg=ON if name in picked else OFF,
                               relief="raised", bd=1, font=("Segoe UI", 9, "bold"), padx=8, pady=4)
                lbl.grid(row=0, column=i, padx=1)
                lbl.bind("<Button-1>", lambda e, n=name, l=lbl: toggle(n, l))

        bottom = tk.Frame(top, bg="#202124")
        bottom.pack(fill="x", padx=8, pady=8)
        tk.Label(bottom, text="Tổ hợp tùy chỉnh (vd: Ctrl+Shift+N, Alt+F, Win+R), cách nhau dấu phẩy:",
                 fg="#bdc1c6", bg="#202124").pack(anchor="w")
        entry = tk.Entry(bottom)
        entry.insert(0, ", ".join(k for k in chosen if k not in ALL_ORDER))
        entry.pack(fill="x", pady=4)
        err = tk.Label(bottom, fg="#f28b82", bg="#202124")
        err.pack(anchor="w")

        def apply():
            extra_keys = [s.strip() for s in entry.get().split(",") if s.strip()]
            bad = [s for s in extra_keys if not parse_combo(s)]
            if bad:
                err.configure(text="Không hiểu: " + ", ".join(bad))
                return
            # giữ thứ tự cũ, phím mới thêm theo thứ tự trên bàn phím
            keys = [k for k in chosen if k in picked]
            keys += [k for k in ALL_ORDER if k in picked and k not in keys]
            keys += [k for k in extra_keys if k not in keys]
            top.destroy()
            self.set_cfg("keys", keys)

        def clear():
            picked.clear()
            for w in list(kb.winfo_children()) + [c for r in extra.winfo_children()
                                                  for c in r.winfo_children()]:
                if isinstance(w, tk.Label) and w["bg"] == ON:
                    w.configure(bg=OFF)

        tk.Button(bottom, text="Áp dụng", width=12, command=apply).pack(side="right")
        tk.Button(bottom, text="Hủy", width=12, command=top.destroy).pack(side="right", padx=6)
        tk.Button(bottom, text="Bỏ chọn hết", width=12, command=clear).pack(side="left")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    # mỗi bàn phím chỉ chạy 1 bản
    ctypes.windll.kernel32.CreateMutexW(None, False, f"PhimAo_{PROFILE}")
    if ctypes.windll.kernel32.GetLastError() == 183:
        sys.exit()
    if len(sys.argv) == 1:  # mở file trực tiếp -> mở luôn các bàn phím khác
        for p in all_profiles():
            if p != "1":
                launch(p)
    App().run()
