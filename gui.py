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
        
        # Playlist Variables
        self.playlist_url = tk.StringVar()
        self.playlist_mode = tk.StringVar(value="video") # video | audio
        self.playlist_data = [] # Stores (id, title, url)
        
        # Channel Variables
        self.channel_url = tk.StringVar()
        self.channel_mode = tk.StringVar(value="video") # video | audio
        self.channel_data = []

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

        self._create_ui()

    def _create_ui(self):
        # 1. Global Config Section (Top)
        config_frame = ttk.LabelFrame(self.root, text="Global Configuration", padding=5)
        config_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(config_frame, text="yt-dlp Path:").pack(side="left", padx=5)
        ttk.Entry(config_frame, textvariable=self.yt_dlp_path, width=40).pack(side="left", padx=5)
        ttk.Button(config_frame, text="Browse", command=self._browse_exe).pack(side="left")
        
        ttk.Label(config_frame, text="Save To:").pack(side="left", padx=10)
        ttk.Entry(config_frame, textvariable=self.download_path, width=40).pack(side="left", padx=5)
        ttk.Button(config_frame, text="Browse", command=self._browse_dir).pack(side="left")

        # 2. Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Tab 1: Single Video
        self.tab_video = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_video, text="Video Download")
        self._build_video_tab(self.tab_video)

        # Tab 2: Playlist
        self.tab_playlist = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_playlist, text="Playlist Download")
        self._build_list_tab(self.tab_playlist, "playlist")

        # Tab 3: Channel
        self.tab_channel = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_channel, text="Channel Download")
        self._build_list_tab(self.tab_channel, "channel")

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
        
        ttk.Label(action_frame, text="Download Format:").pack(side="left")
        ttk.Radiobutton(action_frame, text="Best Video+Audio", variable=self.video_mode, value="video").pack(side="left", padx=10)
        ttk.Radiobutton(action_frame, text="Best Audio (MP3)", variable=self.video_mode, value="audio").pack(side="left")
        
        ttk.Button(action_frame, text="Download Video", command=lambda: self._start_thread(self._download_video)).pack(side="right", padx=10)

    def _build_list_tab(self, parent, mode):
        # Determine vars based on mode
        url_var = self.playlist_url if mode == "playlist" else self.channel_url
        mode_var = self.playlist_mode if mode == "playlist" else self.channel_mode
        
        # Input
        input_frame = ttk.Frame(parent)
        input_frame.pack(fill="x", pady=10)
        ttk.Label(input_frame, text=f"{mode.capitalize()} URL:").pack(side="left")
        ttk.Entry(input_frame, textvariable=url_var, width=60).pack(side="left", padx=5)
        ttk.Button(input_frame, text="Fetch List", command=lambda: self._start_thread(lambda: self._fetch_list(mode))).pack(side="left")

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

        # Store tree ref
        if mode == "playlist":
            self.playlist_tree = tree
        else:
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
        ttk.Radiobutton(action_frame, text="Best Video+Audio", variable=mode_var, value="video").pack(side="left", padx=10)
        ttk.Radiobutton(action_frame, text="Best Audio (MP3)", variable=mode_var, value="audio").pack(side="left")
        
        ttk.Button(action_frame, text="Download Selected", command=lambda: self._start_thread(lambda: self._download_batch(mode))).pack(side="right", padx=10)

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

        self.log("Fetching video info...")
        try:
            cmd = [exe, "--dump-json", "--no-warnings", url]
            res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            if res.returncode == 0:
                data = json.loads(res.stdout)
                title = data.get('title', 'Unknown')
                duration = data.get('duration_string', 'Unknown')
                uploader = data.get('uploader', 'Unknown')
                self.video_info.set(f"Title: {title}\nDuration: {duration}\nChannel: {uploader}")
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
        cmd = [exe, "-P", path, "--no-playlist"]
        if self.ffmpeg_path:
            cmd.extend(["--ffmpeg-location", self.ffmpeg_path])
            
        if mode == "audio":
            cmd.extend(["-x", "--audio-format", "mp3", "--audio-quality", "0"])
        else:
            cmd.extend(["-f", "bv+ba/b"])
        
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

    # --- List Logic (Playlist/Channel) ---
    def _fetch_list(self, mode):
        # Setup references
        if mode == "playlist":
            url = self.playlist_url.get().strip()
            tree = self.playlist_tree
        else:
            url = self.channel_url.get().strip()
            tree = self.channel_tree
            
        exe = self.yt_dlp_path.get()
        
        if not url or not exe:
            self.log("Missing configuration.")
            return

        self.log(f"Fetching {mode} list...")
        
        # Clear tree
        for item in tree.get_children():
            tree.delete(item)
            
        try:
            # --flat-playlist is key for speed
            cmd = [exe, "--dump-json", "--flat-playlist", "--no-warnings", url]
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
                    # For flat playlist, we usually get 'id', 'title', 'url' (sometimes)
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

    def _download_batch(self, mode):
        if mode == "playlist":
            tree = self.playlist_tree
            fmt_mode = self.playlist_mode.get()
        else:
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
            # Standard youtube URL logic
            vid_url = f"https://www.youtube.com/watch?v={vid_id}"

            cmd = [exe, "-P", path]
            if self.ffmpeg_path:
                cmd.extend(["--ffmpeg-location", self.ffmpeg_path])
                
            if fmt_mode == "audio":
                cmd.extend(["-x", "--audio-format", "mp3", "--audio-quality", "0"])
            else:
                cmd.extend(["-f", "bv+ba/b"])
            
            cmd.append(vid_url)

            try:
                # We can subprocess.run here. Since this is already in a thread, it won't block UI.
                # However, loop is sequential.
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