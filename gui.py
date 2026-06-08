import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import json
import threading
import os
import shutil

class YtDlpGui:
    def __init__(self, root):
        self.root = root
        self.root.title("yt-dlp GUI v2.0")
        self.root.geometry("1000x700")

        # --- Variables ---
        self.yt_dlp_path = tk.StringVar()
        self.download_path = tk.StringVar(value=os.getcwd())
        self.status_var = tk.StringVar(value="Ready")
        
        # Video Tab Variables
        self.video_url = tk.StringVar()
        self.video_mode = tk.StringVar(value="video") # video | audio
        self.video_info = tk.StringVar(value="No video fetched")
        
        # Channel Variables
        self.channel_url = tk.StringVar()
        self.channel_mode = tk.StringVar(value="video") # video | audio
        self.channel_data = []

        # Default Format Settings
        self.default_res = tk.StringVar(value="Best")
        self.default_codec = tk.StringVar(value="Best (Auto)")
        self.available_formats = [("Use Defaults (Configured above)", None, None)]

        # Auto-detect yt-dlp
        yt_dlp_bin = shutil.which("yt-dlp") or shutil.which("yt-dlp.exe")
        if yt_dlp_bin:
            self.yt_dlp_path.set(yt_dlp_bin)
        elif os.path.exists("yt-dlp.exe"):
            self.yt_dlp_path.set(os.path.abspath("yt-dlp.exe"))
            
        # Detect local ffmpeg
        self.ffmpeg_path = ""
        local_ffmpeg = os.path.join(os.getcwd(), "ffmpeg-8.0.1", "bin", "ffmpeg.exe")
        if os.path.exists(local_ffmpeg):
            self.ffmpeg_path = local_ffmpeg
        elif shutil.which("ffmpeg"):
            self.ffmpeg_path = shutil.which("ffmpeg")

        # Detect JS runtime to avoid YouTube extraction warnings/failures
        self.js_args = []
        if shutil.which("node"):
            self.js_args = ["--js-runtimes", "node"]

        self._create_ui()

    def _create_ui(self):
        # 1. Global Config Section (Top)
        config_frame = ttk.LabelFrame(self.root, text="Global Configuration", padding=5)
        config_frame.pack(fill="x", padx=5, pady=5)
        
        # Row 1: Paths
        row1 = ttk.Frame(config_frame)
        row1.pack(fill="x", pady=2)
        
        ttk.Label(row1, text="yt-dlp Path:").pack(side="left", padx=5)
        ttk.Entry(row1, textvariable=self.yt_dlp_path, width=40).pack(side="left", padx=5)
        ttk.Button(row1, text="Browse", command=self._browse_exe).pack(side="left", padx=2)
        ttk.Button(row1, text="Update yt-dlp", command=lambda: self._start_thread(self._update_yt_dlp)).pack(side="left", padx=2)
        
        ttk.Label(row1, text="Save To:").pack(side="left", padx=10)
        ttk.Entry(row1, textvariable=self.download_path, width=40).pack(side="left", padx=5)
        ttk.Button(row1, text="Browse", command=self._browse_dir).pack(side="left")

        # Row 2: Default Format Settings
        row2 = ttk.Frame(config_frame)
        row2.pack(fill="x", pady=2)
        
        ttk.Label(row2, text="Default Resolution:").pack(side="left", padx=5)
        self.default_res_combo = ttk.Combobox(row2, textvariable=self.default_res, values=["Best", "2160p (4K)", "1440p (2K)", "1080p", "720p", "480p", "360p"], width=15, state="readonly")
        self.default_res_combo.pack(side="left", padx=5)
        
        ttk.Label(row2, text="Default Format/Codec:").pack(side="left", padx=10)
        self.default_codec_combo = ttk.Combobox(row2, textvariable=self.default_codec, values=["Best (Auto)", "MP4 (H.264/AAC preferred)", "WebM (VP9/Opus preferred)"], width=28, state="readonly")
        self.default_codec_combo.pack(side="left", padx=5)

        # 2. Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Tab 1: Single Video
        self.tab_video = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_video, text="Video Download")
        self._build_video_tab(self.tab_video)

        # Tab 2: Channel
        self.tab_channel = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_channel, text="Channel Download")
        self._build_channel_tab(self.tab_channel)

        # 3. Status Bar
        status_frame = ttk.Frame(self.root, padding=5)
        status_frame.pack(fill="x", side="bottom")
        ttk.Label(status_frame, textvariable=self.status_var, relief="sunken").pack(fill="x")

    def _build_video_tab(self, parent):
        # Input
        input_frame = ttk.Frame(parent)
        input_frame.pack(fill="x", pady=10)
        ttk.Label(input_frame, text="Video URL:").pack(side="left")
        ttk.Entry(input_frame, textvariable=self.video_url, width=60).pack(side="left", padx=5)
        ttk.Button(input_frame, text="Fetch Info", command=lambda: self._start_thread(self._fetch_video)).pack(side="left")

        # Info Display
        info_frame = ttk.LabelFrame(parent, text="Video Information", padding=10)
        info_frame.pack(fill="both", expand=True, pady=10)
        ttk.Label(info_frame, textvariable=self.video_info, justify="left", font=("Consolas", 10)).pack(anchor="nw")

        # Actions
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill="x", pady=10)
        
        ttk.Label(action_frame, text="Download Mode:").pack(side="left")
        ttk.Radiobutton(action_frame, text="Video+Audio", variable=self.video_mode, value="video").pack(side="left", padx=10)
        ttk.Radiobutton(action_frame, text="Best Audio (MP3)", variable=self.video_mode, value="audio").pack(side="left")
        
        ttk.Label(action_frame, text="Specific Resolution:").pack(side="left", padx=(20, 5))
        self.format_combobox = ttk.Combobox(action_frame, width=35, state="readonly")
        self.format_combobox.pack(side="left", padx=5)
        self.format_combobox['values'] = ["Use Defaults (Configured above)"]
        self.format_combobox.current(0)
        
        ttk.Button(action_frame, text="Download Video", command=lambda: self._start_thread(self._download_video)).pack(side="right", padx=10)

    def _build_channel_tab(self, parent):
        # Input
        input_frame = ttk.Frame(parent)
        input_frame.pack(fill="x", pady=10)
        ttk.Label(input_frame, text="Channel URL:").pack(side="left")
        ttk.Entry(input_frame, textvariable=self.channel_url, width=60).pack(side="left", padx=5)
        ttk.Button(input_frame, text="Fetch List", command=lambda: self._start_thread(self._fetch_channel)).pack(side="left")

        # Treeview
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill="both", expand=True, pady=5)
        
        columns = ("ID", "Title", "Status")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="extended")
        tree.heading("ID", text="ID")
        tree.heading("Title", text="Title")
        tree.heading("Status", text="Status")
        tree.column("ID", width=120, stretch=False)
        tree.column("Title", width=400)
        tree.column("Status", width=150, stretch=False)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.channel_tree = tree

        # Controls
        ctrl_frame = ttk.Frame(parent)
        ctrl_frame.pack(fill="x", pady=5)
        
        ttk.Button(ctrl_frame, text="Select All", command=lambda: self._select_all(tree)).pack(side="left", padx=2)
        ttk.Button(ctrl_frame, text="Select None", command=lambda: self._select_none(tree)).pack(side="left", padx=2)

        # Download Actions
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill="x", pady=10)
        
        ttk.Label(action_frame, text="Batch Format:").pack(side="left")
        ttk.Radiobutton(action_frame, text="Best Video+Audio", variable=self.channel_mode, value="video").pack(side="left", padx=10)
        ttk.Radiobutton(action_frame, text="Best Audio (MP3)", variable=self.channel_mode, value="audio").pack(side="left")
        
        ttk.Button(action_frame, text="Download Selected", command=lambda: self._start_thread(self._download_channel)).pack(side="right", padx=10)

    # --- Helpers ---
    def _browse_exe(self):
        f = filedialog.askopenfilename(filetypes=[("Executables", "*.exe")])
        if f: self.yt_dlp_path.set(f)

    def _browse_dir(self):
        d = filedialog.askdirectory()
        if d: self.download_path.set(d)

    def log(self, msg):
        self.status_var.set(msg)

    def _start_thread(self, target):
        threading.Thread(target=target, daemon=True).start()

    def _update_yt_dlp(self):
        exe = self.yt_dlp_path.get()
        if not exe:
            self.log("No yt-dlp path configured.")
            messagebox.showerror("Error", "Please configure or browse for the yt-dlp executable first.")
            return

        self.log("Updating yt-dlp...")
        try:
            cmd = [exe, "-U"]
            proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            if proc.returncode == 0:
                self.log("yt-dlp updated successfully.")
                messagebox.showinfo("Success", f"yt-dlp updated successfully:\n{proc.stdout}")
            else:
                self.log("yt-dlp update failed.")
                messagebox.showerror("Error", f"yt-dlp update failed:\n{proc.stderr}\n{proc.stdout}")
        except Exception as e:
            self.log(f"Exception during update: {str(e)}")
            messagebox.showerror("Error", f"Exception during update:\n{str(e)}")

    def _get_format_selector(self, res_val, codec_val):
        # Parse height
        height_limit = ""
        if "2160p" in res_val:
            height_limit = "[height<=2160]"
        elif "1440p" in res_val:
            height_limit = "[height<=1440]"
        elif "1080p" in res_val:
            height_limit = "[height<=1080]"
        elif "720p" in res_val:
            height_limit = "[height<=720]"
        elif "480p" in res_val:
            height_limit = "[height<=480]"
        elif "360p" in res_val:
            height_limit = "[height<=360]"

        # Format string based on codec selection
        if "MP4" in codec_val:
            fmt = f"bv*{height_limit}[ext=mp4]+ba[ext=m4a]/bv*{height_limit}+ba/b"
            merge_fmt = "mp4"
        elif "WebM" in codec_val:
            fmt = f"bv*{height_limit}[ext=webm]+ba[ext=webm]/bv*{height_limit}+ba/b"
            merge_fmt = "webm"
        else: # Best (Auto)
            fmt = f"bv*{height_limit}+ba/b"
            merge_fmt = None
            
        return fmt, merge_fmt
    
    def _select_all(self, tree):
        for item in tree.get_children():
            tree.selection_add(item)
            
    def _select_none(self, tree):
        tree.selection_remove(tree.get_children())

    # --- Video Logic ---
    def _fetch_video(self):
        url = self.video_url.get().strip()
        exe = self.yt_dlp_path.get()
        if not url or not exe:
            self.log("Error: Missing URL or yt-dlp path")
            return

        # Reset format combobox
        self.available_formats = [("Use Defaults (Configured above)", None, None)]
        self.format_combobox['values'] = ["Use Defaults (Configured above)"]
        self.format_combobox.current(0)

        self.log("Fetching video info...")
        try:
            cmd = [exe] + self.js_args + ["--dump-json", "--no-warnings", url]
            res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            if res.returncode == 0:
                data = json.loads(res.stdout)
                title = data.get('title', 'Unknown')
                duration = data.get('duration_string', 'Unknown')
                uploader = data.get('uploader', 'Unknown')
                self.video_info.set(f"Title: {title}\nDuration: {duration}\nChannel: {uploader}")
                
                # Parse formats
                formats = data.get('formats', [])
                video_options_raw = []
                seen_resolutions = set()
                
                for f in formats:
                    vcodec = f.get('vcodec')
                    if not vcodec or vcodec == 'none':
                        continue
                    height = f.get('height')
                    if not height:
                        continue
                    ext = f.get('ext', '')
                    fps = f.get('fps', 0) or 0
                    
                    res_key = (height, ext, fps)
                    if res_key in seen_resolutions:
                        continue
                    seen_resolutions.add(res_key)
                    
                    fps_label = f"@{fps}fps" if fps and fps > 30 else ""
                    vcodec_name = vcodec.split('.')[0] if vcodec else 'unknown'
                    display = f"{height}p{fps_label} ({ext}) - {vcodec_name}"
                    
                    video_options_raw.append({
                        "height": height,
                        "fps": fps,
                        "ext": ext,
                        "display": display,
                        "format_id": f.get('format_id')
                    })
                
                # Sort by height desc, then fps desc
                video_options_raw.sort(key=lambda x: (x['height'], x['fps']), reverse=True)
                
                # Convert to display list
                for opt in video_options_raw:
                    self.available_formats.append((opt['display'], opt['format_id'], opt['ext']))
                    
                self.format_combobox['values'] = [opt[0] for opt in self.available_formats]
                self.format_combobox.current(0)
                
                self.log("Video info fetched.")
            else:
                self.log("Error fetching video info.")
                self.video_info.set(f"Error:\n{res.stderr[:200]}")
        except Exception as e:
            self.log(f"Exception: {str(e)}")

    def _download_video(self):
        url = self.video_url.get().strip()
        path = self.download_path.get()
        exe = self.yt_dlp_path.get()
        mode = self.video_mode.get()

        if not url or not exe: return

        self.log("Downloading...")
        cmd = [exe] + self.js_args + ["--no-part", "-P", path, "--no-playlist"]
        if self.ffmpeg_path:
            cmd.extend(["--ffmpeg-location", self.ffmpeg_path])
            
        if mode == "audio":
            cmd.extend(["-x", "--audio-format", "mp3", "--audio-quality", "0"])
        else:
            selected_idx = self.format_combobox.current()
            # Check if user selected a specific format or wants defaults
            if selected_idx > 0:
                _, format_id, ext = self.available_formats[selected_idx]
                cmd.extend(["-f", f"{format_id}+bestaudio/best"])
                if ext:
                    cmd.extend(["--merge-output-format", ext])
            else:
                # Use default settings
                res_val = self.default_res.get()
                codec_val = self.default_codec.get()
                fmt, merge_fmt = self._get_format_selector(res_val, codec_val)
                cmd.extend(["-f", fmt])
                if merge_fmt:
                    cmd.extend(["--merge-output-format", merge_fmt])
        
        cmd.append(url)

        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            if proc.returncode == 0:
                self.log("Download complete!")
                messagebox.showinfo("Success", "Download finished successfully.")
            else:
                self.log("Download failed.")
                messagebox.showerror("Error", f"Download failed:\n{proc.stderr}")
        except Exception as e:
            self.log(f"Error: {str(e)}")

    # --- Channel Logic ---
    def _fetch_channel(self):
        url = self.channel_url.get().strip()
        tree = self.channel_tree
        exe = self.yt_dlp_path.get()
        
        if not url or not exe:
            self.log("Missing configuration.")
            return

        self.log("Fetching channel list...")
        
        # Clear tree
        for item in tree.get_children():
            tree.delete(item)
            
        try:
            # --flat-playlist is key for speed
            cmd = [exe] + self.js_args + ["--dump-json", "--flat-playlist", "--no-warnings", url]
            res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            if res.returncode != 0:
                self.log("Error fetching list.")
                return

            lines = res.stdout.strip().split('\n')
            count = 0
            for line in lines:
                if not line.strip(): continue
                try:
                    entry = json.loads(line)
                    vid_id = entry.get('id')
                    title = entry.get('title', 'Unknown')
                    
                    if vid_id:
                        tree.insert("", "end", values=(vid_id, title, "Pending"))
                        count += 1
                except:
                    pass
            
            self.log(f"Fetched {count} items.")

        except Exception as e:
            self.log(f"Exception: {str(e)}")

    def _download_channel(self):
        tree = self.channel_tree
        fmt_mode = self.channel_mode.get()

        selected = tree.selection()
        if not selected:
            self.log("No items selected.")
            return

        path = self.download_path.get()
        exe = self.yt_dlp_path.get()
        
        total = len(selected)
        self.log(f"Starting batch download of {total} items...")

        for idx, item in enumerate(selected):
            vals = tree.item(item, "values")
            vid_id = vals[0]
            title = vals[1]
            
            # Update status
            tree.set(item, "Status", "Downloading...")
            self.log(f"Downloading ({idx+1}/{total}): {title[:30]}...")
            self.root.update_idletasks() # Force UI update

            # Build URL
            vid_url = f"https://www.youtube.com/watch?v={vid_id}"

            cmd = [exe] + self.js_args + ["--no-part", "-P", path]
            if self.ffmpeg_path:
                cmd.extend(["--ffmpeg-location", self.ffmpeg_path])
                
            if fmt_mode == "audio":
                cmd.extend(["-x", "--audio-format", "mp3", "--audio-quality", "0"])
            else:
                res_val = self.default_res.get()
                codec_val = self.default_codec.get()
                fmt, merge_fmt = self._get_format_selector(res_val, codec_val)
                cmd.extend(["-f", fmt])
                if merge_fmt:
                    cmd.extend(["--merge-output-format", merge_fmt])
            
            cmd.append(vid_url)

            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                
                if proc.returncode == 0:
                    tree.set(item, "Status", "Done")
                else:
                    tree.set(item, "Status", "Failed")
                    print(f"Failed {vid_id}: {proc.stderr}")
            except Exception as e:
                tree.set(item, "Status", "Error")
                print(e)
        
        self.log("Batch download finished.")
        messagebox.showinfo("Batch Done", f"Processed {total} items.")

if __name__ == "__main__":
    root = tk.Tk()
    app = YtDlpGui(root)
    root.mainloop()