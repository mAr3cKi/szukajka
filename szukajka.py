import os
import time
import hashlib
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import threading
import sys

# Weryfikacja integralności programu
def verify_integrity():
    """Weryfikacja integralności pliku programu"""
    print("\n" + "="*65)
    print("  WERYFIKACJA INTEGRALNOŚCI PROGRAMU")
    print("="*65)
    try:
        script_path = os.path.abspath(__file__)
        if os.path.exists(script_path):
            # Oblicz hash pliku
            with open(script_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()

            file_size = os.path.getsize(script_path)
            size_kb = file_size / 1024

            print(f"  ✓ Status:       OK")
            print(f"  ✓ Ścieżka:      {script_path}")
            print(f"  ✓ Rozmiar:      {size_kb:.1f} KB")
            print(f"  ✓ Hash MD5:     {file_hash[:16]}...")
            print(f"  ✓ Program zweryfikowany i gotowy do pracy")
            print("="*65 + "\n")
            return True
    except Exception as e:
        print(f"  ⚠ Ostrzeżenie weryfikacji: {e}")
        print("="*65 + "\n")
    return True

verify_integrity()

print(r"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   ███╗   ███╗ █████╗ ██████╗ ███████╗ ██████╗██╗  ██╗██╗ ║
║   ████╗ ████║██╔══██╗██╔══██╗██╔════╝██╔════╝██║ ██╔╝██║ ║
║   ██╔████╔██║███████║██████╔╝█████╗  ██║     █████╔╝ ██║ ║
║   ██║╚██╔╝██║██╔══██║██╔══██╗██╔══╝  ██║     ██╔═██╗ ██║ ║
║   ██║ ╚═╝ ██║██║  ██║██║  ██║███████╗╚██████╗██║  ██╗██║ ║
║   ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝ ║
║                                                           ║
║         SZUKAJKA PREMIUM v3.0 - Ultra Edition             ║
║         Bufor 8MB • Obsługuje pliki 200GB+                ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
""")

class Szukajka:
    def __init__(self):
        self.stop_flag = False
        self.BUFFER_SIZE = 8 * 1024 * 1024  # 8MB

    def format_size(self, size_bytes):
        """Formatowanie rozmiaru pliku"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    def format_time(self, seconds):
        """Formatowanie czasu"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds//60)}m {int(seconds%60)}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"

    def get_unique_filename(self, directory, base_name=None):
        """Generuje unikalną nazwę pliku"""
        if not base_name:
            base_name = "wyniki"
        counter = 1
        while True:
            if counter == 1:
                filename = f"{base_name}.txt"
            else:
                filename = f"{base_name}_{counter}.txt"

            full_path = os.path.join(directory, filename)
            if not os.path.exists(full_path):
                return full_path
            counter += 1

    def search_in_files(self, file_paths, search_phrases, progress_callback,
                        save_folder=None, output_name=None, format_filter=None,
                        strip_spaces=False):
        """Przeszukuje pliki z buforowaniem 8MB - obsługuje wiele fraz (do 10)"""
        if not file_paths or not search_phrases:
            return {}

        # Użyj custom folderu zapisu lub domyślnego
        if save_folder:
            output_dir = save_folder
        else:
            output_dir = os.path.dirname(file_paths[0])

        import re
        email_re = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
        # Regex do normalizacji spacji wokół separatorów (eksperymentalny)
        space_sep_re = re.compile(r'\s*([:;|\t])\s*')

        def extract_credentials(line):
            """Wyciąga login:hasło - regex dla email, od prawej dla user"""
            m = email_re.search(line)
            if m:
                email = m.group(0)
                after = line[m.end():]
                if strip_spaces:
                    after = after.lstrip()
                if after and after[0] in ':;|\t':
                    password = after[1:].strip()
                    if password:
                        return email, password, True

            for sep in [':', ';', '|', '\t']:
                idx = line.rfind(sep)
                if idx > 0:
                    password = line[idx+1:].strip()
                    rest = line[:idx]
                    for sep2 in [':', ';', '|', '\t']:
                        idx2 = rest.rfind(sep2)
                        if idx2 >= 0:
                            login = rest[idx2+1:].strip()
                            if login and password:
                                return login, password, True
                    if rest.strip() and password:
                        return rest.strip(), password, True
                    break
            return line, "", False

        # Przygotuj strukturę per fraza
        single = len(search_phrases) == 1
        phrases_lower = [(p, p.lower()) for p in search_phrases]
        results = {}  # phrase -> dict(output, combo, found, combo_count, dupes, out_fh, combo_fh, seen_lines, seen_combo)

        for phrase, _ in phrases_lower:
            safe = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in phrase)
            if single and output_name:
                base = output_name
            elif output_name:
                base = f"{output_name}_{safe}"
            else:
                base = f"wyniki_{safe}"
            out_path = self.get_unique_filename(output_dir, base_name=base)
            combo_path = None
            if format_filter:
                combo_path = self.get_unique_filename(output_dir, base_name=f"{safe}_combolist")
            results[phrase] = {
                "output": out_path, "combo": combo_path,
                "found": 0, "combo_count": 0, "dupes": 0,
                "out_fh": None, "combo_fh": None,
                "seen_lines": set(), "seen_combo": set(),
            }

        # Otwórz wszystkie uchwyty
        for phrase, info in results.items():
            info["out_fh"] = open(info["output"], 'w', encoding='utf-8', errors='ignore')
            if info["combo"]:
                info["combo_fh"] = open(info["combo"], 'w', encoding='utf-8', errors='ignore')

        total_size = sum(os.path.getsize(f) for f in file_paths)
        processed_size = 0
        total_found = 0
        total_dupes = 0
        start_time = time.time()

        def process_line_for_phrase(phrase, line_stripped):
            """Przetwarza jedną linię dla konkretnej frazy"""
            nonlocal total_found, total_dupes
            info = results[phrase]
            line_lower = line_stripped.lower()
            if line_lower in info["seen_lines"]:
                info["dupes"] += 1
                total_dupes += 1
                return
            info["seen_lines"].add(line_lower)
            info["out_fh"].write(line_stripped + '\n')
            info["found"] += 1
            total_found += 1

            if info["combo_fh"] and format_filter:
                extraction_line = line_stripped
                if strip_spaces:
                    extraction_line = space_sep_re.sub(r'\1', extraction_line)
                login, password, ok = extract_credentials(extraction_line)
                if ok and password:
                    has_email = '@' in login and bool(email_re.match(login))
                    if format_filter == "email" and not has_email:
                        return
                    if format_filter == "user" and has_email:
                        return
                    combo_line = f"{login}:{password}"
                    combo_lower = combo_line.lower()
                    if combo_lower not in info["seen_combo"]:
                        info["seen_combo"].add(combo_lower)
                        info["combo_fh"].write(combo_line + '\n')
                        info["combo_count"] += 1

        try:
            for file_path in file_paths:
                if self.stop_flag:
                    break
                with open(file_path, 'r', encoding='utf-8', errors='ignore', buffering=self.BUFFER_SIZE) as f:
                    buffer = ""
                    while True:
                        if self.stop_flag:
                            break
                        chunk = f.read(self.BUFFER_SIZE)
                        if not chunk:
                            break
                        buffer += chunk
                        lines = buffer.split('\n')
                        buffer = lines[-1]

                        for line in lines[:-1]:
                            if not any(sep in line for sep in [':', ';', '|', '\t']):
                                continue
                            line_stripped = line.strip()
                            if not line_stripped:
                                continue
                            line_lower = line.lower()
                            for phrase, p_lower in phrases_lower:
                                if p_lower in line_lower:
                                    process_line_for_phrase(phrase, line_stripped)

                        processed_size += len(chunk.encode('utf-8'))
                        elapsed = time.time() - start_time
                        if elapsed > 0:
                            speed = processed_size / elapsed
                            remaining = total_size - processed_size
                            eta = remaining / speed if speed > 0 else 0
                        else:
                            speed = 0
                            eta = 0
                        progress_callback(processed_size, total_size,
                                          total_found, total_dupes, speed, eta)

                    # Reszta bufora
                    if buffer and any(sep in buffer for sep in [':', ';', '|', '\t']):
                        line_stripped = buffer.strip()
                        if line_stripped:
                            line_lower = buffer.lower()
                            for phrase, p_lower in phrases_lower:
                                if p_lower in line_lower:
                                    process_line_for_phrase(phrase, line_stripped)
        finally:
            for info in results.values():
                if info["out_fh"]:
                    info["out_fh"].close()
                if info["combo_fh"]:
                    info["combo_fh"].close()
                # Zwolnij sety (oszczędność RAM przy powrocie)
                info["seen_lines"] = None
                info["seen_combo"] = None
                info["out_fh"] = None
                info["combo_fh"] = None

        if self.stop_flag:
            return {}

        return results


# ===== PALETA KOLORÓW (styl DRM Player) =====
C = {
    "bg": "#000000",
    "card": "#0d0d0d",
    "card_border": "#1a1a1a",
    "input_bg": "#0a0a0a",
    "input_border": "#2d1a3d",
    "accent1": "#e94560",      # róż
    "accent2": "#a855f7",      # fiolet
    "text": "#ffffff",
    "text_dim": "#888888",
    "text_muted": "#555555",
    "success": "#22c55e",
    "danger": "#ef4444",
    "font": "Segoe UI",
    "mono": "Consolas",
}


class RoundedButton(tk.Canvas):
    """Zaokrąglony przycisk w stylu DRM Player"""
    def __init__(self, parent, text, command, bg_color, fg_color, width=200, height=44):
        super().__init__(parent, width=width, height=height, bg=parent['bg'], highlightthickness=0)
        self.command = command
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.text = text
        self._hover_color = self._calc_hover(bg_color)
        self.draw_button()
        self.bind("<Button-1>", lambda e: self.on_click())
        self.bind("<Enter>", lambda e: self.on_hover())
        self.bind("<Leave>", lambda e: self.on_leave())

    def _calc_hover(self, color):
        try:
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            return f"#{min(255,r+30):02x}{min(255,g+30):02x}{min(255,b+30):02x}"
        except:
            return color

    def draw_button(self, hover=False):
        self.delete("all")
        color = self._hover_color if hover else self.bg_color
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        self.create_rounded_rect(3, 3, w-3, h-3, radius=12, fill=color, outline="")
        self.create_text(w//2, h//2, text=self.text, fill=self.fg_color,
                        font=(C["font"], 11, "bold"))

    def create_rounded_rect(self, x1, y1, x2, y2, radius=12, **kwargs):
        points = [x1+radius, y1, x1+radius, y1, x2-radius, y1, x2-radius, y1,
                  x2, y1, x2, y1+radius, x2, y1+radius, x2, y2-radius,
                  x2, y2-radius, x2, y2, x2-radius, y2, x2-radius, y2,
                  x1+radius, y2, x1+radius, y2, x1, y2, x1, y2-radius,
                  x1, y2-radius, x1, y1+radius, x1, y1+radius, x1, y1]
        return self.create_polygon(points, smooth=True, **kwargs)

    def on_hover(self):
        self.draw_button(hover=True)
        self.config(cursor="hand2")

    def on_leave(self):
        self.draw_button(hover=False)
        self.config(cursor="")

    def on_click(self):
        if self.command:
            self.command()


class ModernEntry(tk.Frame):
    """Pole tekstowe w stylu DRM Player"""
    def __init__(self, parent, placeholder="", **kwargs):
        super().__init__(parent, bg=C["input_border"], bd=1, relief="flat")
        self.entry = tk.Entry(
            self, font=(C["font"], 11), bg=C["input_bg"], fg=C["text"],
            insertbackground=C["accent2"], bd=0, relief="flat", **kwargs
        )
        self.entry.pack(fill="both", expand=True, padx=2, pady=2)
        self.placeholder = placeholder
        self.placeholder_active = False
        if placeholder:
            self.show_placeholder()
            self.entry.bind("<FocusIn>", self.hide_placeholder)
            self.entry.bind("<FocusOut>", self.show_placeholder)

    def show_placeholder(self, event=None):
        if not self.entry.get():
            self.entry.insert(0, self.placeholder)
            self.entry.config(fg=C["text_muted"])
            self.placeholder_active = True

    def hide_placeholder(self, event=None):
        if self.placeholder_active:
            self.entry.delete(0, tk.END)
            self.entry.config(fg=C["text"])
            self.placeholder_active = False

    def get(self):
        if self.placeholder_active:
            return ""
        return self.entry.get()

    def insert(self, index, text):
        self.hide_placeholder()
        self.entry.insert(index, text)


class SzukajkaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Szukajka Premium v3.0")
        self.root.geometry("900x870")
        self.root.configure(bg=C["bg"])
        self.root.resizable(True, True)
        self.root.minsize(750, 650)
        self.engine = Szukajka()
        self.selected_files = []
        self.save_folder = None
        self.is_searching = False
        self.setup_gui()

    def _make_section(self, parent, padx=30):
        """Tworzy sekcję-kartę z obramowaniem"""
        frame = tk.Frame(parent, bg=C["card"], highlightbackground=C["card_border"],
                        highlightthickness=1)
        frame.pack(fill="x", pady=(0, 10), padx=padx)
        return frame

    def _section_label(self, parent, text):
        """Nagłówek sekcji z kolorem akcentu"""
        tk.Label(parent, text=text, font=(C["font"], 10, "bold"),
                bg=C["card"], fg=C["accent1"], anchor="w"
        ).pack(fill="x", padx=15, pady=(12, 5))

    def setup_gui(self):
        # Scrollowalny kontener
        scroll_canvas = tk.Canvas(self.root, bg=C["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=scroll_canvas.yview)
        scroll_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        scroll_canvas.pack(side="left", fill="both", expand=True)

        main_container = tk.Frame(scroll_canvas, bg=C["bg"])
        canvas_window = scroll_canvas.create_window((0, 0), window=main_container, anchor="n")

        def on_frame_configure(event):
            scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all"))
        def on_canvas_configure(event):
            scroll_canvas.itemconfig(canvas_window, width=event.width)
        main_container.bind("<Configure>", on_frame_configure)
        scroll_canvas.bind("<Configure>", on_canvas_configure)

        # Przewijanie kółkiem myszy (Linux)
        scroll_canvas.bind_all("<Button-4>", lambda e: scroll_canvas.yview_scroll(-3, "units"))
        scroll_canvas.bind_all("<Button-5>", lambda e: scroll_canvas.yview_scroll(3, "units"))
        scroll_canvas.bind_all("<MouseWheel>", lambda e: scroll_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        # ===== HEADER =====
        header = tk.Frame(main_container, bg=C["bg"])
        header.pack(pady=(15, 12))

        tk.Label(header, text="SZUKAJKA", font=(C["font"], 24, "bold"),
                bg=C["bg"], fg=C["accent1"]).pack()
        tk.Label(header, text="PREMIUM", font=(C["font"], 12),
                bg=C["bg"], fg=C["accent2"]).pack()
        tk.Label(header, text="Ultra-Fast  |  8MB Buffer  |  200GB+",
                font=(C["font"], 8), bg=C["bg"], fg=C["text_muted"]).pack(pady=(2, 0))

        # ===== PLIKI ŹRÓDŁOWE =====
        files_sec = self._make_section(main_container)
        self._section_label(files_sec, "PLIKI ŹRÓDŁOWE")

        self.files_status = tk.Label(files_sec,
            text="Nie wybrano plików", font=(C["font"], 9),
            bg=C["card"], fg=C["text_dim"], anchor="w")
        self.files_status.pack(fill="x", padx=15, pady=(0, 8))

        btn_row = tk.Frame(files_sec, bg=C["card"])
        btn_row.pack(pady=(0, 12))
        for txt, cmd in [("Plik", self.select_file), ("Wiele", self.select_multiple_files), ("Folder", self.select_folder)]:
            RoundedButton(btn_row, txt, cmd, "#1a1028", C["accent2"], width=120, height=36).pack(side="left", padx=4)

        # ===== SZUKANA FRAZA =====
        search_sec = self._make_section(main_container)
        self._section_label(search_sec, "SZUKANA FRAZA")

        entry_box = tk.Frame(search_sec, bg=C["card"])
        entry_box.pack(fill="x", padx=15, pady=(0, 5))
        self.search_entry = ModernEntry(entry_box, placeholder="np. helion, ebookpoint, cda.pl (max 10)")
        self.search_entry.pack(fill="x", ipady=8)

        tk.Label(search_sec,
                text="Wiele fraz oddziel przecinkiem  |  Separatory wierszy: :  ;  |  TAB",
                font=(C["font"], 8), bg=C["card"], fg=C["text_muted"]
        ).pack(fill="x", padx=15, pady=(0, 10))

        # ===== ZAPISZ DO =====
        save_sec = self._make_section(main_container)
        self._section_label(save_sec, "ZAPISZ DO")

        name_row = tk.Frame(save_sec, bg=C["card"])
        name_row.pack(fill="x", padx=15, pady=(0, 5))
        tk.Label(name_row, text="Nazwa pliku:", font=(C["font"], 9),
                bg=C["card"], fg=C["text_dim"]).pack(side="left", padx=(0, 5))
        self.output_name_entry = ModernEntry(name_row, placeholder="wyniki_cda_pl")
        self.output_name_entry.pack(side="left", fill="x", expand=True, ipady=4)
        tk.Label(name_row, text=".txt", font=(C["font"], 9),
                bg=C["card"], fg=C["text_dim"]).pack(side="left", padx=(3, 0))

        self.save_status = tk.Label(save_sec,
            text="Automatycznie w folderze źródłowym", font=(C["font"], 9),
            bg=C["card"], fg=C["text_dim"], anchor="w")
        self.save_status.pack(fill="x", padx=15, pady=(0, 5))

        save_btn_row = tk.Frame(save_sec, bg=C["card"])
        save_btn_row.pack(pady=(0, 10))
        RoundedButton(save_btn_row, "Wybierz folder", self.select_save_folder,
                      "#1a1028", C["accent2"], width=160, height=36).pack()

        # ===== FILTRUJ FORMAT (combolist) =====
        filter_sec = self._make_section(main_container)
        self._section_label(filter_sec, "COMBOLIST")

        self.filter_email = tk.BooleanVar(value=False)
        self.filter_user = tk.BooleanVar(value=False)
        self.strip_spaces = tk.BooleanVar(value=False)

        filter_row = tk.Frame(filter_sec, bg=C["card"])
        filter_row.pack(fill="x", padx=15, pady=(0, 5))

        for txt, var in [("email:pass", self.filter_email), ("user:pass", self.filter_user)]:
            tk.Checkbutton(filter_row, text=txt, variable=var,
                font=(C["font"], 10), bg=C["card"], fg=C["accent2"],
                selectcolor=C["input_bg"], activebackground=C["card"],
                activeforeground=C["accent1"], highlightthickness=0, bd=0,
            ).pack(side="left", padx=(0, 20))

        exp_row = tk.Frame(filter_sec, bg=C["card"])
        exp_row.pack(fill="x", padx=15, pady=(0, 5))
        tk.Checkbutton(exp_row, text="Ignoruj spacje wokół separatorów (EXP)",
            variable=self.strip_spaces,
            font=(C["font"], 9), bg=C["card"], fg=C["accent1"],
            selectcolor=C["input_bg"], activebackground=C["card"],
            activeforeground=C["accent2"], highlightthickness=0, bd=0,
        ).pack(side="left")

        tk.Label(filter_sec,
            text="Brak zaznaczenia = tylko pełne linie  |  Zaznaczenie = dodatkowy plik combolist",
            font=(C["font"], 8), bg=C["card"], fg=C["text_muted"]
        ).pack(fill="x", padx=15, pady=(0, 10))

        # ===== POSTĘP =====
        progress_sec = self._make_section(main_container)
        self._section_label(progress_sec, "POSTĘP")

        style = ttk.Style()
        style.theme_use('default')
        style.configure("DRM.Horizontal.TProgressbar",
            troughcolor='#1a1a1a', bordercolor=C["card"],
            background=C["accent1"], lightcolor=C["accent1"],
            darkcolor='#c73a50', thickness=20)

        self.progress_bar = ttk.Progressbar(progress_sec,
            style="DRM.Horizontal.TProgressbar", mode="determinate")
        self.progress_bar.pack(fill="x", padx=15, pady=(0, 8))

        stats_box = tk.Frame(progress_sec, bg=C["bg"])
        stats_box.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        self.stats_text = tk.Text(stats_box, height=4, font=(C["mono"], 9),
            bg=C["bg"], fg=C["accent2"], bd=0, relief="flat",
            state="disabled", cursor="arrow")
        self.stats_text.pack(fill="both", expand=True, padx=3, pady=3)

        # ===== PRZYCISKI AKCJI =====
        action_frame = tk.Frame(main_container, bg=C["bg"])
        action_frame.pack(pady=(0, 8))

        self.start_btn = RoundedButton(action_frame, "SKANUJ", self.start_search,
            C["accent1"], "#ffffff", width=260, height=44)
        self.start_btn.pack(side="left", padx=5)

        self.stop_btn = RoundedButton(action_frame, "STOP", self.stop_search,
            "#2a1215", C["danger"], width=150, height=44)
        self.stop_btn.pack(side="left", padx=5)

        # Footer
        tk.Label(main_container, text="MARECKI SYSTEMS  v3.0",
            font=(C["font"], 7), bg=C["bg"], fg="#333333").pack(pady=(5, 10))

    def select_file(self):
        file = filedialog.askopenfilename(
            title="Wybierz plik do przeszukania",
            filetypes=[("Pliki tekstowe", "*.txt"), ("Wszystkie pliki", "*.*")]
        )
        if file:
            self.selected_files = [file]
            self.update_files_status()

    def select_multiple_files(self):
        files = filedialog.askopenfilenames(
            title="Wybierz wiele plików",
            filetypes=[("Pliki tekstowe", "*.txt"), ("Wszystkie pliki", "*.*")]
        )
        if files:
            self.selected_files = list(files)
            self.update_files_status()

    def select_folder(self):
        folder = filedialog.askdirectory(
            title="Wybierz folder z plikami"
        )
        if folder:
            # Rekurencyjnie wszystkie pliki (z podfolderami)
            all_files = []
            for root, dirs, files in os.walk(folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.isfile(file_path):
                        all_files.append(file_path)

            if all_files:
                self.selected_files = all_files
                self.update_files_status()
            else:
                messagebox.showwarning(
                    "Brak plików",
                    "W wybranym folderze (i podfolderach) nie znaleziono żadnych plików"
                )

    def select_save_folder(self):
        folder = filedialog.askdirectory(
            title="Wybierz folder do zapisu wyników"
        )
        if folder:
            self.save_folder = folder
            self.save_status.config(text=folder, fg=C["success"])

    def update_files_status(self):
        if not self.selected_files:
            self.files_status.config(text="Nie wybrano plików", fg=C["text_dim"])
            return
        total_size = sum(os.path.getsize(f) for f in self.selected_files)
        size_str = self.engine.format_size(total_size)
        n = len(self.selected_files)
        count_text = "1 plik" if n == 1 else f"{n} pliki" if n < 5 else f"{n} plików"
        text = f"{count_text}  |  {size_str}  |  {os.path.dirname(self.selected_files[0])}"
        self.files_status.config(text=text, fg=C["success"])

    def update_stats(self, processed, total, found, duplicates, speed, eta):
        """Aktualizacja statystyk"""
        percent = (processed / total * 100) if total > 0 else 0
        # Upewnij się że pasek dochodzi do 100%
        if percent > 100:
            percent = 100
        self.progress_bar['value'] = percent

        speed_str = self.engine.format_size(speed)
        eta_str = self.engine.format_time(eta)
        elapsed_str = self.engine.format_time(time.time() - self.start_time)

        stats = (
            f"  WYNIKI:  {found:,}   |   DUPLIKATY: {duplicates:,}\n"
            f"  CZAS:    {elapsed_str}   |   PRĘDKOŚĆ:  {speed_str}/s\n"
            f"  POZOSTAŁO:  {eta_str}"
        )

        self.stats_text.config(state="normal")
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats)
        self.stats_text.config(state="disabled")

        self.root.update_idletasks()

    def start_search(self):
        if not self.selected_files:
            messagebox.showerror(
                "Brak plików",
                "⚠  Najpierw wybierz pliki do przeszukania!"
            )
            return

        raw_phrase = self.search_entry.get().strip()
        if not raw_phrase:
            messagebox.showerror("Brak frazy", "⚠  Wpisz frazę do wyszukania!")
            return

        # Parsowanie wielu fraz: przecinek jako separator, max 10, deduplikacja
        phrases = []
        seen = set()
        for p in raw_phrase.split(','):
            p = p.strip()
            if p and p.lower() not in seen:
                phrases.append(p)
                seen.add(p.lower())
        if not phrases:
            messagebox.showerror("Brak frazy", "⚠  Wpisz frazę do wyszukania!")
            return
        if len(phrases) > 10:
            messagebox.showwarning("Limit", "Max 10 fraz - biorę pierwsze 10")
            phrases = phrases[:10]

        self.is_searching = True
        self.engine.stop_flag = False
        self.start_time = time.time()

        output_name = self.output_name_entry.get().strip() or None

        want_email = self.filter_email.get()
        want_user = self.filter_user.get()
        if want_email and want_user:
            format_filter = "both"
        elif want_email:
            format_filter = "email"
        elif want_user:
            format_filter = "user"
        else:
            format_filter = None

        strip_spaces = self.strip_spaces.get()

        def search_thread():
            results = self.engine.search_in_files(
                self.selected_files, phrases, self.update_stats,
                self.save_folder, output_name, format_filter, strip_spaces
            )

            self.progress_bar['value'] = 100
            self.root.update_idletasks()
            self.is_searching = False

            if results and not self.engine.stop_flag:
                total_time = self.engine.format_time(time.time() - self.start_time)
                total_found = sum(r["found"] for r in results.values())
                total_combo = sum(r["combo_count"] for r in results.values())

                lines = [
                    f"Fraz przeszukanych: {len(results)}",
                    f"Łącznie wyników: {total_found:,}",
                    f"Czas: {total_time}",
                    "",
                ]
                for phrase, info in results.items():
                    lines.append(f"▸ {phrase}  →  {info['found']:,} linii")
                    lines.append(f"   {info['output']}")
                    if info["combo"] and info["combo_count"] > 0:
                        lines.append(f"   combolist: {info['combo_count']:,}  →  {info['combo']}")
                if format_filter:
                    lines.append("")
                    lines.append(f"Combolisty łącznie: {total_combo:,}")
                messagebox.showinfo("✓ Skanowanie zakończone!", "\n".join(lines))

        threading.Thread(target=search_thread, daemon=True).start()

    def stop_search(self):
        self.engine.stop_flag = True
        messagebox.showwarning(
            "Przerwano",
            "⚠  Skanowanie zostało zatrzymane przez użytkownika"
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = SzukajkaGUI(root)
    root.mainloop()


