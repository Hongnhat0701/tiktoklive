```python
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import threading
import time
import os
import sys


class TikTokDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TikTok Live Downloader Pro - Đa luồng")
        self.root.geometry("750x450")
        self.root.configure(padx=15, pady=15)

        self.style = ttk.Style()

        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")

        self.style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 10, "bold"),
            background="#f0f0f0"
        )

        self.style.configure(
            "Treeview",
            font=("Segoe UI", 9),
            rowheight=30
        )

        # Thư mục mặc định
        if getattr(sys, "frozen", False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        self.base_dir = base_dir

        self.save_folder = tk.StringVar(value=base_dir)
        self.task_counter = 0

        self.create_widgets()

    # =========================================================
    # GIAO DIỆN
    # =========================================================

    def create_widgets(self):

        # Thư mục lưu
        frame_folder = ttk.Frame(self.root)
        frame_folder.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(
            frame_folder,
            text="Thư mục lưu:",
            font=("Segoe UI", 9, "bold")
        ).pack(side=tk.LEFT)

        ttk.Entry(
            frame_folder,
            textvariable=self.save_folder,
            state="readonly"
        ).pack(
            side=tk.LEFT,
            padx=10,
            fill=tk.X,
            expand=True
        )

        ttk.Button(
            frame_folder,
            text="📁 Chọn thư mục",
            command=self.choose_folder
        ).pack(side=tk.LEFT)

        # Link
        frame_link = ttk.Frame(self.root)
        frame_link.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(
            frame_link,
            text="Link TikTok Live:",
            font=("Segoe UI", 9, "bold")
        ).pack(side=tk.LEFT)

        self.url_entry = ttk.Entry(frame_link)

        self.url_entry.pack(
            side=tk.LEFT,
            padx=10,
            fill=tk.X,
            expand=True
        )

        self.style.configure(
            "Accent.TButton",
            font=("Segoe UI", 9, "bold"),
            foreground="blue"
        )

        ttk.Button(
            frame_link,
            text="➕ Thêm tiến trình tải (5 Phút)",
            style="Accent.TButton",
            command=self.start_download
        ).pack(side=tk.LEFT)

        # Danh sách tiến trình
        columns = ("id", "url", "status", "time")

        self.tree = ttk.Treeview(
            self.root,
            columns=columns,
            show="headings",
            height=10
        )

        self.tree.heading("id", text="STT")
        self.tree.heading("url", text="Đường link Live")
        self.tree.heading("status", text="Trạng thái")
        self.tree.heading("time", text="Thời gian")

        self.tree.column(
            "id",
            width=40,
            anchor=tk.CENTER
        )

        self.tree.column(
            "url",
            width=370,
            anchor=tk.W
        )

        self.tree.column(
            "status",
            width=180,
            anchor=tk.CENTER
        )

        self.tree.column(
            "time",
            width=80,
            anchor=tk.CENTER
        )

        self.tree.pack(
            fill=tk.BOTH,
            expand=True
        )

        scrollbar = ttk.Scrollbar(
            self.tree,
            orient=tk.VERTICAL,
            command=self.tree.yview
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set
        )

        scrollbar.pack(
            side=tk.RIGHT,
            fill=tk.Y
        )

    # =========================================================
    # CHỌN THƯ MỤC
    # =========================================================

    def choose_folder(self):

        folder = filedialog.askdirectory(
            title="Chọn thư mục lưu video"
        )

        if folder:
            self.save_folder.set(folder)

    # =========================================================
    # UPDATE GIAO DIỆN AN TOÀN
    # =========================================================

    def safe_update(
        self,
        item_id,
        url,
        status,
        time_str
    ):

        try:
            current = self.tree.item(
                item_id,
                "values"
            )

            if not current:
                return

            self.tree.item(
                item_id,
                values=(
                    current[0],
                    url,
                    status,
                    time_str
                )
            )

        except Exception:
            pass

    # =========================================================
    # THÊM DOWNLOAD
    # =========================================================

    def start_download(self):

        url = self.url_entry.get().strip()

        if not url:

            messagebox.showwarning(
                "Thiếu thông tin",
                "Vui lòng dán link TikTok Live vào ô trống!"
            )

            return

        self.task_counter += 1

        # STT thật
        task_number = self.task_counter

        item_id = self.tree.insert(
            "",
            tk.END,
            values=(
                task_number,
                url,
                "Đang khởi tạo...",
                "05:00"
            )
        )

        self.url_entry.delete(
            0,
            tk.END
        )

        folder = self.save_folder.get()

        thread = threading.Thread(
            target=self.process_download,
            args=(
                item_id,
                task_number,
                url,
                folder
            ),
            daemon=True
        )

        thread.start()

    # =========================================================
    # XÁC ĐỊNH THƯ MỤC APP
    # =========================================================

    def get_base_dir(self):

        if getattr(sys, "frozen", False):

            return os.path.dirname(
                os.path.abspath(
                    sys.executable
                )
            )

        return os.path.dirname(
            os.path.abspath(__file__)
        )

    # =========================================================
    # TÌM YT-DLP
    # =========================================================

    def get_ytdlp_command(self):

        base_dir = self.get_base_dir()

        # Ưu tiên yt-dlp.exe nằm cạnh app.exe
        local_ytdlp = os.path.join(
            base_dir,
            "yt-dlp.exe"
        )

        if os.path.isfile(local_ytdlp):

            return local_ytdlp

        # Nếu không có thì dùng yt-dlp trong PATH
        return "yt-dlp"

    # =========================================================
    # ĐỌC OUTPUT CỦA YT-DLP
    # =========================================================

    def read_process_output(
        self,
        process,
        output_lines
    ):

        try:

            for line in iter(
                process.stdout.readline,
                ""
            ):

                if not line:
                    break

                line = line.strip()

                if line:
                    output_lines.append(line)

        except Exception as e:

            output_lines.append(
                f"Reader error: {e}"
            )

        finally:

            try:
                process.stdout.close()
            except Exception:
                pass

    # =========================================================
    # PHÂN TÍCH LỖI
    # =========================================================

    def classify_error(
        self,
        output_lines
    ):

        if not output_lines:
            return "❌ yt-dlp đã dừng"

        full_text = "\n".join(
            output_lines
        )

        text = full_text.lower()

        # Đăng nhập / cookies
        if any(
            key in text
            for key in [
                "sign in",
                "login",
                "cookie",
                "authentication",
                "authenticate"
            ]
        ):

            return "❌ Lỗi đăng nhập/Cookies"

        # Không Live
        if any(
            key in text
            for key in [
                "not currently live",
                "not live",
                "offline",
                "is not live"
            ]
        ):

            return "❌ Kênh không phát Live"

        # Khu vực
        if any(
            key in text
            for key in [
                "geo",
                "region",
                "country",
                "not available in your country"
            ]
        ):

            return "❌ Bị giới hạn khu vực"

        # Private
        if any(
            key in text
            for key in [
                "private",
                "followers-only"
            ]
        ):

            return "❌ Live riêng tư"

        # HTTP / tải
        if any(
            key in text
            for key in [
                "http error",
                "unable to download",
                "download error",
                "connection error",
                "network error",
                "timed out",
                "timeout"
            ]
        ):

            return "❌ Lỗi kết nối/Tải"

        # Tìm dòng ERROR
        error_lines = [
            line
            for line in output_lines
            if "error" in line.lower()
        ]

        if error_lines:

            error = error_lines[-1]

        else:

            error = output_lines[-1]

        # Loại bỏ tiền tố ERROR:
        error = error.replace(
            "ERROR:",
            ""
        ).strip()

        if len(error) > 50:

            error = error[:50] + "..."

        return f"❌ {error}"

    # =========================================================
    # DOWNLOAD
    # =========================================================

    def process_download(
        self,
        item_id,
        task_number,
        url,
        folder
    ):

        process = None
        output_lines = []

        try:

            # -------------------------------------------------
            # THƯ MỤC APP
            # -------------------------------------------------

            base_dir = self.get_base_dir()

            # -------------------------------------------------
            # COOKIES
            # -------------------------------------------------

            cookie_path = os.path.join(
                base_dir,
                "cookies.txt"
            )

            if not os.path.isfile(
                cookie_path
            ):

                self.root.after(
                    0,
                    self.safe_update,
                    item_id,
                    url,
                    "❌ Thiếu cookies.txt",
                    "00:00"
                )

                return

            # -------------------------------------------------
            # FILE OUTPUT
            # -------------------------------------------------

            output_template = os.path.join(
                folder,
                f"TiktokLive_STT{task_number}_%(id)s.%(ext)s"
            )

            # -------------------------------------------------
            # YT-DLP
            # -------------------------------------------------

            ytdlp = self.get_ytdlp_command()

            # -------------------------------------------------
            # COMMAND
            # -------------------------------------------------

            cmd = [
                ytdlp,

                "--no-part",

                "--cookies",
                cookie_path,

                "-o",
                output_template,

                url
            ]

            # -------------------------------------------------
            # CHẠY YT-DLP
            # -------------------------------------------------

            process = subprocess.Popen(
                cmd,

                stdout=subprocess.PIPE,

                stderr=subprocess.STDOUT,

                text=True,

                encoding="utf-8",

                errors="replace",

                creationflags=subprocess.CREATE_NO_WINDOW
            )

            # -------------------------------------------------
            # THREAD ĐỌC LOG
            # -------------------------------------------------

            reader_thread = threading.Thread(
                target=self.read_process_output,
                args=(
                    process,
                    output_lines
                ),
                daemon=True
            )

            reader_thread.start()

            # -------------------------------------------------
            # TIMER 5 PHÚT
            # -------------------------------------------------

            total_seconds = 300

            while total_seconds > 0:

                # yt-dlp tự dừng
                if process.poll() is not None:

                    reader_thread.join(
                        timeout=2
                    )

                    status_text = self.classify_error(
                        output_lines
                    )

                    # In log ra console nếu chạy Python
                    print("\n========== YT-DLP ==========")

                    for line in output_lines:
                        print(line)

                    print(
                        "RETURN CODE:",
                        process.returncode
                    )

                    print(
                        "============================\n"
                    )

                    self.root.after(
                        0,
                        self.safe_update,
                        item_id,
                        url,
                        status_text,
                        "00:00"
                    )

                    return

                # Timer
                mins, secs = divmod(
                    total_seconds,
                    60
                )

                time_str = (
                    f"{mins:02d}:{secs:02d}"
                )

                self.root.after(
                    0,
                    self.safe_update,
                    item_id,
                    url,
                    "🔴 Đang ghi hình",
                    time_str
                )

                time.sleep(1)

                total_seconds -= 1

            # -------------------------------------------------
            # ĐỦ 5 PHÚT
            # -------------------------------------------------

            if process.poll() is None:

                try:

                    subprocess.run(
                        [
                            "taskkill",
                            "/F",
                            "/T",
                            "/PID",
                            str(process.pid)
                        ],

                        creationflags=subprocess.CREATE_NO_WINDOW,

                        stdout=subprocess.DEVNULL,

                        stderr=subprocess.DEVNULL,

                        timeout=10
                    )

                except Exception:
                    pass

            # -------------------------------------------------
            # CHỜ PROCESS KẾT THÚC
            # -------------------------------------------------

            try:

                process.wait(
                    timeout=10
                )

            except Exception:
                pass

            reader_thread.join(
                timeout=3
            )

            # -------------------------------------------------
            # KIỂM TRA FILE VIDEO
            # -------------------------------------------------

            try:

                files = os.listdir(
                    folder
                )

                prefix = (
                    f"TiktokLive_STT{task_number}_"
                )

                video_files = [
                    f
                    for f in files
                    if f.startswith(prefix)
                    and os.path.isfile(
                        os.path.join(
                            folder,
                            f
                        )
                    )
                    and os.path.getsize(
                        os.path.join(
                            folder,
                            f
                        )
                    ) > 0
                ]

            except Exception:

                video_files = []

            # -------------------------------------------------
            # CÓ VIDEO
            # -------------------------------------------------

            if video_files:

                self.root.after(
                    0,
                    self.safe_update,
                    item_id,
                    url,
                    "✅ Đã lưu video",
                    "00:00"
                )

            # -------------------------------------------------
            # KHÔNG CÓ VIDEO
            # -------------------------------------------------

            else:

                status_text = self.classify_error(
                    output_lines
                )

                if status_text == "❌ yt-dlp đã dừng":

                    status_text = (
                        "❌ Không tạo được video"
                    )

                self.root.after(
                    0,
                    self.safe_update,
                    item_id,
                    url,
                    status_text,
                    "00:00"
                )

                # In log
                print("\n========== YT-DLP ==========")

                for line in output_lines:
                    print(line)

                print(
                    "RETURN CODE:",
                    process.returncode
                )

                print(
                    "============================\n"
                )

        # =====================================================
        # KHÔNG TÌM THẤY YT-DLP
        # =====================================================

        except FileNotFoundError:

            self.root.after(
                0,
                self.safe_update,
                item_id,
                url,
                "❌ Không tìm thấy yt-dlp",
                "00:00"
            )

        # =====================================================
        # LỖI KHÁC
        # =====================================================

        except Exception as e:

            print(
                "APP ERROR:",
                repr(e)
            )

            self.root.after(
                0,
                self.safe_update,
                item_id,
                url,
                f"❌ Lỗi: {str(e)[:35]}",
                "00:00"
            )

        finally:

            # Đảm bảo process không còn chạy
            if process is not None:

                try:

                    if process.poll() is None:

                        subprocess.run(
                            [
                                "taskkill",
                                "/F",
                                "/T",
                                "/PID",
                                str(process.pid)
                            ],

                            creationflags=subprocess.CREATE_NO_WINDOW,

                            stdout=subprocess.DEVNULL,

                            stderr=subprocess.DEVNULL
                        )

                except Exception:
                    pass


# =============================================================
# MAIN
# =============================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = TikTokDownloaderApp(
        root
    )

    root.mainloop()
```
