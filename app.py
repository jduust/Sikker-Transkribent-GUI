import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
from backend import process_file
from wakepy import keep

class DiarizationApp:
    def __init__(self, root):
        self.root = root
        root.title("Sikker-Transkribent")
        root.geometry("800x620")

        self.folder_path = tk.StringVar()
        self.device = tk.StringVar(value="cpu")
        self.stop_flag = threading.Event()

        # Top frame
        top = tk.Frame(root)
        top.pack(padx=10, pady=8, fill=tk.X)
        tk.Label(top, text="Mappe med lydfiler:").grid(row=0, column=0, sticky="w")
        tk.Entry(top, textvariable=self.folder_path, width=60).grid(row=0, column=1)
        tk.Button(top, text="Vælg", command=self.browse_folder).grid(row=0, column=2, padx=4)
        tk.Label(top, text="Device:").grid(row=2, column=0, sticky="w")
        ttk.Combobox(top, textvariable=self.device, values=["cpu", "cuda"], width=10, state="readonly").grid(row=2, column=1, sticky="w")
        tk.Label(top, text="(Vælg 'cuda' hvis du har GPU)").grid(row=3, column=1, sticky="w")

        # File list
        list_frame = tk.Frame(root)
        list_frame.pack(padx=10, pady=6, fill=tk.BOTH, expand=False)
        self.file_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, width=90, height=14)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        btns = tk.Frame(list_frame)
        btns.pack(side=tk.LEFT, padx=6)
        tk.Button(btns, text="Select All", command=self.select_all).pack(fill=tk.X)
        tk.Button(btns, text="Clear", command=self.clear_selection).pack(fill=tk.X, pady=4)
        tk.Button(btns, text="Refresh", command=self.load_files).pack(fill=tk.X)

        # Run & progress
        run_frame = tk.Frame(root)
        run_frame.pack(padx=10, pady=8, fill=tk.X)
        self.run_btn = tk.Button(run_frame, text="Kør valgte filer", command=self.run_selected, bg="#2e8b57", fg="white")
        self.run_btn.pack(side=tk.LEFT)
        self.stop_btn = tk.Button(run_frame, text="Stop", command=self.stop_processing, bg="#b22222", fg="white", state="disabled")
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        self.progress = ttk.Progressbar(run_frame, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(side=tk.LEFT, padx=10)
        self.status_label = tk.Label(run_frame, text="Klar")
        self.status_label.pack(side=tk.LEFT)

        # Log
        tk.Label(root, text="Log:").pack(anchor="w", padx=10)
        self.log = scrolledtext.ScrolledText(root, height=16, state="disabled")
        self.log.pack(padx=10, pady=(0,10), fill=tk.BOTH, expand=True)

    # File operations
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)
            self.load_files()

    def load_files(self):
        self.file_listbox.delete(0, tk.END)
        folder = self.folder_path.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showinfo("Ingen mappe", "Vælg en gyldig mappe først.")
            return
        for f in sorted(os.listdir(folder)):
            path = os.path.join(folder, f)
            if os.path.isfile(path):
                self.file_listbox.insert(tk.END, f)

    def select_all(self):
        self.file_listbox.select_set(0, tk.END)

    def clear_selection(self):
        self.file_listbox.select_clear(0, tk.END)

    # Logging
    def log_message(self, msg):
        self.log.configure(state="normal")
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)
        self.log.configure(state="disabled")

    # Stop button
    def stop_processing(self):
        self.stop_flag.set()
        self.log_message("⏹️ Stop-signal sendt")

    # Run selected files
    def run_selected(self):
        selected_indices = self.file_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Ingen filer", "Vælg en eller flere filer.")
            return

        self.stop_flag.clear()
        self.run_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        files = [self.file_listbox.get(i) for i in selected_indices]
        folder = self.folder_path.get()
        device = self.device.get()

        def worker():
            with keep.running():
                try:
                    for f_idx, fname in enumerate(files, start=1):
                        if self.stop_flag.is_set():
                            self.log_message("⏹️ Processing stopped by user")
                            break
                        path = os.path.join(folder, fname)
                        self.progress["value"] = 0
                        self.status_label.config(text=f"Kører {fname} ({f_idx}/{len(files)})")

                        # Thread-safe callbacks
                        def log_cb(msg):
                            self.root.after(0, lambda: self.log_message(msg))

                        def prog_cb(current_sec, total_sec):
                            def update():
                                if total_sec:
                                    self.progress["maximum"] = total_sec
                                self.progress["value"] = min(current_sec, self.progress["maximum"])
                            self.root.after(0, update)

                        try:
                            process_file(
                                audio_path=path,
                                device=device,
                                log_callback=log_cb,
                                progress_callback=prog_cb,
                                stop_flag=self.stop_flag
                            )
                        except Exception as e:
                            self.log_message(f"❌ Fejl i {fname}: {e}")

                        self.progress["value"] = 0

                finally:
                    self.run_btn.config(state="normal")
                    self.stop_btn.config(state="disabled")
                    self.status_label.config(text="Færdig")

        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = DiarizationApp(root)
    root.mainloop()
