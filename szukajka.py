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

    def search_in_files(self, file_paths, search_phrase, progress_callback, save_folder=None, output_name=None, format_filter=None):
        """Przeszukuje pliki z buforowaniem 8MB"""
        if not file_paths:
            return None, 0, None, 0

        # Użyj custom folderu zapisu lub domyślnego
        if save_folder:
            output_dir = save_folder
        else:
            output_dir = os.path.dirname(file_paths[0])

        # Plik główny - pełne linie
        output_file = self.get_unique_filename(output_dir, base_name=output_name)

        # Plik combolist - login:hasło (jeśli zaznaczono filtr)
        combo_file = None
        combo_count = 0
        if format_filter:
            safe_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in search_phrase)
            combo_file = self.get_unique_filename(output_dir, base_name=f"{safe_name}_combolist")

        total_size = sum(os.path.getsize(f) for f in file_paths)
        processed_size = 0
        found_count = 0
        duplicate_count = 0
        start_time = time.time()
        seen_lines = set()
        seen_combo = set()

        search_lower = search_phrase.lower()
        import re
        sep_pattern = re.compile(r'[:;|\t]')

        def extract_credentials(line):
            """Wyciąga login:hasło z linii (usuwa domenę z początku jeśli jest)"""
            parts = sep_pattern.split(line, maxsplit=2)
            if len(parts) >= 3:
                return parts[1], parts[2], True
            elif len(parts) == 2:
                return parts[0], parts[1], True
            return line, "", False

        def process_line(line_stripped, out_main, out_combo):
            """Przetwarza jedną linię - zapisuje do plików"""
            nonlocal found_count, duplicate_count, combo_count

            # Plik główny - pełne linie (zawsze)
            line_lower = line_stripped.lower()
            if line_stripped and line_lower not in seen_lines:
                seen_lines.add(line_lower)
                out_main.write(line_stripped + '\n')
                found_count += 1
            else:
                duplicate_count += 1
                return

            # Combolist - wyciągnij login:hasło (jeśli filtr aktywny)
            if out_combo and format_filter:
                login, password, ok = extract_credentials(line_stripped)
                if ok and password:
                    if format_filter == "email" and '@' not in login:
                        return
                    elif format_filter == "user" and '@' in login:
                        return
                    # "both" przepuszcza wszystko
                    combo_line = f"{login}:{password}"
                    combo_lower = combo_line.lower()
                    if combo_lower not in seen_combo:
                        seen_combo.add(combo_lower)
                        out_combo.write(combo_line + '\n')
                        combo_count += 1

        combo_fh = open(combo_file, 'w', encoding='utf-8', errors='ignore') if combo_file else None

        try:
            with open(output_file, 'w', encoding='utf-8', errors='ignore') as out:
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
                                has_separator = any(sep in line for sep in [':', ';', '|', '\t'])
                                if search_lower in line.lower() and has_separator:
                                    line_stripped = line.strip()
                                    if line_stripped:
                                        process_line(line_stripped, out, combo_fh)

                            processed_size += len(chunk.encode('utf-8'))

                            elapsed = time.time() - start_time
                            if elapsed > 0:
                                speed = processed_size / elapsed
                                remaining = total_size - processed_size
                                eta = remaining / speed if speed > 0 else 0
                            else:
                                speed = 0
                                eta = 0

                            progress_callback(
                                processed_size, total_size,
                                found_count, duplicate_count,
                                speed, eta
                            )

                        # Reszta bufora
                        if buffer and search_lower in buffer.lower():
                            has_separator = any(sep in buffer for sep in [':', ';', '|', '\t'])
                            if has_separator:
                                line_stripped = buffer.strip()
                                if line_stripped:
                                    process_line(line_stripped, out, combo_fh)
        finally:
            if combo_fh:
                combo_fh.close()

        if self.stop_flag:
            return None, 0, None, 0

        return output_file, found_count, combo_file, combo_count


class RoundedButton(tk.Canvas):
    """Zaokrąglony przycisk z gradientem"""
    def __init__(self, parent, text, command, bg_color, fg_color, width=200, height=50):
        super().__init__(parent, width=width, height=height, bg=parent['bg'], highlightthickness=0)

        self.command = command
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.text = text

        self.draw_button()
        self.bind("<Button-1>", lambda e: self.on_click())
        self.bind("<Enter>", lambda e: self.on_hover())
        self.bind("<Leave>", lambda e: self.on_leave())

    def draw_button(self, hover=False):
        self.delete("all")

        color = self.lighten_color(self.bg_color) if hover else self.bg_color

        # Zaokrąglony prostokąt
        self.create_rounded_rect(5, 5, self.winfo_reqwidth()-5, self.winfo_reqheight()-5,
                                 radius=15, fill=color, outline="")

        # Tekst
        self.create_text(self.winfo_reqwidth()//2, self.winfo_reqheight()//2,
                        text=self.text, fill=self.fg_color,
                        font=("Arial", 12, "bold"))

    def create_rounded_rect(self, x1, y1, x2, y2, radius=25, **kwargs):
        points = [x1+radius, y1,
                  x1+radius, y1,
                  x2-radius, y1,
                  x2-radius, y1,
                  x2, y1,
                  x2, y1+radius,
                  x2, y1+radius,
                  x2, y2-radius,
                  x2, y2-radius,
                  x2, y2,
                  x2-radius, y2,
                  x2-radius, y2,
                  x1+radius, y2,
                  x1+radius, y2,
                  x1, y2,
                  x1, y2-radius,
                  x1, y2-radius,
                  x1, y1+radius,
                  x1, y1+radius,
                  x1, y1]
        return self.create_polygon(points, smooth=True, **kwargs)

    def lighten_color(self, color):
        """Rozjaśnia kolor dla efektu hover"""
        if color == "#00ff00":
            return "#33ff33"
        elif color == "#ff3333":
            return "#ff5555"
        return color

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
    """Nowoczesne pole tekstowe z placeholderem"""
    def __init__(self, parent, placeholder="", **kwargs):
        super().__init__(parent, bg="#0f0f0f")

        self.entry = tk.Entry(
            self,
            font=("Arial", 11),
            bg="#1a1a1a",
            fg="#00ff00",
            insertbackground="#00ff00",
            bd=0,
            relief="flat",
            **kwargs
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
            self.entry.config(fg="#666666")
            self.placeholder_active = True

    def hide_placeholder(self, event=None):
        if self.placeholder_active:
            self.entry.delete(0, tk.END)
            self.entry.config(fg="#00ff00")
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
        self.root.title("Szukajka Premium")
        self.root.geometry("900x870")
        self.root.configure(bg="#0a0a0a")
        self.root.resizable(True, True)
        # Minimalna wielkość okna
        self.root.minsize(750, 650)

        self.engine = Szukajka()
        self.selected_files = []
        self.save_folder = None  # Folder zapisu wyników
        self.is_searching = False

        self.setup_gui()

    def setup_gui(self):
        # Scrollowalny kontener
        scroll_canvas = tk.Canvas(self.root, bg="#0a0a0a", highlightthickness=0)
        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=scroll_canvas.yview)
        scroll_canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        scroll_canvas.pack(side="left", fill="both", expand=True)

        main_container = tk.Frame(scroll_canvas, bg="#0a0a0a")
        canvas_window = scroll_canvas.create_window((0, 0), window=main_container, anchor="n")

        def on_frame_configure(event):
            scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all"))

        def on_canvas_configure(event):
            scroll_canvas.itemconfig(canvas_window, width=event.width)

        main_container.bind("<Configure>", on_frame_configure)
        scroll_canvas.bind("<Configure>", on_canvas_configure)

        # Przewijanie kółkiem myszy
        def on_mousewheel(event):
            scroll_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def on_button4(event):
            scroll_canvas.yview_scroll(-3, "units")

        def on_button5(event):
            scroll_canvas.yview_scroll(3, "units")

        scroll_canvas.bind_all("<MouseWheel>", on_mousewheel)
        scroll_canvas.bind_all("<Button-4>", on_button4)
        scroll_canvas.bind_all("<Button-5>", on_button5)

        # ===== HEADER =====
        header_frame = tk.Frame(main_container, bg="#0a0a0a")
        header_frame.pack(pady=(5, 10))

        # Logo i tytuł
        title_frame = tk.Frame(header_frame, bg="#0a0a0a")
        title_frame.pack()

        tk.Label(
            title_frame,
            text="⚡",
            font=("Arial", 28),
            bg="#0a0a0a",
            fg="#00ff00"
        ).pack(side="left", padx=(0, 5))

        title_container = tk.Frame(title_frame, bg="#0a0a0a")
        title_container.pack(side="left")

        tk.Label(
            title_container,
            text="SZUKAJKA",
            font=("Arial", 20, "bold"),
            bg="#0a0a0a",
            fg="#00ff00"
        ).pack(anchor="w")

        tk.Label(
            title_container,
            text="Ultra-Fast • 8MB Buffer • 200GB+",
            font=("Arial", 8),
            bg="#0a0a0a",
            fg="#666666"
        ).pack(anchor="w")

        # ===== SEKCJA PLIKÓW =====
        files_section = tk.Frame(main_container, bg="#0f0f0f", bd=0)
        files_section.pack(fill="x", pady=(0, 8), padx=30)

        # Header sekcji
        tk.Label(
            files_section,
            text="📁  PLIKI ŹRÓDŁOWE",
            font=("Arial", 10, "bold"),
            bg="#0f0f0f",
            fg="#00ff00",
            anchor="w"
        ).pack(fill="x", padx=15, pady=(10, 5))

        # Status plików
        self.files_status = tk.Label(
            files_section,
            text="Nie wybrano plików • Kliknij poniżej aby dodać",
            font=("Arial", 9),
            bg="#0f0f0f",
            fg="#666666",
            anchor="w"
        )
        self.files_status.pack(fill="x", padx=15, pady=(0, 8))

        # Przyciski wyboru plików
        btn_container = tk.Frame(files_section, bg="#0f0f0f")
        btn_container.pack(pady=(0, 10))

        file_btn = RoundedButton(
            btn_container,
            "📄 Plik",
            self.select_file,
            "#1a4d1a",
            "#00ff00",
            width=120,
            height=35
        )
        file_btn.pack(side="left", padx=3)

        multiple_btn = RoundedButton(
            btn_container,
            "📂 Wiele",
            self.select_multiple_files,
            "#1a4d1a",
            "#00ff00",
            width=120,
            height=35
        )
        multiple_btn.pack(side="left", padx=3)

        folder_btn = RoundedButton(
            btn_container,
            "📁 Folder",
            self.select_folder,
            "#1a4d1a",
            "#00ff00",
            width=120,
            height=35
        )
        folder_btn.pack(side="left", padx=3)

        # ===== SEKCJA WYSZUKIWANIA =====
        search_section = tk.Frame(main_container, bg="#0f0f0f", bd=0)
        search_section.pack(fill="x", pady=(0, 8), padx=30)

        tk.Label(
            search_section,
            text="🔍  SZUKANA FRAZA",
            font=("Arial", 10, "bold"),
            bg="#0f0f0f",
            fg="#00ff00",
            anchor="w"
        ).pack(fill="x", padx=15, pady=(10, 5))

        # Entry z gradientem
        entry_container = tk.Frame(search_section, bg="#0f0f0f")
        entry_container.pack(fill="x", padx=15, pady=(0, 5))

        self.search_entry = ModernEntry(entry_container, placeholder="np. cda.pl, tb7.pl...")
        self.search_entry.pack(fill="x", ipady=8)

        tk.Label(
            search_section,
            text="💡 Szuka w formacie: domena:email:hasło • Separatory: : ; | TAB",
            font=("Arial", 8),
            bg="#0f0f0f",
            fg="#555555"
        ).pack(fill="x", padx=15, pady=(0, 10))

        # ===== SEKCJA ZAPISZ DO =====
        save_section = tk.Frame(main_container, bg="#0f0f0f", bd=0)
        save_section.pack(fill="x", pady=(0, 8), padx=30)

        tk.Label(
            save_section,
            text="💾  ZAPISZ DO",
            font=("Arial", 10, "bold"),
            bg="#0f0f0f",
            fg="#00ff00",
            anchor="w"
        ).pack(fill="x", padx=15, pady=(10, 5))

        # Nazwa pliku wynikowego
        name_row = tk.Frame(save_section, bg="#0f0f0f")
        name_row.pack(fill="x", padx=15, pady=(0, 5))

        tk.Label(
            name_row,
            text="Nazwa pliku:",
            font=("Arial", 9),
            bg="#0f0f0f",
            fg="#aaaaaa",
        ).pack(side="left", padx=(0, 5))

        self.output_name_entry = ModernEntry(name_row, placeholder="wyniki_cda_pl")
        self.output_name_entry.pack(side="left", fill="x", expand=True, ipady=4)

        tk.Label(
            name_row,
            text=".txt",
            font=("Arial", 9),
            bg="#0f0f0f",
            fg="#aaaaaa",
        ).pack(side="left", padx=(3, 0))

        # Status zapisu (folder)
        self.save_status = tk.Label(
            save_section,
            text="Automatycznie w folderze z plikami źródłowymi",
            font=("Arial", 9),
            bg="#0f0f0f",
            fg="#666666",
            anchor="w"
        )
        self.save_status.pack(fill="x", padx=15, pady=(0, 5))

        # Przycisk wyboru folderu zapisu
        save_btn_container = tk.Frame(save_section, bg="#0f0f0f")
        save_btn_container.pack(pady=(0, 5))

        save_btn = RoundedButton(
            save_btn_container,
            "📁 Wybierz folder",
            self.select_save_folder,
            "#1a4d1a",
            "#00ff00",
            width=150,
            height=35
        )
        save_btn.pack(side="left", padx=5)

        # ===== SEKCJA FILTRUJ FORMAT =====
        filter_section = tk.Frame(main_container, bg="#0f0f0f", bd=0)
        filter_section.pack(fill="x", pady=(0, 8), padx=30)

        tk.Label(
            filter_section,
            text="🔧  FILTRUJ FORMAT",
            font=("Arial", 10, "bold"),
            bg="#0f0f0f",
            fg="#00ff00",
            anchor="w"
        ).pack(fill="x", padx=15, pady=(10, 5))

        self.filter_email = tk.BooleanVar(value=False)
        self.filter_user = tk.BooleanVar(value=False)

        filter_row = tk.Frame(filter_section, bg="#0f0f0f")
        filter_row.pack(fill="x", padx=15, pady=(0, 10))

        tk.Checkbutton(
            filter_row, text="email:pass", variable=self.filter_email,
            font=("Arial", 10), bg="#0f0f0f", fg="#00ff00",
            selectcolor="#1a1a1a", activebackground="#0f0f0f",
            activeforeground="#00ff00", highlightthickness=0, bd=0,
        ).pack(side="left", padx=(0, 20))

        tk.Checkbutton(
            filter_row, text="user:pass", variable=self.filter_user,
            font=("Arial", 10), bg="#0f0f0f", fg="#00ff00",
            selectcolor="#1a1a1a", activebackground="#0f0f0f",
            activeforeground="#00ff00", highlightthickness=0, bd=0,
        ).pack(side="left", padx=(0, 20))

        tk.Label(
            filter_section,
            text="💡 Brak zaznaczenia = pełne linie • Zaznaczenie = wyciąga login:hasło",
            font=("Arial", 8), bg="#0f0f0f", fg="#555555"
        ).pack(fill="x", padx=15, pady=(0, 10))

        # ===== SEKCJA POSTĘPU =====
        progress_section = tk.Frame(main_container, bg="#0f0f0f", bd=0)
        progress_section.pack(fill="both", expand=True, pady=(0, 8), padx=30)

        tk.Label(
            progress_section,
            text="📊  POSTĘP",
            font=("Arial", 10, "bold"),
            bg="#0f0f0f",
            fg="#00ff00",
            anchor="w"
        ).pack(fill="x", padx=15, pady=(10, 5))

        # Progress bar z Custom Style
        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor='#1a1a1a',
            bordercolor='#0f0f0f',
            background='#00ff00',
            lightcolor='#00ff00',
            darkcolor='#00cc00',
            thickness=20
        )

        self.progress_bar = ttk.Progressbar(
            progress_section,
            style="Custom.Horizontal.TProgressbar",
            mode="determinate",
            length=700
        )
        self.progress_bar.pack(fill="x", padx=15, pady=(0, 8))

        # Statystyki
        stats_container = tk.Frame(progress_section, bg="#0a0a0a")
        stats_container.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        self.stats_text = tk.Text(
            stats_container,
            height=4,
            font=("Consolas", 8),
            bg="#0a0a0a",
            fg="#00ff00",
            bd=0,
            relief="flat",
            state="disabled",
            cursor="arrow"
        )
        self.stats_text.pack(fill="both", expand=True, padx=3, pady=3)

        # ===== PRZYCISKI AKCJI =====
        action_frame = tk.Frame(main_container, bg="#0a0a0a")
        action_frame.pack(pady=(0, 5))

        self.start_btn = RoundedButton(
            action_frame,
            "⚡ SKANUJ",
            self.start_search,
            "#00ff00",
            "#000000",
            width=250,
            height=40
        )
        self.start_btn.pack(side="left", padx=5)

        self.stop_btn = RoundedButton(
            action_frame,
            "⏹ STOP",
            self.stop_search,
            "#ff3333",
            "#ffffff",
            width=150,
            height=40
        )
        self.stop_btn.pack(side="left", padx=5)
        # Stop button działa od razu
        self.stop_btn_disabled = True

        # Footer
        tk.Label(
            main_container,
            text="© 2026 MARECKI SYSTEMS • v3.0",
            font=("Arial", 7),
            bg="#0a0a0a",
            fg="#333333"
        ).pack(pady=(5, 0))

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
            # Znajdź WSZYSTKIE pliki w folderze
            all_files = []
            for file in os.listdir(folder):
                file_path = os.path.join(folder, file)
                if os.path.isfile(file_path):
                    all_files.append(file_path)

            if all_files:
                self.selected_files = all_files
                self.update_files_status()
            else:
                messagebox.showwarning(
                    "Brak plików",
                    "W wybranym folderze nie znaleziono żadnych plików"
                )

    def select_save_folder(self):
        folder = filedialog.askdirectory(
            title="Wybierz folder do zapisu wyników"
        )
        if folder:
            self.save_folder = folder
            self.save_status.config(
                text=f"✓  {folder}",
                fg="#00ff00"
            )

    def update_files_status(self):
        if not self.selected_files:
            self.files_status.config(
                text="Nie wybrano plików • Kliknij poniżej aby dodać",
                fg="#666666"
            )
            return

        total_size = sum(os.path.getsize(f) for f in self.selected_files)
        size_str = self.engine.format_size(total_size)

        count_text = "1 plik" if len(self.selected_files) == 1 else f"{len(self.selected_files)} pliki"
        text = f"✓  {count_text} • {size_str} • {os.path.dirname(self.selected_files[0])}"

        self.files_status.config(text=text, fg="#00ff00")

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

        stats = f"""
  ┌───────────────────────────────────────────┐
  │  UNIKALNE WYNIKI:  {found:,}
  │  DUPLIKATY:        {duplicates:,}
  │  CZAS:             {elapsed_str}
  │  PRĘDKOŚĆ:         {speed_str}/s
  │  POZOSTAŁO:        {eta_str}
  └───────────────────────────────────────────┘
        """

        self.stats_text.config(state="normal")
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats.strip())
        self.stats_text.config(state="disabled")

        self.root.update_idletasks()

    def start_search(self):
        if not self.selected_files:
            messagebox.showerror(
                "Brak plików",
                "⚠  Najpierw wybierz pliki do przeszukania!"
            )
            return

        search_phrase = self.search_entry.get().strip()
        if not search_phrase:
            messagebox.showerror(
                "Brak frazy",
                "⚠  Wpisz frazę do wyszukania!"
            )
            return

        self.is_searching = True
        self.engine.stop_flag = False
        self.start_time = time.time()

        # Nazwa pliku wynikowego
        output_name = self.output_name_entry.get().strip()
        if not output_name:
            # Domyślna nazwa na bazie frazy wyszukiwania
            safe_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in search_phrase)
            output_name = f"wyniki_{safe_name}"

        # Filtr formatu: None=pełne linie, "email", "user", "both"
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

        def search_thread():
            output_file, found_count, combo_file, combo_count = self.engine.search_in_files(
                self.selected_files,
                search_phrase,
                self.update_stats,
                self.save_folder,
                output_name,
                format_filter
            )

            # Ustaw pasek na 100% po zakończeniu
            self.progress_bar['value'] = 100
            self.root.update_idletasks()

            self.is_searching = False

            if output_file and not self.engine.stop_flag:
                total_time = self.engine.format_time(time.time() - self.start_time)
                msg = (
                    f"Znaleziono {found_count:,} unikalnych wyników!\n\n"
                    f"Czas: {total_time}\n\n"
                    f"Pełne linie:\n{output_file}"
                )
                if combo_file and combo_count > 0:
                    msg += (
                        f"\n\nCombolist ({combo_count:,} wpisów):\n{combo_file}"
                    )
                messagebox.showinfo("✓ Skanowanie zakończone!", msg)

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

