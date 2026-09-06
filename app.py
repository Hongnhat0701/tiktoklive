import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import threading
import time
import os
import sys

class TikTokFinalRecorder:
    def __init__(self, root):
        self.root = root
        self.root.title("TikTok Live 5-Min Auto Recorder (Final)")
        self.root.geometry("780x430")
        self.root.configure(padx=15, pady=15)
        
        # Mặc định lưu ra ngoài Desktop cho dễ tìm
        default_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        self.save_folder = tk.StringVar(value=default_dir)
        self.counter = 0
        
        self.build_ui()
        
    def build_ui(self):
        # 1. Chọn thư mục lưu
        f_folder = ttk.Frame(self.root)
        f_folder.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(f_folder, text="Thư mục lưu:", font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT)
        ttk.Entry(f_folder, textvariable=self.save_folder, state='readonly').pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        ttk.Button(f_folder, text="📁 Chọn thư mục", command=self.choose_folder).pack(side=tk.LEFT)
        
        # 2. Nhập link stream
        f_input = ttk.Frame(self.root)
        f_input.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(f_input, text="Link Stream:", font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT)
        self.entry_url = ttk.Entry(f_input)
        self.entry_url.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        btn_start = ttk.Button(f_input, text="➕ Bắt đầu ghi 5 Phút", command=self.start_download)
        btn_start.pack(side=tk.LEFT)
        
        # 3. Bảng tiến trình
        cols = ("id", "url", "status", "time")
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings", height=9)
        self.tree.heading("id", text="STT")
        self.tree.heading("url", text="Luồng tải")
        self.tree.heading("status", text="Trạng thái")
        self.tree.heading("time", text="Thời gian")
        
        self.tree.column("id", width=45, anchor=tk.CENTER)
        self.tree.column("url", width=380, anchor=tk.W)
        self.tree.column("status", width=200, anchor=tk.CENTER)
        self.tree.column("time", width=85, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True)

    def choose_folder(self):
        d = filedialog.askdirectory()
        if d:
            self.save_folder.set(d)

    def ui_update(self, item_id, title, status, time_str):
        # Đảm bảo cập nhật giao diện an toàn 100% trong luồng chính
        try:
            self.tree.item(item_id, values=(self.tree.item(item_id, 'values')[0], title, status, time_str))
        except Exception:
            pass

    def start_download(self):
        raw_url = self.entry_url.get().strip()
        if not raw_url:
            messagebox.showwarning("Cảnh báo", "Vui lòng dán link stream vào!")
            return
            
        # Kiểm tra nếu dán nhầm link cá nhân tiktok.com/@username
        if "tiktok.com/@" in raw_url and not any(k in raw_url for k in [".flv", ".m3u8", "pull", "stream"]):
            messagebox.showerror("Sai link", "Đây là link profile cá nhân. Bạn hãy lấy Link Stream trực tiếp từ Extension/Network (link có chứa 'pull', 'stream' hoặc '.flv') rồi dán vào đây.")
            return

        self.counter += 1
        title = f"Live_Record_{self.counter}"
        item_id = self.tree.insert("", tk.END, values=(self.counter, title, "Khởi tạo luồng...", "05:00"))
        self.entry_url.delete(0, tk.END)
        
        dest = self.save_folder.get()
        threading.Thread(target=self.worker_record, args=(item_id, title, raw_url, dest), daemon=True).start()

    def worker_record(self, item_id, title, stream_url, folder):
        ts_output = None
        mp4_output = None
        try:
            t_now = int(time.time())
            # Bước 1: Ghi vào file .ts để chống hỏng header tuyệt đối
            ts_output = os.path.join(folder, f"{title}_{t_now}.ts")
            mp4_output = os.path.join(folder, f"{title}_{t_now}.mp4")

            ffmpeg_record_cmd = [
                "ffmpeg",
                "-y",
                "-reconnect", "1",
                "-reconnect_streamed", "1",
                "-reconnect_delay_max", "5",
                "-headers", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\r\nReferer: https://www.tiktok.com/\r\n",
                "-i", stream_url,
                "-t", "300",
                "-c", "copy",
                ts_output
            ]

            proc = subprocess.Popen(
                ffmpeg_record_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            # Đếm lùi 300 giây (5 phút)
            total_time = 300
            while total_time > 0:
                if proc.poll() is not None:
                    break
                m, s = divmod(total_time, 60)
                self.root.after(0, self.ui_update, item_id, title, "🔴 Đang ghi hình", f"{m:02d}:{s:02d}")
                time.sleep(1)
                total_time -= 1

            # Đợi ffmpeg chốt file .ts an toàn
            try:
                proc.wait(timeout=5)
            except Exception:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], creationflags=subprocess.CREATE_NO_WINDOW)

            # Kiểm tra file .ts có dữ liệu không
            if not os.path.exists(ts_output) or os.path.getsize(ts_output) < 10240:
                self.root.after(0, self.ui_update, item_id, title, "❌ Lỗi: Không bắt được hình", "00:00")
                if os.path.exists(ts_output):
                    os.remove(ts_output)
                return

            # Bước 2: Tự động đóng sang .mp4 chuẩn có cờ faststart (đảm bảo VLC mở được 100%)
            self.root.after(0, self.ui_update, item_id, title, "⚙️ Đang xử lý file MP4...", "00:00")
            
            ffmpeg_convert_cmd = [
                "ffmpeg",
                "-y",
                "-i", ts_output,
                "-c", "copy",
                "-movflags", "faststart",
                mp4_output
            ]

            conv_proc = subprocess.run(ffmpeg_convert_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)

            # Dọn dẹp file tạm .ts sau khi đã có MP4 hoàn chỉnh
            if os.path.exists(mp4_output) and os.path.getsize(mp4_output) > 10240:
                if os.path.exists(ts_output):
                    os.remove(ts_output)
                self.root.after(0, self.ui_update, item_id, title, "✅ Đã xong (MP4 chuẩn)", "00:00")
            else:
                # Nếu không chuyển đổi được thì giữ nguyên file .ts để vẫn xem được
                self.root.after(0, self.ui_update, item_id, title, "✅ Đã lưu (.TS)", "00:00")

        except Exception as err:
            self.root.after(0, self.ui_update, item_id, title, f"❌ Lỗi: {str(err)[:18]}", "00:00")

if __name__ == "__main__":
    root = tk.Tk()
    app = TikTokFinalRecorder(root)
    root.mainloop()
