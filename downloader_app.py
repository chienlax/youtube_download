import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import subprocess
import threading
import json
import re
import queue
import os
from PIL import Image, ImageTk
from io import BytesIO
import urllib.request
import time

class YTDLP_GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Downloader v2.0")
        self.root.geometry("900x700")  # Increased size for channel mode

        # --- URL and Fetch Section ---
        self.url_label = ttk.Label(root, text="Video/Channel URL:")
        self.url_label.pack(pady=5)

        self.url_entry = ttk.Entry(root, width=80)
        self.url_entry.pack(pady=5, padx=10)

        # --- Button Frame ---
        self.button_frame = ttk.Frame(root)
        self.button_frame.pack(pady=5)
        
        self.fetch_button = ttk.Button(self.button_frame, text="Fetch Formats", command=self.start_fetch_formats)
        self.fetch_button.pack(side="left", padx=5)
        
        self.channel_fetch_button = ttk.Button(self.button_frame, text="Fetch Channel Videos", command=self.start_fetch_channel)
        self.channel_fetch_button.pack(side="left", padx=5)

        # --- Download Mode Selection ---
        self.mode_frame = ttk.LabelFrame(root, text="Download Mode")
        self.mode_frame.pack(pady=5, padx=10, fill="x")
        
        self.mode_var = tk.StringVar(value="simple")
        self.simple_mode_radio = ttk.Radiobutton(
            self.mode_frame, text="Simple Mode (Download Complete Video)", 
            variable=self.mode_var, value="simple", command=self.toggle_mode)
        self.simple_mode_radio.pack(side="left", padx=10, pady=5)
        
        self.advanced_mode_radio = ttk.Radiobutton(
            self.mode_frame, text="Advanced Mode (Download Components)", 
            variable=self.mode_var, value="advanced", command=self.toggle_mode)
        self.advanced_mode_radio.pack(side="left", padx=10, pady=5)
        
        self.channel_mode_radio = ttk.Radiobutton(
            self.mode_frame, text="Channel Mode (Batch Download)", 
            variable=self.mode_var, value="channel", command=self.toggle_mode)
        self.channel_mode_radio.pack(side="left", padx=10, pady=5)

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
        
        # Channel mode tab
        self.channel_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.channel_frame, text="Channel Videos")
        
        # Channel info frame
        self.channel_info_frame = ttk.Frame(self.channel_frame)
        self.channel_info_frame.pack(fill="x", pady=5, padx=10)
        
        self.channel_name_label = ttk.Label(self.channel_info_frame, text="Channel: Not loaded")
        self.channel_name_label.pack(side="left", padx=5)
        
        self.video_count_label = ttk.Label(self.channel_info_frame, text="Videos: 0")
        self.video_count_label.pack(side="left", padx=5)
        
        # Channel options frame
        self.channel_options_frame = ttk.Frame(self.channel_frame)
        self.channel_options_frame.pack(fill="x", pady=5, padx=10)
        
        self.format_label = ttk.Label(self.channel_options_frame, text="Download format:")
        self.format_label.pack(side="left", padx=5)
        
        self.format_var = tk.StringVar(value="best[height<=720]")
        self.format_combo = ttk.Combobox(self.channel_options_frame, textvariable=self.format_var, width=30)
        self.format_combo['values'] = [
            "best", "bestvideo+bestaudio", "best[height<=720]", 
            "best[height<=480]", "worst"
        ]
        self.format_combo.pack(side="left", padx=5)
        
        self.select_all_var = tk.BooleanVar()
        self.select_all_check = ttk.Checkbutton(
            self.channel_options_frame, text="Select All", 
            variable=self.select_all_var, command=self.toggle_select_all)
        self.select_all_check.pack(side="right", padx=5)
        
        # Create a canvas with scrollbar for the videos
        self.videos_canvas_frame = ttk.Frame(self.channel_frame)
        self.videos_canvas_frame.pack(fill="both", expand=True, pady=5, padx=10)
        
        self.videos_canvas = tk.Canvas(self.videos_canvas_frame, borderwidth=0)
        self.videos_scrollbar = ttk.Scrollbar(
            self.videos_canvas_frame, orient="vertical", command=self.videos_canvas.yview)
        self.videos_scrollbar.pack(side="right", fill="y")
        
        self.videos_canvas.pack(side="left", fill="both", expand=True)
        self.videos_canvas.configure(yscrollcommand=self.videos_scrollbar.set)
        
        self.videos_frame = ttk.Frame(self.videos_canvas)
        self.videos_canvas.create_window((0, 0), window=self.videos_frame, anchor="nw", tags="self.videos_frame")
        self.videos_frame.bind("<Configure>", self.on_frame_configure)
        
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
        
        # Channel mode data
        self.channel_videos = []  # List of videos in the channel
        self.selected_videos = []  # List of selected video indices
        self.video_checkboxes = []  # List of checkbox variables
        self.video_widgets = []  # References to video widgets for cleanup
        
        # Initially hide Advanced and Channel tabs
        self.notebook.hide(1)
        self.notebook.hide(2)

    def toggle_mode(self):
        mode = self.mode_var.get()
        # Hide all tabs
        for i in range(self.notebook.index("end")):
            self.notebook.hide(i)
        
        # Show the selected tab
        if mode == "simple":
            self.notebook.select(0)
        elif mode == "advanced":
            self.notebook.select(1)
        elif mode == "channel":
            self.notebook.select(2)

    def toggle_subtitle_selection(self):
        # Enable or disable subtitle selection in advanced mode based on checkbox
        if self.mode_var.get() == "advanced":
            if self.subtitle_var.get():
                self.subtitle_listbox.config(state="normal")
            else:
                self.subtitle_listbox.config(state="disabled")

    def toggle_select_all(self):
        select_all = self.select_all_var.get()
        for i, var in enumerate(self.video_checkboxes):
            var.set(select_all)
            if select_all:
                if i not in self.selected_videos:
                    self.selected_videos.append(i)
            else:
                if i in self.selected_videos:
                    self.selected_videos.remove(i)

    def check_queue(self):
        try:
            message = self.message_queue.get(block=False)
            msg_type = message[0]
            if msg_type == "formats":
                # Now receives formats, subtitles and processes them
                self.update_formats_list(message[1], message[2])
            elif msg_type == "channel_info":
                # Handle channel information
                self.update_channel_info(message[1])
            elif msg_type == "channel_videos":
                # Handle channel videos list
                self.update_channel_videos(message[1])
            elif msg_type == "channel_thumbnail":
                # Handle a channel video thumbnail
                self.update_video_thumbnail(message[1], message[2])
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
        self.channel_fetch_button.config(state="disabled")

        thread = threading.Thread(target=self.fetch_formats_thread, args=(url,))
        thread.daemon = True
        thread.start()
        
    def start_fetch_channel(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showwarning("Warning", "Please enter a channel URL.")
            return
            
        # Clear previous channel videos
        self.clear_channel_videos()
        self.channel_videos = []
        self.selected_videos = []
        self.video_checkboxes = []
        
        # Switch to channel mode
        self.mode_var.set("channel")
        self.toggle_mode()
        
        # Update UI state
        self.update_status("Fetching channel information...")
        self.fetch_button.config(state="disabled")
        self.channel_fetch_button.config(state="disabled")
        self.download_button.config(state="disabled")
        
        # Start thread to fetch channel info
        thread = threading.Thread(target=self.fetch_channel_thread, args=(url,))
        thread.daemon = True
        thread.start()

    def fetch_channel_thread(self, url):
        try:
            # First get basic channel info
            command = ["yt-dlp.exe", "--flat-playlist", "--dump-single-json", url]
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                raise Exception(f"yt-dlp error: {stderr}")

            channel_info = json.loads(stdout)
            self.message_queue.put(("channel_info", channel_info))
            self.message_queue.put(("status", "Fetching videos from channel..."))
            
            # Get detailed video information
            command = [
                "yt-dlp.exe", 
                "--flat-playlist", 
                "--dump-json",
                "--playlist-items", "1-30",  # Limit to 30 videos for performance
                url
            ]
            
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            videos = []
            for line in process.stdout:
                try:
                    video_info = json.loads(line)
                    videos.append(video_info)
                except json.JSONDecodeError:
                    continue
                    
            process.wait()
            if videos:
                self.message_queue.put(("channel_videos", videos))
                
                # Now fetch thumbnails for each video
                for i, video in enumerate(videos[:30]):  # Limit thumbnail fetching
                    try:
                        if 'thumbnail' in video and video['thumbnail']:
                            thumbnail_url = video['thumbnail']
                            with urllib.request.urlopen(thumbnail_url) as response:
                                thumbnail_data = response.read()
                                self.message_queue.put(("channel_thumbnail", (i, thumbnail_data)))
                    except Exception as e:
                        print(f"Error fetching thumbnail for video {i}: {e}")
                        
            else:
                raise Exception("No videos found in this channel")
                
        except Exception as e:
            self.message_queue.put(("error", str(e)))
        finally:
            self.message_queue.put(("status", "Ready"))
            self.message_queue.put(("progress", 100))

    def update_channel_info(self, info):
        """Update the channel information display"""
        channel_title = info.get('channel', info.get('uploader', 'Unknown Channel'))
        video_count = info.get('playlist_count', 0)
        
        self.channel_name_label.config(text=f"Channel: {channel_title}")
        self.video_count_label.config(text=f"Videos: {video_count}")

    def update_channel_videos(self, videos):
        """Display the list of videos from the channel"""
        self.channel_videos = videos
        self.video_checkboxes = []
        
        # Create a video entry for each video
        for i, video in enumerate(videos):
            frame = ttk.Frame(self.videos_frame)
            frame.pack(fill="x", pady=5, padx=5)
            self.video_widgets.append(frame)
            
            # Create a thumbnail placeholder
            thumbnail_frame = ttk.LabelFrame(frame, width=120, height=90)
            thumbnail_frame.pack(side="left", padx=5)
            thumbnail_frame.pack_propagate(False)
            
            thumbnail_label = ttk.Label(thumbnail_frame, text="Loading...")
            thumbnail_label.pack(fill="both", expand=True)
            self.video_widgets.append(thumbnail_label)
            
            # Create video info
            info_frame = ttk.Frame(frame)
            info_frame.pack(side="left", fill="both", expand=True, padx=5)
            self.video_widgets.append(info_frame)
            
            title = video.get('title', 'Unknown Title')
            uploader = video.get('uploader', 'Unknown Uploader')
            duration = video.get('duration', 0)
            duration_str = self.format_duration(duration)
            
            title_label = ttk.Label(info_frame, text=title, wraplength=600, font=('TkDefaultFont', 10, 'bold'))
            title_label.pack(anchor="w")
            self.video_widgets.append(title_label)
            
            uploader_label = ttk.Label(info_frame, text=f"By: {uploader}")
            uploader_label.pack(anchor="w")
            self.video_widgets.append(uploader_label)
            
            duration_label = ttk.Label(info_frame, text=f"Duration: {duration_str}")
            duration_label.pack(anchor="w")
            self.video_widgets.append(duration_label)
            
            # Checkbox for selection
            var = tk.BooleanVar(value=False)
            self.video_checkboxes.append(var)
            
            checkbox = ttk.Checkbutton(frame, variable=var, text="Select", 
                                      command=lambda idx=i: self.toggle_video_selection(idx))
            checkbox.pack(side="right", padx=10)
            self.video_widgets.append(checkbox)
        
        # Update UI state
        self.fetch_button.config(state="normal")
        self.channel_fetch_button.config(state="normal")
        self.download_button.config(state="normal")
        self.update_status(f"Loaded {len(videos)} videos from channel")

    def update_video_thumbnail(self, data):
        """Update a video's thumbnail with the downloaded image"""
        index, thumbnail_data = data
        try:
            # Each video has multiple widgets, find the thumbnail label
            widget_index = index * 7 + 1  # Adjust based on how many widgets per video
            
            if widget_index < len(self.video_widgets):
                thumbnail_label = self.video_widgets[widget_index]
                image = Image.open(BytesIO(thumbnail_data))
                image = image.resize((120, 90), Image.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                
                # Keep a reference to prevent garbage collection
                thumbnail_label.image = photo
                thumbnail_label.config(image=photo, text="")
        except Exception as e:
            print(f"Error updating thumbnail for video {index}: {e}")

    def toggle_video_selection(self, index):
        """Handle toggling a video's selection state"""
        is_selected = self.video_checkboxes[index].get()
        
        if is_selected and index not in self.selected_videos:
            self.selected_videos.append(index)
        elif not is_selected and index in self.selected_videos:
            self.selected_videos.remove(index)

    def clear_channel_videos(self):
        """Remove all video widgets from the channel display"""
        for widget in self.video_widgets:
            widget.destroy()
        self.video_widgets = []
        
        # Reset the canvas scroll region
        self.videos_canvas.configure(scrollregion=(0, 0, 0, 0))

    def on_frame_configure(self, event):
        """Update the scroll region when the videos frame changes size"""
        self.videos_canvas.configure(scrollregion=self.videos_canvas.bbox("all"))

    def format_duration(self, seconds):
        """Format seconds into a readable duration string"""
        if not seconds:
            return "Unknown duration"
            
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"

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
            self.fetch_button.config(state="normal")
            self.channel_fetch_button.config(state="normal")
            
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

    def start_download(self):
        mode = self.mode_var.get()
        if mode == "simple":
            self.start_simple_download()
        elif mode == "advanced":
            self.start_advanced_download()
        elif mode == "channel":
            self.start_channel_download()
            
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
        self.channel_fetch_button.config(state="disabled")

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
        self.channel_fetch_button.config(state="disabled")
        
        # Start download thread
        thread = threading.Thread(target=self.download_components_thread, 
                                  args=(url, download_tasks, save_dir))
        thread.daemon = True
        thread.start()
        
    def start_channel_download(self):
        if not self.selected_videos:
            messagebox.showwarning("Warning", "Please select at least one video to download.")
            return
        
        # Ask for directory to save files
        save_dir = filedialog.askdirectory(title="Select directory to save videos")
        if not save_dir:
            self.update_status("Download cancelled.")
            return
        
        # Get the selected format
        format_selector = self.format_var.get()
        
        # Prepare the download tasks - a list of video URLs
        download_tasks = []
        for index in self.selected_videos:
            if index < len(self.channel_videos):
                video = self.channel_videos[index]
                video_url = video.get('url') or video.get('webpage_url')
                if video_url:
                    download_tasks.append(video_url)
        
        if not download_tasks:
            messagebox.showwarning("Warning", "Could not get URLs for selected videos.")
            return
            
        # Disable UI during download
        self.progress['value'] = 0
        self.download_button.config(state="disabled")
        self.fetch_button.config(state="disabled")
        self.channel_fetch_button.config(state="disabled")
        
        # Start download thread
        thread = threading.Thread(target=self.download_channel_videos_thread, 
                                  args=(download_tasks, format_selector, save_dir))
        thread.daemon = True
        thread.start()
        
    def download_channel_videos_thread(self, video_urls, format_selector, save_dir):
        try:
            total_videos = len(video_urls)
            completed_videos = 0
            
            for i, url in enumerate(video_urls):
                self.message_queue.put(("status", f"Downloading video {i+1} of {total_videos}: {url}"))
                self.message_queue.put(("progress", (i / total_videos) * 100))
                
                # Build command for this video
                command = [
                    "yt-dlp.exe",
                    "-f", format_selector,
                    "-o", f"{save_dir}/%(title)s.%(ext)s",
                    "--progress",
                    url
                ]
                
                if self.thumbnail_var.get():
                    command.append("--write-thumbnail")
                    
                if self.subtitle_var.get():
                    command.append("--write-subs")
                    command.append("--write-auto-subs")
                
                # Execute download command
                process = subprocess.Popen(
                    command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, bufsize=1, universal_newlines=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                # Monitor process
                for line in process.stdout:
                    self.message_queue.put(("status", line.strip()))
                    match = re.search(r"\[download\]\s+([0-9.]+)%", line)
                    if match:
                        percentage = float(match.group(1))
                        video_progress = (i + percentage / 100) / total_videos * 100
                        self.message_queue.put(("progress", video_progress))
                
                process.wait()
                if process.returncode != 0:
                    stderr = process.stderr.read()
                    self.message_queue.put(("status", f"Error downloading video {i+1}: {stderr}"))
                else:
                    completed_videos += 1
                
            # Final status update
            if completed_videos == total_videos:
                self.message_queue.put(("done",))
            else:
                self.message_queue.put(("status", f"Completed {completed_videos} of {total_videos} videos"))
                
        except Exception as e:
            self.message_queue.put(("error", str(e)))
        finally:
            self.message_queue.put(("progress", 100))
            self.download_button.config(state="normal")
            self.fetch_button.config(state="normal")
            self.channel_fetch_button.config(state="normal")
        
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
        self.channel_fetch_button.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = YTDLP_GUI(root)
    root.mainloop()