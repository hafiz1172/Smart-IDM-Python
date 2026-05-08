# SwiftGet - Python Internet Download Manager (IDM) 🚀

Welcome to **SwiftGet**! This is a fast, multi-threaded Internet Download Manager built with Python. It can download normal files very quickly and can also download videos directly from YouTube and other social media platforms.

## 🌟 Main Features
* **Multi-threaded Downloading:** Breaks large files into 4 parts and downloads them at the same time for high speed.
* **YouTube Video Downloader:** Automatically detects YouTube/Facebook links and downloads the video.
* **Pause & Resume:** You can pause your download and resume it later without losing data.
* **Modern GUI:** A clean and beautiful user interface made with PyQt6.
* **Standalone App:** Can be converted into a `.exe` file so you don't need Python to run it.

---

## 🛠️ How to Use This Code

If you want to run this code on your computer, follow these simple steps:

### 1. Install Required Libraries
Open your Command Prompt (CMD) or terminal and run this command to install all the necessary Python packages:
```bash
pip install PyQt6 requests yt-dlp pyinstaller

2. Run the Source Code
Make sure main_app.py and idm_design.ui are in the same folder. Then run:
python main_app.py

How to Convert into a .exe Software
If you want to create a portable Windows software (.exe) that you can share with your friends, follow this step.

Open your terminal in the project folder and run this magic command:
pyinstaller --noconsole --onefile --add-data "idm_design.ui;." main_app.py

Note: If you have an icon file (like logo.ico), you can use this command instead:
pyinstaller --noconsole --onefile --add-data "idm_design.ui;." --icon="logo.ico" main_app.py

After 2-3 minutes, go to the dist folder. You will find your ready-to-use .exe software there! You can delete the build folder and .spec file as they are temporary.

Author
Muhammad Tariq Computer Engineering Student

Feel free to use this code, modify it, and learn from it!
