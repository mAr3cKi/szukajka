import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os

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
║              SEARCH ENGINE SYSTEM  v1.0                   ║
║              ════════════════════════════                 ║
║                     [  ACTIVE  ]                          ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

        >> INITIALIZING SEARCH INTERFACE
""")

def search_files():
    input_dir = folder_path_entry.get()
    search_phrase = entry_phrase.get()
    if not input_dir or not os.path.exists(input_dir):
        messagebox.showerror("BŁĄD", "Wybierz folder źródłowy!")
        return
    output_file = filedialog.asksaveasfilename(defaultextension=".txt", title="Gdzie zapisać wyniki?")
    if not output_file: return
    try:
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        progress["maximum"] = len(files)
        found_lines = []
        seen_lines = set()

        for i, filename in enumerate(files):
            try:
                with open(os.path.join(input_dir, filename), "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if search_phrase in line:
                            line_stripped = line.strip()
                            if line_stripped not in seen_lines:
                                seen_lines.add(line_stripped)
                                found_lines.append(line)
            except: continue
            progress["value"] = i + 1
            root.update_idletasks()

        with open(output_file, "w", encoding="utf-8") as out:
            out.writelines(found_lines)

        messagebox.showinfo("MARECKI SYSTEM", f"ZAKOŃCZONO.\nZnaleziono: {len(found_lines)} unikalnych linii.\nZapisano w: {output_file}")
    except Exception as e: messagebox.showerror("FATAL ERROR", str(e))

root = tk.Tk()
root.title("MARECKI - SEARCH ENGINE")
root.geometry("600x420")
root.configure(bg="#000000")
root.resizable(False, False)

frame = tk.Frame(root, bg="#000000", padx=35, pady=35)
frame.pack(expand=True, fill="both")

tk.Label(frame, text="FOLDER ŹRÓDŁOWY:", font=("Arial", 10, "bold"), bg="#000000", fg="#ffffff").pack(anchor="w")
folder_path_entry = tk.Entry(frame, bg="#1a1a1a", fg="#ffffff", borderwidth=0, highlightthickness=1, highlightbackground="#333333")
folder_path_entry.pack(pady=(5, 10), fill="x")
tk.Button(frame, text="WYBIERZ FOLDER", command=lambda: (folder_path_entry.delete(0, tk.END), folder_path_entry.insert(0, filedialog.askdirectory())), bg="#333333", fg="#ffffff", relief="flat", cursor="hand2").pack(anchor="w")

tk.Label(frame, text="SZUKANA FRAZA:", font=("Arial", 10, "bold"), bg="#000000", fg="#ffffff").pack(anchor="w", pady=(25, 5))
entry_phrase = tk.Entry(frame, bg="#1a1a1a", fg="#ffffff", borderwidth=0, highlightthickness=1, highlightbackground="#333333")
entry_phrase.insert(0, "cda.pl")
entry_phrase.pack(pady=5, fill="x")

progress = ttk.Progressbar(frame, orient="horizontal", mode="determinate")
progress.pack(pady=20, fill="x")

start_btn = tk.Button(frame, text="URUCHOM I ZAPISZ", command=search_files, bg="#ffffff", fg="#000000", font=("Arial", 10, "bold"), relief="flat", height=2, cursor="hand2")
start_btn.pack(side="bottom", fill="x")

root.mainloop()

