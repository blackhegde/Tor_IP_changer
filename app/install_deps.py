# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import tempfile
import urllib.request
from tkinter import messagebox

def install_python_libs():
    """Tự động cài đặt thư viện Python cần thiết"""
    required_libs = ['pysocks', 'stem', 'requests']
    
    # Kiểm tra và cài đặt từng thư viện
    for lib in required_libs:
        try:
            __import__(lib)
        except ImportError:
            try:
                # Cài đặt bằng pip
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', lib], 
                                    creationflags=subprocess.CREATE_NO_WINDOW)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể cài đặt {lib}: {str(e)}")
                return False
    return True

def check_tor_portable():
    """Kiểm tra Tor portable"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    tor_path = os.path.join(base_path, "tor_portable", "tor.exe")
    return os.path.exists(tor_path)

if __name__ == "__main__":
    if install_python_libs() and check_tor_portable():
        messagebox.showinfo("Thành công", "Đã cài đặt xong các thư viện cần thiết!")
    else:
        messagebox.showerror("Lỗi", "Cài đặt không hoàn tất!")