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
        self.root.geometry("700x650")  # Increased height for subtitle section

        # --- URL and Fetch Section ---
        self.url_label = ttk.Label(root, text="Video URL:")
        self.url_label.pack(pady=5)

        self.url_entry = ttk.Entry(root, width=80)
        self.url_entry.pack(pady=5, padx=10)

        self.fetch_button = ttk.Button(root, text="Fetch Formats", command=self.start_fetch_formats)
        self.fetch_button.pack(pady=10)

        # --- Download Mode Selection ---
        self.mode_frame = ttk.LabelFrame(root, text="Download Mode")
        self.mode_frame.pack(pady=5, padx=10, fill="x")
        
        self.mode_var = tk.StringVar(value="simple")
        self.simple_mode_radio = ttk.Radiobutton(
            self.mode_frame, text="Simple Mode (Download Complete Video)", 
            variable=self.mode_var, value="simple", command=self.toggle_mode)
        self.simple_mode_radio.pack(side="left", padx=10, pady=5)
        
        self.advanced_mode_radio = ttk.Radiobutton(
            self.mode_frame, text="Advanced Mode (Download Components Separately)", 
            variable=self.mode_var, value="advanced", command=self.toggle_mode)
        self.advanced_mode_radio.pack(side="left", padx=10, pady=5)

        # --- Format Selection ---
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(pady=5, fill="both", expand=True)
        
        # Simple mode tab
        self.simple_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.simple_frame, text="Simple Mode")
        
        self.formats_label = ttk.Label(self.simple_frame, text="Available Formats:")
        self.formats_label.pack(pady=5)

        self.formats_listbox = tk.Listbox(self.simple_frame, height=10, width=100)
        self.formats_listbox.pack(pady=5, padx=10, fill="both", expand=True)
        
        # Advanced mode tab
        self.advanced_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.advanced_frame, text="Advanced Mode")
        
        self.components_frame = ttk.Frame(self.advanced_frame)
        self.components_frame.pack(fill="both", expand=True)
        
        # Video streams
        self.video_frame = ttk.LabelFrame(self.components_frame, text="Video Streams")
        self.video_frame.pack(pady=5, padx=10, fill="both", expand=True)
        
        self.video_listbox = tk.Listbox(self.video_frame, height=4, width=100, selectmode=tk.SINGLE)
        self.video_listbox.pack(pady=5, padx=10, fill="both", expand=True)
        
        # Audio streams
        self.audio_frame = ttk.LabelFrame(self.components_frame, text="Audio Streams")
        self.audio_frame.pack(pady=5, padx=10, fill="both", expand=True)
        
        self.audio_listbox = tk.Listbox(self.audio_frame, height=4, width=100, selectmode=tk.SINGLE)
        self.audio_listbox.pack(pady=5, padx=10, fill="both", expand=True)
        
        # Subtitle selection
        self.subtitle_frame = ttk.LabelFrame(self.components_frame, text="Available Subtitles")
        self.subtitle_frame.pack(pady=5, padx=10, fill="both", expand=True)
        
        self.subtitle_list_frame = ttk.Frame(self.subtitle_frame)
        self.subtitle_list_frame.pack(fill="both", expand=True)
        
        self.subtitle_listbox = tk.Listbox(self.subtitle_list_frame, height=4, width=80, 
                                          selectmode=tk.MULTIPLE)
        self.subtitle_listbox.pack(side="left", pady=5, padx=5, fill="both", expand=True)
        
        self.subtitle_scrollbar = ttk.Scrollbar(self.subtitle_list_frame, orient="vertical", 
                                               command=self.subtitle_listbox.yview)
        self.subtitle_scrollbar.pack(side="right", fill="y")
        self.subtitle_listbox.config(yscrollcommand=self.subtitle_scrollbar.set)
        
        self.subtitle_info_label = ttk.Label(self.subtitle_frame, 
                                           text="No subtitles available. Select multiple with Ctrl/Shift.")
        self.subtitle_info_label.pack(pady=2)
        
        # --- Additional Download Options ---
        self.options_frame = ttk.Frame(root)
        self.options_frame.pack(pady=5)

        self.thumbnail_var = tk.BooleanVar()
        self.thumbnail_checkbox = ttk.Checkbutton(
            self.options_frame, text="Download Thumbnail", variable=self.thumbnail_var
        )
        self.thumbnail_checkbox.pack(side="left", padx=10)

        self.subtitle_var = tk.BooleanVar()
        self.subtitle_checkbox = ttk.Checkbutton(
            self.options_frame, text="Download Subtitles", variable=self.subtitle_var, state="disabled",
            command=self.toggle_subtitle_selection
        )
        self.subtitle_checkbox.pack(side="left", padx=10)

        # --- Download Buttons ---
        self.download_button = ttk.Button(root, text="Download Selected", command=self.start_download)
        self.download_button.pack(pady=10)

        # --- Progress and Status ---
        self.progress = ttk.Progressbar(root, orient="horizontal", length=500, mode="determinate")
        self.progress.pack(pady=10)

        self.status_label = ttk.Label(root, text="Status: Ready")
        self.status_label.pack(side="bottom", fill="x", padx=10, pady=5)

        # --- Internal State ---
        self.formats_data = []
        self.video_formats = []
        self.audio_formats = []
        self.available_subs = {}  # Changed to dictionary: {lang_code: lang_name}
        self.subtitle_data = {}   # Detailed subtitle info
        self.message_queue = queue.Queue()
        self.check_queue()
        
        # Initially hide Advanced tab
        self.notebook.hide(1)

    def toggle_mode(self):
        if self.mode_var.get() == "simple":
            self.notebook.select(0)
            self.notebook.hide(1)
        else:
            self.notebook.select(1)
            self.notebook.hide(0)
            
    def toggle_subtitle_selection(self):
        # Enable or disable subtitle selection in advanced mode based on checkbox
        if self.mode_var.get() == "advanced":
            if self.subtitle_var.get():
                self.subtitle_listbox.config(state="normal")
            else:
                self.subtitle_listbox.config(state="disabled")

    def check_queue(self):
        try:
            message = self.message_queue.get(block=False)
            msg_type = message[0]
            if msg_type == "formats":
                # Now receives formats, subtitles and processes them
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
        self.video_listbox.delete(0, tk.END)
        self.audio_listbox.delete(0, tk.END)
        self.subtitle_listbox.delete(0, tk.END)
        self.formats_data = []
        self.video_formats = []
        self.audio_formats = []
        self.available_subs = {}
        self.subtitle_data = {}
        
        # Reset subtitle checkbox and UI elements
        self.subtitle_checkbox.config(state="disabled", text="Download Subtitles")
        self.subtitle_var.set(False)
        self.subtitle_info_label.config(text="No subtitles available. Select multiple with Ctrl/Shift.")
        
        self.update_status("Fetching info...")
        self.fetch_button.config(state="disabled")

        thread = threading.Thread(target=self.fetch_formats_thread, args=(url,))
        thread.daemon = True
        thread.start()

    def fetch_formats_thread(self, url):
        try:
            # First get list of available subtitles with --list-subs
            command = ["yt-dlp.exe", "--list-subs", url]
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            stdout, stderr = process.communicate()
            
            # Parse the subtitle information from the output
            subtitle_info = self.parse_subtitle_info(stdout)
            
            # Now get the full video info
            command = ["yt-dlp.exe", "--dump-json", url]
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                raise Exception(f"yt-dlp error:\n{stderr}")

            video_info = json.loads(stdout)
            
            # Extract detailed subtitle information
            subtitles = video_info.get('subtitles', {})
            auto_captions = video_info.get('automatic_captions', {})
            
            # Send formats AND subtitles back to the main thread
            self.message_queue.put(("formats", video_info["formats"], 
                                   {"manual": subtitles, "auto": auto_captions, "parsed": subtitle_info}))
            self.message_queue.put(("status", "Info loaded. Select format and options, then click Download."))

        except Exception as e:
            self.message_queue.put(("error", str(e)))
        finally:
            self.message_queue.put(("status", "Ready"))
            
    def parse_subtitle_info(self, output):
        """Parse the subtitle information from yt-dlp --list-subs output"""
        subtitle_info = {"manual": [], "auto": []}
        
        # Extract available subtitles
        manual_section = False
        auto_section = False
        
        for line in output.splitlines():
            line = line.strip()
            
            if "Available subtitles for" in line:
                manual_section = True
                continue
                
            if "Available automatic captions for" in line:
                manual_section = False
                auto_section = True
                continue
                
            # Parse language entries
            if manual_section or auto_section:
                # Format is typically: "en    English"
                parts = line.split()
                if len(parts) >= 2 and len(parts[0]) <= 5:  # Language codes are usually short
                    lang_code = parts[0]
                    lang_name = " ".join(parts[1:])
                    
                    if manual_section:
                        subtitle_info["manual"].append({"code": lang_code, "name": lang_name})
                    elif auto_section:
                        subtitle_info["auto"].append({"code": lang_code, "name": lang_name})
                        
        return subtitle_info

    def update_formats_list(self, formats, subtitles):
        self.formats_data = formats
        
        # Process subtitle information
        self.subtitle_data = subtitles
        subtitle_count = 0
        
        # Clear subtitle listbox
        self.subtitle_listbox.delete(0, tk.END)
        
        # Add manual subtitles
        if "parsed" in subtitles and "manual" in subtitles["parsed"]:
            for sub in subtitles["parsed"]["manual"]:
                display_text = f"{sub['code']} - {sub['name']} (Manual)"
                self.subtitle_listbox.insert(tk.END, display_text)
                self.available_subs[sub['code']] = {"name": sub['name'], "type": "manual"}
                subtitle_count += 1
                
        # Add auto-generated subtitles
        if "parsed" in subtitles and "auto" in subtitles["parsed"]:
            for sub in subtitles["parsed"]["auto"]:
                display_text = f"{sub['code']} - {sub['name']} (Auto-Generated)"
                self.subtitle_listbox.insert(tk.END, display_text)
                self.available_subs[sub['code']] = {"name": sub['name'], "type": "auto"}
                subtitle_count += 1
        
        # Categorize formats for advanced mode
        self.video_formats = []
        self.audio_formats = []
        combined_formats = []
        
        for f in formats:
            vcodec = f.get('vcodec', 'none')
            acodec = f.get('acodec', 'none')
            
            # Categorize the format
            if vcodec != 'none' and acodec != 'none':
                combined_formats.append(f)  # Both audio and video
            elif vcodec != 'none' and acodec == 'none':
                self.video_formats.append(f)  # Video only
            elif vcodec == 'none' and acodec != 'none':
                self.audio_formats.append(f)  # Audio only
        
        # Populate simple mode list (all formats)
        for f in formats:
            filesize = f.get('filesize') or f.get('filesize_approx')
            filesize_str = f"{filesize / (1024*1024):.2f} MB" if filesize else "N/A"
            display_text = (
                f"{f['format_id']:<5} | {f.get('ext', 'N/A'):<5} | "
                f"{f.get('resolution', 'audio only'):<12} | "
                f"{filesize_str:<12} | {f.get('format_note', '')}"
            )
            self.formats_listbox.insert(tk.END, display_text)
        
        # Populate advanced mode lists
        for f in self.video_formats:
            filesize = f.get('filesize') or f.get('filesize_approx')
            filesize_str = f"{filesize / (1024*1024):.2f} MB" if filesize else "N/A"
            display_text = (
                f"{f['format_id']:<5} | {f.get('ext', 'N/A'):<5} | "
                f"{f.get('resolution', 'N/A'):<12} | "
                f"{filesize_str:<12} | {f.get('format_note', '')}"
            )
            self.video_listbox.insert(tk.END, display_text)
            
        for f in self.audio_formats:
            filesize = f.get('filesize') or f.get('filesize_approx')
            filesize_str = f"{filesize / (1024*1024):.2f} MB" if filesize else "N/A"
            display_text = (
                f"{f['format_id']:<5} | {f.get('ext', 'N/A'):<5} | "
                f"{f.get('abr', 'N/A'):<12} | "
                f"{filesize_str:<12} | {f.get('format_note', '')}"
            )
            self.audio_listbox.insert(tk.END, display_text)
        
        # Update subtitle UI elements based on availability
        if subtitle_count > 0:
            self.subtitle_checkbox.config(state="normal", text=f"Download Subtitles ({subtitle_count} found)")
            self.subtitle_info_label.config(text=f"Found {subtitle_count} subtitles. Select multiple with Ctrl/Shift.")
        else:
            self.subtitle_checkbox.config(state="disabled", text="Download Subtitles (None found)")
            self.subtitle_info_label.config(text="No subtitles available.")
            
        self.fetch_button.config(state="normal")

    def start_download(self):
        if self.mode_var.get() == "simple":
            self.start_simple_download()
        else:
            self.start_advanced_download()
            
    def start_simple_download(self):
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
            initialfile=f"{self.url_entry.get().split('v=')[-1]}" 
        )
        if not save_path_no_ext:
            self.update_status("Download cancelled.")
            return

        self.progress['value'] = 0
        self.download_button.config(state="disabled")
        self.fetch_button.config(state="disabled")

        command = [
            "yt-dlp.exe",
            "-f", final_format_selector,
            "--merge-output-format", "mp4",
            "-o", f"{save_path_no_ext}.%(ext)s",
            "--progress",
            url
        ]

        if self.thumbnail_var.get():
            command.append("--write-thumbnail")

        if self.subtitle_var.get():
            command.append("--write-subs")
            command.append("--write-auto-subs")

        self.update_status("Starting download...")
        thread = threading.Thread(target=self.download_thread, args=(command,))
        thread.daemon = True
        thread.start()
        
    def start_advanced_download(self):
        url = self.url_entry.get()
        download_tasks = []
        
        # Check for video selection
        video_index = self.video_listbox.curselection()
        if video_index:
            video_format = self.video_formats[video_index[0]]
            download_tasks.append(("video", video_format))
            
        # Check for audio selection
        audio_index = self.audio_listbox.curselection()
        if audio_index:
            audio_format = self.audio_formats[audio_index[0]]
            download_tasks.append(("audio", audio_format))
        
        # Check if specific subtitles are selected
        selected_subtitles = []
        if self.subtitle_var.get() and self.available_subs:
            selected_indices = self.subtitle_listbox.curselection()
            if selected_indices:
                # Get selected subtitle languages
                selected_langs = []
                for index in selected_indices:
                    item_text = self.subtitle_listbox.get(index)
                    lang_code = item_text.split(' ')[0]  # Extract language code
                    selected_langs.append(lang_code)
                    
                download_tasks.append(("subtitles", selected_langs))
            else:
                # If checkbox is checked but no specific languages selected, download all
                download_tasks.append(("subtitles", list(self.available_subs.keys())))
            
        # Check if thumbnail selected
        if self.thumbnail_var.get():
            download_tasks.append(("thumbnail", None))
            
        if not download_tasks:
            messagebox.showwarning("Warning", "Please select at least one component to download.")
            return
            
        # Ask for directory to save files
        save_dir = filedialog.askdirectory(title="Select directory to save components")
        if not save_dir:
            self.update_status("Download cancelled.")
            return
            
        # Disable UI during download
        self.progress['value'] = 0
        self.download_button.config(state="disabled")
        self.fetch_button.config(state="disabled")
        
        # Start download thread
        thread = threading.Thread(target=self.download_components_thread, 
                                  args=(url, download_tasks, save_dir))
        thread.daemon = True
        thread.start()
        
    def download_components_thread(self, url, tasks, save_dir):
        try:
            total_tasks = len(tasks)
            completed_tasks = 0
            
            for task_type, task_data in tasks:
                # Update status
                self.message_queue.put(("status", f"Downloading {task_type}..."))
                
                if task_type == "video":
                    # Download video-only stream
                    format_id = task_data['format_id']
                    command = [
                        "yt-dlp.exe",
                        "-f", format_id,
                        "-o", f"{save_dir}/%(title)s_video.%(ext)s",
                        "--progress",
                        url
                    ]
                    self.run_download_command(command)
                    
                elif task_type == "audio":
                    # Download audio-only stream
                    format_id = task_data['format_id']
                    command = [
                        "yt-dlp.exe",
                        "-f", format_id,
                        "-o", f"{save_dir}/%(title)s_audio.%(ext)s",
                        "--progress",
                        url
                    ]
                    self.run_download_command(command)
                    
                elif task_type == "subtitles":
                    # Download selected subtitles only
                    selected_langs = task_data
                    
                    # Create subtitle language selector
                    sub_langs = ",".join(selected_langs)
                    
                    command = [
                        "yt-dlp.exe",
                        "--skip-download",
                        "--write-subs",
                        "--write-auto-subs",
                        "--sub-langs", sub_langs,
                        "-o", f"{save_dir}/%(title)s",
                        url
                    ]
                    self.run_download_command(command)
                    
                elif task_type == "thumbnail":
                    # Download thumbnail only
                    command = [
                        "yt-dlp.exe",
                        "--skip-download",
                        "--write-thumbnail",
                        "-o", f"{save_dir}/%(title)s",
                        url
                    ]
                    self.run_download_command(command)
                
                completed_tasks += 1
                self.message_queue.put(("progress", (completed_tasks / total_tasks) * 100))
                
            self.message_queue.put(("done",))
            
        except Exception as e:
            self.message_queue.put(("error", str(e)))
            
    def run_download_command(self, command):
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