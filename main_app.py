import sys
import os
import requests
import threading
import yt_dlp
import re
from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import QThread, pyqtSignal

# ==========================================
# 0. PYINSTALLER FIX (UI File Path Locator)
# ==========================================
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ==========================================
# 1. THE SMART WORKER (Handles both Direct & YouTube)
# ==========================================
class DownloadWorker(QThread):
    progress_update = pyqtSignal(int)
    status_update = pyqtSignal(str)
    finished = pyqtSignal(str)

    def __init__(self, url, num_parts=4):
        super().__init__()
        self.url = url
        self.num_parts = num_parts
        self.is_paused = False
        self.is_cancelled = False
        self.total_size = 0
        self.downloaded_bytes = 0
        self.file_name = url.split('/')[-1].split('?')[0] or "download.file"

    def clean_ansi(self, text):
        # yt-dlp ke colorful codes ko saaf karne ke liye
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def ytdl_progress_hook(self, d):
        # yt-dlp ki progress ko Qt Table mein bhejne ke liye
        if self.is_cancelled:
            raise Exception("Cancelled by user")
            
        if d['status'] == 'downloading':
            p_raw = d.get('_percent_str', '0%')
            p_clean = self.clean_ansi(p_raw).replace('%', '').strip()
            try:
                p_float = float(p_clean)
                self.progress_update.emit(int(p_float))
                self.status_update.emit("Downloading Video...")
            except ValueError:
                pass

    def run(self):
        try:
            self.status_update.emit("Analyzing Link...")
            
            # Check karna ke link video site ka to nahi
            video_sites = ["youtube", "youtu.be", "facebook", "fb.watch", "instagram", "tiktok", "twitter"]
            is_video = any(site in self.url.lower() for site in video_sites)

            if is_video:
                self.status_update.emit("Extracting Video Data...")
                ydl_opts = {
                    'format': 'best',
                    'progress_hooks': [self.ytdl_progress_hook],
                    'outtmpl': '%(title)s.%(ext)s',
                    'no_color': True,
                    'quiet': True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(self.url, download=True)
                    self.file_name = f"{info['title']}.{info['ext']}"
                
                if not self.is_cancelled:
                    self.finished.emit(self.file_name)
                else:
                    self.status_update.emit("Cancelled")
            
            else:
                # --- DIRECT SEGMENTED DOWNLOAD LOGIC ---
                self.status_update.emit("Getting file size...")
                r = requests.head(self.url)
                self.total_size = int(r.headers.get('content-length', 0))
                
                if self.total_size == 0:
                    self.status_update.emit("File size unknown. Error.")
                    return
                
                self.status_update.emit(f"Starting {self.num_parts} Segments...")
                chunk_size = self.total_size // self.num_parts
                threads = []

                for i in range(self.num_parts):
                    start = i * chunk_size
                    end = (i + 1) * chunk_size - 1 if i < self.num_parts - 1 else self.total_size
                    t = threading.Thread(target=self.download_part, args=(start, end, i))
                    threads.append(t)
                    t.start()

                for t in threads:
                    t.join()

                if self.is_cancelled:
                    self.cleanup()
                    self.status_update.emit("Cancelled and Cleaned.")
                    return

                self.status_update.emit("Merging segments...")
                with open(self.file_name, "wb") as outfile:
                    for i in range(self.num_parts):
                        part_name = f"{self.file_name}.part{i}"
                        with open(part_name, "rb") as infile:
                            outfile.write(infile.read())
                        os.remove(part_name)
                
                self.finished.emit(self.file_name)

        except Exception as e:
            if "Cancelled" in str(e):
                self.status_update.emit("Cancelled")
            else:
                self.status_update.emit(f"Failed: {str(e)}")

    def download_part(self, start, end, part_num):
        headers = {'Range': f'bytes={start}-{end}'}
        part_name = f"{self.file_name}.part{part_num}"
        
        try:
            response = requests.get(self.url, headers=headers, stream=True, timeout=10)
            with open(part_name, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    while self.is_paused:
                        if self.is_cancelled: break
                        QThread.msleep(500)
                    
                    if self.is_cancelled: break
                        
                    if chunk:
                        f.write(chunk)
                        self.downloaded_bytes += len(chunk)
                        if self.total_size > 0:
                            percent = int((self.downloaded_bytes / self.total_size) * 100)
                            self.progress_update.emit(percent)
        except Exception as e:
            pass # Handle silently for now

    def cleanup(self):
        for i in range(self.num_parts):
            part_name = f"{self.file_name}.part{i}"
            if os.path.exists(part_name): os.remove(part_name)


# ==========================================
# 2. THE UI CONTROLLER
# ==========================================
class IndustryIDM(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        # --- PYINSTALLER FIX YAHAN APPLY HUA HAI ---
        ui_file = resource_path('idm_design.ui')
        uic.loadUi(ui_file, self)
        # -------------------------------------------

        self.worker = None

        # Achi practice: Buttons ko pehle se check kar len ke UI mein hain ya nahi
        if hasattr(self, 'btn_start'): self.btn_start.clicked.connect(self.start_download)
        if hasattr(self, 'btn_pause'): self.btn_pause.clicked.connect(self.pause_download)
        if hasattr(self, 'btn_cancel'): self.btn_cancel.clicked.connect(self.cancel_download)

    def start_download(self):
        url = self.url_input.text().strip()
        if not url: return

        row_pos = self.table_queue.rowCount()
        self.table_queue.insertRow(row_pos)
        self.table_queue.setItem(row_pos, 0, QtWidgets.QTableWidgetItem("Analyzing..."))
        self.table_queue.setItem(row_pos, 2, QtWidgets.QTableWidgetItem("Starting..."))

        self.worker = DownloadWorker(url, num_parts=4)
        
        # UI Table ko signals se update karna
        self.worker.progress_update.connect(lambda p: self.table_queue.setItem(row_pos, 3, QtWidgets.QTableWidgetItem(f"{p}%")))
        self.worker.status_update.connect(lambda s: self.table_queue.setItem(row_pos, 2, QtWidgets.QTableWidgetItem(s)))
        
        # Job khatam hone par final update
        def on_finish(filename):
            self.table_queue.setItem(row_pos, 0, QtWidgets.QTableWidgetItem(filename))
            self.table_queue.setItem(row_pos, 2, QtWidgets.QTableWidgetItem("Completed!"))
            QtWidgets.QMessageBox.information(self, "Success", f"File saved: {filename}")
            
        self.worker.finished.connect(on_finish)
        self.worker.start()

    def pause_download(self):
        if self.worker:
            self.worker.is_paused = not self.worker.is_paused
            self.btn_pause.setText("Resume" if self.worker.is_paused else "Pause")

    def cancel_download(self):
        if self.worker:
            self.worker.is_cancelled = True
            self.worker.is_paused = False 

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = IndustryIDM()
    window.show()
    sys.exit(app.exec())