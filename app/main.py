# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import ctypes
import time
import requests
from tkinter import Tk, messagebox, Toplevel, Text, Button, END, Label

class TorServiceManager:
    @staticmethod
    def get_tor_dir():
        """Lấy đường dẫn thư mục tor (đã fix cho cả khi đóng gói)"""
        try:
            base_dir = sys._MEIPASS  # Khi đóng gói bằng PyInstaller
        except AttributeError:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_dir, 'tor')

    @staticmethod
    def is_admin():
        """Kiểm tra quyền admin"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
        
    @classmethod
    def run_as_admin(cls):
        """Yêu cầu chạy lại với quyền admin"""
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, None, 1)
        sys.exit(0)

    @classmethod
    def install_service(cls):
        """Cài đặt service với debug chi tiết"""
        tor_exe = os.path.join(cls.get_tor_dir(), 'tor.exe')
        print(f"[DEBUG] Đường dẫn tor.exe: {tor_exe}")  # Debug path
        
        if not os.path.exists(tor_exe):
            error_msg = f"Không tìm thấy file tor.exe tại: {tor_exe}"
            print(f"[ERROR] {error_msg}")
            messagebox.showerror("Lỗi", error_msg)
            return False
        try:
            # Tạo service với logging chi tiết
            print("[DEBUG] Đang tạo Tor service...")
            create_cmd = [
                'sc', 'create', 'Tor',
                f'binPath= "{tor_exe}" --service',
                'start= auto',
                'DisplayName= "Tor Service"'
            ]
            print(f"[DEBUG] Command: {' '.join(create_cmd)}")
            
            result = subprocess.run(
                create_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                text=True,
                timeout=15
            )
            
            if result.returncode != 0:
                error_msg = f"Lỗi tạo service: {result.stderr}"
                print(f"[ERROR] {error_msg}")
                messagebox.showerror("Lỗi", error_msg)
                return False
            
            print("[DEBUG] Đã tạo service thành công")
            return True
            
        except Exception as e:
            error_msg = f"Lỗi khi cài đặt: {str(e)}"
            print(f"[ERROR] {error_msg}")
            messagebox.showerror("Lỗi", error_msg)
            return False

    @classmethod
    def service_action(cls, action):
        """Điều khiển service (start/stop/restart)"""
        try:
            if action == 'restart':
                cls.service_action('stop')
                time.sleep(2)
                action = 'start'
            
            result = subprocess.run(
                ['sc', action, 'Tor'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=10
            )
            
            if result.returncode == 0:
                time.sleep(3)  # Chờ service ổn định
                return True
            
            # Xử lý lỗi cụ thể
            if "1060" in result.stderr.decode('utf-8', 'ignore'):
                if cls.install_service():
                    return cls.service_action(action)
            return False
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể {action} service: {str(e)}")
            return False

    @classmethod
    def check_service_exists(cls):
        """Kiểm tra service đã được cài đặt chưa"""
        try:
            output = subprocess.check_output(
                ['sc', 'query', 'Tor'],
                stderr=subprocess.PIPE,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True
            )
            return "SERVICE_NAME: Tor" in output
        except subprocess.CalledProcessError as e:
            print(f"Error checking service: {e}")
            return False

    @classmethod
    def setup(cls):
        """Thiết lập hệ thống Tor"""
        if not cls.is_admin():
            messagebox.showwarning(
                "Yêu cầu quyền Admin",
                "Ứng dụng cần quyền Administrator để cài đặt Tor Service\n"
                "Vui lòng chạy lại với quyền admin"
            )
            return False
        
        if not cls.check_service_exists():
            messagebox.showinfo("Thông báo", "Đang cài đặt Tor Service lần đầu...")
            if not cls.install_service():
                return False
        
        return cls.service_action('start')

class TorIPChangerApp:
    def __init__(self):
        self.check_admin()  # Kiểm tra quyền admin
        self.root = Tk()
        self.root.withdraw()
        
        if not TorServiceManager.setup():
            sys.exit(1)
        
        self.setup_ui()
        self.update_ip()

    def check_admin(self):
        """Kiểm tra quyền admin với debug"""
        print("[DEBUG] Đang kiểm tra quyền admin...")
        if not ctypes.windll.shell32.IsUserAnAdmin():
            print("[DEBUG] Không có quyền admin, yêu cầu nâng cấp...")
            TorServiceManager.run_as_admin()
        print("[DEBUG] Đã chạy với quyền admin")

    def setup_ui(self):
        """Thiết lập giao diện người dùng"""
        self.window = Toplevel()
        self.window.title("Tor IP Changer - Chế độ Service")
        self.window.geometry("500x400")
        
        # Hiển thị IP
        self.ip_label = Label(
            self.window,
            text="Đang kết nối đến Tor...",
            font=("Arial", 12)
        )
        self.ip_label.pack(pady=20)
        
        # Các nút chức năng
        Button(
            self.window,
            text="Thay Đổi IP",
            command=self.change_ip,
            font=("Arial", 10),
            width=15
        ).pack(pady=10)
        
        Button(
            self.window,
            text="Kiểm Tra IP",
            command=self.update_ip,
            font=("Arial", 10),
            width=15
        ).pack(pady=10)
        
        # Console log
        self.log = Text(self.window, height=12)
        self.log.pack(pady=10, fill='both', expand=True)
        self.write_log("Ứng dụng đã sẵn sàng")

    def write_log(self, message):
        """Ghi log vào console"""
        timestamp = time.strftime("%H:%M:%S")
        self.log.insert(END, f"[{timestamp}] {message}\n")
        self.log.see(END)

    def get_current_ip(self):
        """Lấy IP hiện tại qua Tor"""
        try:
            response = requests.get(
                'https://api.ipify.org',
                proxies={
                    'http': 'socks5h://127.0.0.1:9050',
                    'https': 'socks5h://127.0.0.1:9050'
                },
                timeout=15
            )
            return response.text.strip()
        except Exception as e:
            raise Exception(f"Không thể lấy IP: {str(e)}")

    def update_ip(self):
        """Cập nhật hiển thị IP"""
        try:
            ip = self.get_current_ip()
            self.ip_label.config(text=f"IP hiện tại: {ip}")
            self.write_log(f"Kết nối thành công. IP: {ip}")
        except Exception as e:
            self.ip_label.config(text="Lỗi kết nối Tor!")
            self.write_log(f"Lỗi: {str(e)}")

    def change_ip(self):
        """Thay đổi IP bằng cách restart service"""
        self.write_log("Đang thay đổi IP...")
        if TorServiceManager.service_action('restart'):
            time.sleep(5)  # Chờ Tor khởi động lại
            self.update_ip()
        else:
            self.write_log("Không thể thay đổi IP. Thử lại...")
            if TorServiceManager.service_action('start'):
                time.sleep(5)
                self.update_ip()

if __name__ == "__main__":
    try:
        import requests
    except ImportError:
        print("Vui lòng cài đặt thư viện requests:")
        print("pip install requests")
        sys.exit(1)
    
    app = TorIPChangerApp()
    app.root.mainloop()