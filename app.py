import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import threading
import time
import os

class TikTokDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TikTok Live Downloader Pro - Đa luồng")
        self.root.geometry("750x450")
        self.root.configure(padx=15, pady=15)
        
        # Thiết lập giao diện hiện đại (Đã sửa lỗi biến self.style)
        self.style = ttk.Style()
        if 'clam' in self.style.theme_names():
            self.style.theme_use('clam')
        self.style.configure("Treeview.Heading", font=('Segoe UI', 10, 'bold'), background="#f0f0f0")
        self.style.configure("Treeview", font=('Segoe UI', 9), rowheight=30)
        
        # Biến lưu trữ
        self.save_folder = tk.StringVar(value=os.getcwd())
        self.task_counter = 0
        
        self.create_widgets()
        
    def create_widgets(self):
        # 1. Khu vực chọn thư mục
        frame_folder = ttk.Frame(self.root)
        frame_folder.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(frame_folder, text="Thư mục lưu:", font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT)
        ttk.Entry(frame_folder, textvariable=self.save_folder, state='readonly').pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        ttk.Button(frame_folder, text="📁 Chọn thư mục", command=self.choose_folder).pack(side=tk.LEFT)
        
        # 2. Khu vực nhập link
        frame_link = ttk.Frame(self.root)
        frame_link.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(frame_link, text="Link TikTok Live:", font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT)
        self.url_entry = ttk.Entry(frame_link)
        self.url_entry.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        # Nút bấm nhấn mạnh
        self.style.configure("Accent.TButton", font=('Segoe UI', 9, 'bold'), foreground="blue")
        ttk.Button(frame_link, text="➕ Thêm tiến trình tải (5 Phút)", style="Accent.TButton", command=self.start_download).pack(side=tk.LEFT)
        
        # 3. Bảng quản lý tiến trình (Treeview)
        columns = ("id", "url", "status", "time")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=10)
        
        self.tree.heading("id", text="STT")
        self.tree.heading("url", text="Đường link Live")
        self.tree.heading("status", text="Trạng thái")
        self.tree.heading("time", text="Thời gian")
        
        self.tree.column("id", width=40, anchor=tk.CENTER)
        self.tree.column("url", width=380, anchor=tk.W)
        self.tree.column("status", width=140, anchor=tk.CENTER)
        self.tree.column("time", width=80, anchor=tk.CENTER)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Thanh cuộn cho bảng
        scrollbar = ttk.Scrollbar(self.tree, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def choose_folder(self):
        folder = filedialog.askdirectory(title="Chọn thư mục lưu video")
        if folder:
            self.save_folder.set(folder)

    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng dán link TikTok Live vào ô trống!")
            return
            
        self.task_counter += 1
        item_id = self.tree.insert("", tk.END, values=(self.task_counter, url, "Đang kết nối...", "05:00"))
        self.url_entry.delete(0, tk.END) 
        
        folder = self.save_folder.get()
        threading.Thread(target=self.process_download, args=(item_id, url, folder), daemon=True).start()

    def process_download(self, item_id, url, folder):
        try:
            cmd = ["yt-dlp", "-o", "TiktokLive_%(id)s_%(autonumber)s.%(ext)s", url]
            process = subprocess.Popen(cmd, cwd=folder, creationflags=subprocess.CREATE_NO_WINDOW)
            
            total_seconds = 300 # 5 Phút
            
            while total_seconds > 0:
                if process.poll() is not None:
                    break
                    
                mins, secs = divmod(total_seconds, 60)
                time_str = f"{mins:02d}:{secs:02d}"
                
                current_values = self.tree.item(item_id, 'values')
                self.root.after(0, self.tree.item, item_id, {"values": (current_values[0], url, "🔴 Đang ghi hình", time_str)})
                
                time.sleep(1)
                total_seconds -= 1
                
            try:
                process.terminate() 
            except:
                pass
                
            current_values = self.tree.item(item_id, 'values')
            if total_seconds > 0:
                 self.root.after(0, self.tree.item, item_id, {"values": (current_values[0], url, "Live đã tắt sớm", "00:00")})
            else:
                 self.root.after(0, self.tree.item, item_id, {"values": (current_values[0], url, "✅ Đã lưu video", "00:00")})
                 
        except Exception as e:
            current_values = self.tree.item(item_id, 'values')
            self.root.after(0, self.tree.item, item_id, {"values": (current_values[0], url, "❌ Lỗi mạng/yt-dlp", "00:00")})

if __name__ == "__main__":
    root = tk.Tk()
    app = TikTokDownloaderApp(root)
    root.mainloop()
