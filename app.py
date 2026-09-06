import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import threading
import time
import os
import sys
import re
import asyncio

# Thư viện chuyên kết nối Webcast TikTok
from TikTokLive import TikTokLiveClient

class TikTokDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TikTok Live Downloader Pro - Auto Stream Grabber")
        self.root.geometry("780x460")
        self.root.configure(padx=15, pady=15)
        
        self.style = ttk.Style()
        if 'clam' in self.style.theme_names():
            self.style.theme_use('clam')
        self.style.configure("Treeview.Heading", font=('Segoe UI', 10, 'bold'), background="#f0f0f0")
        self.style.configure("Treeview", font=('Segoe UI', 9), rowheight=30)
        
        self.save_folder = tk.StringVar(value=os.getcwd())
        self.task_counter = 0
        
        self.create_widgets()
        
    def create_widgets(self):
        frame_folder = ttk.Frame(self.root)
        frame_folder.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(frame_folder, text="Thư mục lưu:", font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT)
        ttk.Entry(frame_folder, textvariable=self.save_folder, state='readonly').pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        ttk.Button(frame_folder, text="📁 Chọn thư mục", command=self.choose_folder).pack(side=tk.LEFT)
        
        frame_link = ttk.Frame(self.root)
        frame_link.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(frame_link, text="Link / ID Live:", font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT)
        self.url_entry = ttk.Entry(frame_link)
        self.url_entry.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        self.style.configure("Accent.TButton", font=('Segoe UI', 9, 'bold'), foreground="blue")
        ttk.Button(frame_link, text="➕ Bắt đầu tải (5 Phút)", style="Accent.TButton", command=self.start_download).pack(side=tk.LEFT)
        
        columns = ("id", "url", "status", "time")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=10)
        
        self.tree.heading("id", text="STT")
        self.tree.heading("url", text="Tài khoản / URL")
        self.tree.heading("status", text="Trạng thái")
        self.tree.heading("time", text="Thời gian")
        
        self.tree.column("id", width=40, anchor=tk.CENTER)
        self.tree.column("url", width=400, anchor=tk.W)
        self.tree.column("status", width=180, anchor=tk.CENTER)
        self.tree.column("time", width=80, anchor=tk.CENTER)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(self.tree, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def choose_folder(self):
        folder = filedialog.askdirectory(title="Chọn thư mục lưu video")
        if folder:
            self.save_folder.set(folder)

    def safe_update(self, item_id, url, status, time_str):
        try:
            current = self.tree.item(item_id, 'values')
            self.tree.item(item_id, values=(current[0], url, status, time_str))
        except Exception:
            pass

    def extract_username(self, raw_input):
        raw_input = raw_input.strip()
        match = re.search(r"@([a-zA-Z0-9_.-]+)", raw_input)
        if match:
            return match.group(1)
        return raw_input.replace("https://", "").replace("http://", "").split("/")[0]

    def get_live_stream_url(self, unique_id):
        client = TikTokLiveClient(unique_id=unique_id)
        
        async def fetch():
            room_info = await client.web.fetch_room_info()
            if not room_info or not client.room_id:
                return None
            stream_data = room_info.get("stream_url", {})
            # Ưu tiên lấy luồng flv pull url hoặc hls_pull_url
            flv_pull_url = stream_data.get("flv_pull_url", {})
            if flv_pull_url:
                return list(flv_pull_url.values())[0]
            return stream_data.get("hls_pull_url")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(fetch())
        except Exception:
            return None
        finally:
            loop.close()

    def start_download(self):
        raw_input = self.url_entry.get().strip()
        if not raw_input:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập link hoặc username TikTok Live!")
            return
            
        self.task_counter += 1
        username = self.extract_username(raw_input)
        item_id = self.tree.insert("", tk.END, values=(self.task_counter, f"@{username}", "Đang dò luồng Live...", "05:00"))
        self.url_entry.delete(0, tk.END) 
        
        folder = self.save_folder.get()
        threading.Thread(target=self.process_download, args=(item_id, username, folder), daemon=True).start()

    def process_download(self, item_id, username, folder):
        process = None
        try:
            self.root.after(0, self.safe_update, item_id, f"@{username}", "Kết nối Webcast...", "05:00")
            stream_url = self.get_live_stream_url(username)

            if not stream_url:
                self.root.after(0, self.safe_update, item_id, f"@{username}", "❌ Không tìm thấy Live/Offline", "00:00")
                return

            timestamp = int(time.time())
            output_file = os.path.join(folder, f"Tiktok_{username}_{timestamp}.mp4")

            # Dùng ffmpeg hoặc yt-dlp để thu luồng trực tiếp không cần bypass web
            cmd = [
                "ffmpeg",
                "-y",
                "-i", stream_url,
                "-t", "300",
                "-c", "copy",
                output_file
            ]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            total_seconds = 300

            while total_seconds > 0:
                if process.poll() is not None:
                    break

                mins, secs = divmod(total_seconds, 60)
                time_str = f"{mins:02d}:{secs:02d}"
                self.root.after(0, self.safe_update, item_id, f"@{username}", "🔴 Đang ghi hình", time_str)
                time.sleep(1)
                total_seconds -= 1

            if process.poll() is None:
                try:
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(process.pid)], creationflags=subprocess.CREATE_NO_WINDOW)
                except Exception:
                    pass

            if os.path.exists(output_file) and os.path.getsize(output_file) > 1024:
                self.root.after(0, self.safe_update, item_id, f"@{username}", "✅ Đã lưu video", "00:00")
            else:
                self.root.after(0, self.safe_update, item_id, f"@{username}", "❌ Ghi hình thất bại", "00:00")

        except Exception as e:
            self.root.after(0, self.safe_update, item_id, f"@{username}", f"❌ Lỗi: {str(e)[:25]}", "00:00")

if __name__ == "__main__":
    root = tk.Tk()
    app = TikTokDownloaderApp(root)
    root.mainloop()
