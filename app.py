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
        ttk.Label(frame_link, text="Link TikTok Live:", font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT)
        self.url_entry = ttk.Entry(frame_link)
        self.url_entry.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        self.style.configure("Accent.TButton", font=('Segoe UI', 9, 'bold'), foreground="blue")
        ttk.Button(frame_link, text="➕ Thêm tiến trình tải (5 Phút)", style="Accent.TButton", command=self.start_download).pack(side=tk.LEFT)
        
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
        
        scrollbar = ttk.Scrollbar(self.tree, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def choose_folder(self):
        folder = filedialog.askdirectory(title="Chọn thư mục lưu video")
        if folder:
            self.save_folder.set(folder)

    # Hàm hỗ trợ cập nhật giao diện an toàn không bị treo
    def safe_update(self, item_id, url, status, time_str):
        try:
            current = self.tree.item(item_id, 'values')
            self.tree.item(item_id, values=(current[0], url, status, time_str))
        except:
            pass

    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng dán link TikTok Live vào ô trống!")
            return
            
        self.task_counter += 1
        item_id = self.tree.insert("", tk.END, values=(self.task_counter, url, "Đang khởi tạo...", "05:00"))
        self.url_entry.delete(0, tk.END) 
        
        folder = self.save_folder.get()
        threading.Thread(target=self.process_download, args=(item_id, url, folder), daemon=True).start()

    def process_download(self, item_id, url, folder):
        try:
            # Gắn trực tiếp thư mục vào tên file xuất ra để app không bị mất dấu yt-dlp.exe
            output_template = os.path.join(folder, "TiktokLive_%(id)s_%(autonumber)s.%(ext)s")
            cmd = ["yt-dlp", "-o", output_template, url]
            
            process = subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW)
            total_seconds = 300 
            
            while total_seconds > 0:
                if process.poll() is not None:
                    break
                    
                mins, secs = divmod(total_seconds, 60)
                time_str = f"{mins:02d}:{secs:02d}"
                
                # Gọi hàm an toàn để đẩy dữ liệu lên giao diện
                self.root.after(0, self.safe_update, item_id, url, "🔴 Đang ghi hình", time_str)
                
                time.sleep(1)
                total_seconds -= 1
                
            try:
                # Dùng taskkill để diệt tận gốc tiến trình cha và toàn bộ tiến trình con (ffmpeg)
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(process.pid)], creationflags=subprocess.CREATE_NO_WINDOW)
                time.sleep(2) # Chờ 2 giây để Windows nhả file hoàn toàn
                
                # Tự động quét và xóa đuôi .part
                for filename in os.listdir(folder):
                    if filename.endswith(".part") and "TiktokLive" in filename:
                        old_path = os.path.join(folder, filename)
                        new_path = old_path.replace(".part", "")
                        os.rename(old_path, new_path)
            except:
                pass
                
            if total_seconds > 0:
                 self.root.after(0, self.safe_update, item_id, url, "Live đã tắt sớm / Bị lỗi", "00:00")
            else:
                 self.root.after(0, self.safe_update, item_id, url, "✅ Đã lưu video", "00:00")
                 
        except Exception as e:
            self.root.after(0, self.safe_update, item_id, url, "❌ Lỗi: Thiếu file yt-dlp.exe", "00:00")

if __name__ == "__main__":
    root = tk.Tk()
    app = TikTokDownloaderApp(root)
    root.mainloop()
