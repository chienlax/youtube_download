import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import threading
import json
import re
import queue

class YTDLP_GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Downloader v2.0")
        self.root.geometry("700x550") # Increased height for new options

        # --- URL and Fetch Section ---
        self.url_label = ttk.Label(root, text="Video URL:")
        self.url_label.pack(pady=5)

        self.url_entry = ttk.Entry(root, width=80)
        self.url_entry.pack(pady=5, padx=10)

        self.fetch_button = ttk.Button(root, text="Fetch Formats", command=self.start_fetch_formats)
        self.fetch_button.pack(pady=10)

        # --- Format Selection ---
        self.formats_label = ttk.Label(root, text="Available Formats:")
        self.formats_label.pack(pady=5)

        self.formats_listbox = tk.Listbox(root, height=10, width=100)
        self.formats_listbox.pack(pady=5, padx=10)
        
        # --- NEW: Additional Download Options ---
        self.options_frame = ttk.Frame(root)
        self.options_frame.pack(pady=5)

        self.thumbnail_var = tk.BooleanVar()
        self.thumbnail_checkbox = ttk.Checkbutton(
            self.options_frame, text="Download Thumbnail", variable=self.thumbnail_var
        )
        self.thumbnail_checkbox.pack(side="left", padx=10)

        self.subtitle_var = tk.BooleanVar()
        self.subtitle_checkbox = ttk.Checkbutton(
            self.options_frame, text="Download Subtitles", variable=self.subtitle_var, state="disabled"
        )
        self.subtitle_checkbox.pack(side="left", padx=10)
        # --- End of New Section ---

        self.download_button = ttk.Button(root, text="Download Selected", command=self.start_download)
        self.download_button.pack(pady=10)

        # --- Progress and Status ---
        self.progress = ttk.Progressbar(root, orient="horizontal", length=500, mode="determinate")
        self.progress.pack(pady=10)

        self.status_label = ttk.Label(root, text="Status: Ready")
        self.status_label.pack(side="bottom", fill="x", padx=10, pady=5)

        # --- Internal State ---
        self.formats_data = []
        self.available_subs = [] # NEW: To store subtitle info
        self.message_queue = queue.Queue()
        self.check_queue()

    def check_queue(self):
        try:
            message = self.message_queue.get(block=False)
            msg_type = message[0]
            if msg_type == "formats":
                # MODIFIED: Now receives formats and subtitles
                self.update_formats_list(message[1], message[2])
            elif msg_type == "progress":
                self.update_progress(message[1])
            elif msg_type == "status":
                self.update_status(message[1])
            elif msg_type == "error":
                messagebox.showerror("Error", message[1])
                self.reset_ui()
            elif msg_type == "done":
                messagebox.showinfo("Success", "Download completed successfully!")
                self.reset_ui()
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.check_queue)

    def start_fetch_formats(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showwarning("Warning", "Please enter a URL.")
            return

        self.formats_listbox.delete(0, tk.END)
        self.formats_data = []
        self.available_subs = []
        # NEW: Reset subtitle checkbox on new fetch
        self.subtitle_checkbox.config(state="disabled", text="Download Subtitles")
        self.subtitle_var.set(False)
        
        self.update_status("Fetching info...")
        self.fetch_button.config(state="disabled")

        thread = threading.Thread(target=self.fetch_formats_thread, args=(url,))
        thread.daemon = True
        thread.start()

    def fetch_formats_thread(self, url):
        try:
            command = ["yt-dlp.exe", "--dump-json", url]
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                raise Exception(f"yt-dlp error:\n{stderr}")

            video_info = json.loads(stdout)
            
            # NEW: Extract subtitle information
            subtitles = video_info.get('subtitles', {})
            auto_captions = video_info.get('automatic_captions', {})
            available_subs_list = list(subtitles.keys()) + list(auto_captions.keys())
            
            # MODIFIED: Send formats AND subtitles back to the main thread
            self.message_queue.put(("formats", video_info["formats"], available_subs_list))
            self.message_queue.put(("status", "Info loaded. Select format and options, then click Download."))

        except Exception as e:
            self.message_queue.put(("error", str(e)))
        finally:
            self.message_queue.put(("status", "Ready"))

    # MODIFIED: Method now accepts subtitles list
    def update_formats_list(self, formats, subtitles):
        self.formats_data = formats
        self.available_subs = subtitles

        for f in formats:
            filesize = f.get('filesize') or f.get('filesize_approx')
            filesize_str = f"{filesize / (1024*1024):.2f} MB" if filesize else "N/A"
            display_text = (
                f"{f['format_id']:<5} | {f.get('ext', 'N/A'):<5} | "
                f"{f.get('resolution', 'audio only'):<12} | "
                f"{filesize_str:<12} | {f.get('format_note', '')}"
            )
            self.formats_listbox.insert(tk.END, display_text)
        
        # NEW: Enable or disable subtitle checkbox based on availability
        if self.available_subs:
            self.subtitle_checkbox.config(state="normal", text=f"Download Subtitles ({len(self.available_subs)} found)")
        else:
            self.subtitle_checkbox.config(state="disabled", text="Download Subtitles (None found)")
            
        self.fetch_button.config(state="normal")

    def start_download(self):
        selection_index = self.formats_listbox.curselection()
        if not selection_index:
            messagebox.showwarning("Warning", "Please select a format to download.")
            return

        selected_format_data = self.formats_data[selection_index[0]]
        format_id = selected_format_data['format_id']
        url = self.url_entry.get()
        
        is_video_only = selected_format_data.get('vcodec') != 'none' and selected_format_data.get('acodec') == 'none'
        final_format_selector = f"{format_id}+bestaudio" if is_video_only else format_id

        save_path_no_ext = filedialog.asksaveasfilename(
            filetypes=[("Video Files", "*.mp4 *.mkv"), ("Audio Files", "*.m4a *.mp3"), ("All files", "*.*")],
            # Default name based on video ID; yt-dlp will add the correct extension.
            initialfile=f"{self.url_entry.get().split('v=')[-1]}" 
        )
        if not save_path_no_ext:
            self.update_status("Download cancelled.")
            return

        self.progress['value'] = 0
        self.download_button.config(state="disabled")
        self.fetch_button.config(state="disabled")

        # --- MODIFIED: Build the command dynamically ---
        command = [
            "yt-dlp.exe",
            "-f", final_format_selector,
            "--merge-output-format", "mp4",
            "-o", f"{save_path_no_ext}.%(ext)s", # yt-dlp will replace %(ext)s
            "--progress",
            url
        ]

        if self.thumbnail_var.get():
            command.append("--write-thumbnail")

        if self.subtitle_var.get():
            command.append("--write-subs")
            command.append("--write-auto-subs") # Downloads both manual and auto-generated subs

        self.update_status("Starting download...")
        thread = threading.Thread(target=self.download_thread, args=(command,)) # Pass the whole command
        thread.daemon = True
        thread.start()

    # MODIFIED: Method now accepts the full command list
    def download_thread(self, command):
        try:
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, bufsize=1, universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            for line in process.stdout:
                self.message_queue.put(("status", line.strip()))
                match = re.search(r"\[download\]\s+([0-9.]+)%", line)
                if match:
                    percentage = float(match.group(1))
                    self.message_queue.put(("progress", percentage))

            process.wait()
            if process.returncode != 0:
                stderr_output = process.stderr.read()
                raise Exception(f"Download failed:\n{stderr_output}")

            self.message_queue.put(("done",))

        except Exception as e:
            self.message_queue.put(("error", str(e)))

    def update_progress(self, value):
        self.progress['value'] = value
        self.root.update_idletasks()

    def update_status(self, text):
        self.status_label.config(text=f"Status: {text}")

    def reset_ui(self):
        self.progress['value'] = 0
        self.update_status("Ready")
        self.download_button.config(state="normal")
        self.fetch_button.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = YTDLP_GUI(root)
    root.mainloop()