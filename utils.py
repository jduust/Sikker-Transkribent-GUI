import subprocess
import os
import tempfile
from datetime import timedelta
import sys

def format_timestamp(seconds):
    h, m, s = str(timedelta(seconds=int(seconds))).split(":")
    return f"{int(h):02}:{int(m):02}:{int(s):02}"

def get_ffmpeg_path():
    """Return path to ffmpeg.exe, works both in Python and PyInstaller EXE."""
    if getattr(sys, 'frozen', False):
        # Running as EXE
        base_path = sys._MEIPASS
    else:
        # Running as script
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, 'ffmpeg', 'ffmpeg.exe')

def convert_to_wav(file_path):
    temp_fd, temp_path = tempfile.mkstemp(suffix=".wav")
    os.close(temp_fd)

    ffmpeg_exe = get_ffmpeg_path()  # your function from utils.py

    cmd = [
        ffmpeg_exe, "-y", "-i", file_path,
        "-af", "aresample=async=1",
        "-ar", "16000", "-ac", "1",
        "-fflags", "+genpts", "-err_detect", "ignore_err",
        temp_path
    ]

    if sys.platform == "win32":
        # Hide ffmpeg console window
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return temp_path