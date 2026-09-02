import tkinter as tk
from tkinter import messagebox
import subprocess
import threading
import time

def start_download():
    url = url_entry.get().strip()
    if not url:
        messagebox.showwarning("Lỗi", "Vui lòng dán link TikTok Live!")
        return

    # Khóa nút bấm và cập nhật trạng thái
    btn_download.config(state=tk.DISABLED)
    status_label.config(text="Trạng thái: Đang tải... (sẽ tự ngắt sau 5 phút)", fg="blue")
    
    # Chạy luồng riêng để không làm đơ giao diện
    threading.Thread(target=process_download, args=(url,), daemon=True).start()

def process_download(url):
    try:
        # Gọi lệnh yt-dlp
        cmd = ["yt-dlp", "-o", "Tiktok_Live_%(id)s.%(ext)s", url]
        process = subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW)
        
        # Đợi đúng 5 phút (300 giây)
        time.sleep(300)
        
        # Ngắt quá trình tải
        process.terminate()
        
        # Cập nhật giao diện khi hoàn thành
        status_label.config(text="Trạng thái: Đã tải xong 5 phút!", fg="green")
    except Exception as e:
        status_label.config(text=f"Lỗi: {str(e)}", fg="red")
    finally:
        btn_download.config(state=tk.NORMAL)

# Thiết lập giao diện người dùng
root = tk.Tk()
root.title("TikTok Live Downloader - 5 Phút")
root.geometry("400x150")

tk.Label(root, text="Dán link TikTok Live vào đây:").pack(pady=5)
url_entry = tk.Entry(root, width=50)
url_entry.pack(pady=5)

btn_download = tk.Button(root, text="Tải Live", command=start_download)
btn_download.pack(pady=5)

status_label = tk.Label(root, text="Trạng thái: Chờ tải...", fg="black")
status_label.pack(pady=5)

root.mainloop()
