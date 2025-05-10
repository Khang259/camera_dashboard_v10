import os
import time
import argparse
import subprocess
import threading
import json
import sys
import datetime
from pathlib import Path
import signal
import atexit

class AutomationManager:
    """
    Quản lý và tự động hóa toàn bộ quy trình active learning:
    1. Thu thập dữ liệu từ camera
    2. Tự động gán nhãn với model hiện tại
    3. Huấn luyện lại model với dữ liệu mới
    """
    
    def __init__(self, 
                 config_path="../../config.json",
                 cycle_interval=3600,         # 1 giờ mỗi chu kỳ huấn luyện
                 collection_interval=10,       # 10 giây mỗi lần chụp
                 confidence_threshold=0.8,
                 base_dir='.'):
        """
        Khởi tạo Automation Manager
        
        Args:
            config_path: Đường dẫn đến file cấu hình camera
            cycle_interval: Thời gian giữa các chu kỳ huấn luyện lại (giây)
            collection_interval: Thời gian giữa các lần chụp ảnh (giây)
            confidence_threshold: Ngưỡng tin cậy cho pseudo-labeling
            base_dir: Thư mục gốc chứa mã nguồn và dữ liệu
        """
        self.config_path = config_path
        self.cycle_interval = cycle_interval
        self.collection_interval = collection_interval
        self.confidence_threshold = confidence_threshold
        self.base_dir = Path(base_dir)
        
        # Thiết lập thư mục
        self.data_dir = self.base_dir / '../data'
        self.unlabeled_dir = self.base_dir / 'unlabeled'
        self.pseudo_labeled_dir = self.base_dir / 'pseudo_labeled'
        self.manual_review_dir = self.base_dir / 'manual_review'
        
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.unlabeled_dir, exist_ok=True)
        os.makedirs(self.pseudo_labeled_dir, exist_ok=True)
        os.makedirs(self.manual_review_dir, exist_ok=True)
        
        # Theo dõi tiến trình
        self.processes = {}
        self.active = True
        self.training_active = False
        self.last_training_time = 0
        
        # Đăng ký handler để đảm bảo cleanup khi thoát
        signal.signal(signal.SIGINT, self._signal_handler)
        atexit.register(self._cleanup)
        
        # Tạo file log
        self.log_file = self.base_dir / f"automation_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
    def log(self, message):
        """Ghi log thông tin"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_message + "\n")
        except Exception as e:
            print(f"Lỗi khi ghi log: {e}")
    
    def start_automation(self):
        """Bắt đầu quy trình tự động hóa"""
        self.log("=== BẮT ĐẦU QUÁ TRÌNH TỰ ĐỘNG HÓA ===")
        self.log(f"Chu kỳ huấn luyện: {self.cycle_interval//60} phút")
        self.log(f"Khoảng thời gian thu thập: {self.collection_interval} giây")
        self.log(f"Ngưỡng tin cậy: {self.confidence_threshold}")
        
        try:
            # Bắt đầu thu thập dữ liệu
            self._start_data_collection()
            
            # Bắt đầu gán nhãn tự động
            self._start_auto_labeling()
            
            # Vòng lặp chính điều phối các hoạt động
            while self.active:
                # Kiểm tra xem có nên huấn luyện lại không
                current_time = time.time()
                if current_time - self.last_training_time >= self.cycle_interval and not self.training_active:
                    # Kiểm tra xem có đủ dữ liệu mới không
                    if self._check_new_data():
                        self._start_training()
                
                # Hiển thị thống kê
                self._show_stats()
                
                # Chờ đầu vào từ người dùng
                try:
                    user_input = input("Nhập lệnh (q: thoát, t: huấn luyện ngay, s: thống kê): ")
                    if user_input.lower() == 'q':
                        self.log("Đang dừng tự động hóa...")
                        self.active = False
                    elif user_input.lower() == 't':
                        if not self.training_active:
                            self.log("Bắt đầu huấn luyện theo yêu cầu người dùng...")
                            self._start_training()
                        else:
                            self.log("Đang trong quá trình huấn luyện, không thể bắt đầu huấn luyện mới")
                    elif user_input.lower() == 's':
                        self._show_stats(detailed=True)
                except Exception:
                    pass
                
                time.sleep(5)  # Đợi 5 giây trước khi kiểm tra lại
        
        except KeyboardInterrupt:
            self.log("Nhận tín hiệu dừng từ người dùng")
        finally:
            self._cleanup()
            self.log("=== KẾT THÚC QUÁ TRÌNH TỰ ĐỘNG HÓA ===")
    
    def _signal_handler(self, sig, frame):
        """Xử lý tín hiệu interrupt"""
        self.log("\nĐang dừng tự động hóa...")
        self.active = False
    
    def _cleanup(self):
        """Dừng tất cả các tiến trình đang chạy"""
        self.log("Đang dừng tất cả các tiến trình...")
        
        for name, process in self.processes.items():
            if process and process.poll() is None:  # Nếu tiến trình vẫn đang chạy
                self.log(f"Đang dừng tiến trình {name}...")
                try:
                    process.terminate()
                    process.wait(timeout=5)  # Đợi tối đa 5 giây
                except subprocess.TimeoutExpired:
                    self.log(f"Tiến trình {name} không phản hồi, buộc đóng...")
                    process.kill()
                except Exception as e:
                    self.log(f"Lỗi khi dừng tiến trình {name}: {e}")
        
        self.processes = {}
    
    def _start_data_collection(self):
        """Bắt đầu tiến trình thu thập dữ liệu từ camera"""
        self.log("Bắt đầu thu thập dữ liệu từ camera...")
        
        # Tạo lệnh chạy tiến trình thu thập dữ liệu
        cmd = [
            sys.executable,
            str(self.base_dir / "data_collector.py"),
            "--config", str(self.config_path),
            "--output", str(self.data_dir),
            "--interval", str(self.collection_interval),
            "--detect-dir", str(self.unlabeled_dir),
        ]
        
        # Chạy tiến trình trong nền và không block
        self.processes["data_collector"] = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Bắt đầu thread đọc output từ tiến trình
        threading.Thread(target=self._monitor_process_output, 
                        args=(self.processes["data_collector"], "data_collector"),
                        daemon=True).start()
        
        self.log("Tiến trình thu thập dữ liệu đã bắt đầu")
    
    def _start_auto_labeling(self):
        """Bắt đầu tiến trình tự động gán nhãn"""
        self.log("Bắt đầu tự động gán nhãn...")
        
        # Tạo lệnh chạy tiến trình tự động gán nhãn
        cmd = [
            sys.executable,
            str(self.base_dir / "auto_labeling.py"),
            "--unlabeled-dir", str(self.unlabeled_dir),
            "--pseudo-dir", str(self.pseudo_labeled_dir),
            "--manual-dir", str(self.manual_review_dir),
            "--confidence", str(self.confidence_threshold),
            "--interval", "5"  # Kiểm tra mỗi 5 giây
        ]
        
        # Chạy tiến trình trong nền và không block
        self.processes["auto_labeler"] = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Bắt đầu thread đọc output từ tiến trình
        threading.Thread(target=self._monitor_process_output, 
                        args=(self.processes["auto_labeler"], "auto_labeler"),
                        daemon=True).start()
        
        self.log("Tiến trình tự động gán nhãn đã bắt đầu")
    
    def _monitor_process_output(self, process, name):
        """Theo dõi và ghi log output từ tiến trình con"""
        try:
            for line in process.stdout:
                if line.strip():
                    self.log(f"[{name}] {line.strip()}")
            
            for line in process.stderr:
                if line.strip():
                    self.log(f"[{name}:ERROR] {line.strip()}")
        except Exception as e:
            self.log(f"Lỗi khi đọc output từ {name}: {e}")
    
    def _check_new_data(self):
        """Kiểm tra xem có đủ dữ liệu mới để huấn luyện không"""
        try:
            # Đếm số lượng ảnh đã có nhãn
            pseudo_count = len(list(self.pseudo_labeled_dir.glob('*.txt')))
            manual_count = len(list(self.manual_review_dir.glob('*.txt')))
            total_labeled = pseudo_count + manual_count
            
            # Yêu cầu tối thiểu 50 ảnh mới có nhãn để huấn luyện lại
            min_required = 20
            
            self.log(f"Kiểm tra dữ liệu mới: {total_labeled} ảnh đã gán nhãn (yêu cầu {min_required})")
            return total_labeled >= min_required
        
        except Exception as e:
            self.log(f"Lỗi khi kiểm tra dữ liệu mới: {e}")
            return False
    
    def _start_training(self):
        """Khởi động quá trình active learning và huấn luyện"""
        self.log("Bắt đầu quá trình active learning và huấn luyện...")
        self.training_active = True
        
        # Tạo lệnh chạy tiến trình active learning
        cmd = [
            sys.executable,
            str(self.base_dir / "active_learning.py")
        ]
        
        # Chạy tiến trình và đợi kết quả
        try:
            self.log("Chạy tiến trình Active Learning...")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                stdin=subprocess.PIPE
            )
            
            self.processes["active_learning"] = process
            
            # Tự động chạy option 5 (chạy toàn bộ chu kỳ active learning)
            process.stdin.write("5\n")
            process.stdin.flush()
            
            # Chờ và giám sát active learning
            threading.Thread(target=self._monitor_process_output, 
                            args=(process, "active_learning"),
                            daemon=True).start()
            
            # Chờ tiến trình active learning và cập nhật thời gian huấn luyện cuối
            def wait_for_training():
                try:
                    process.wait()
                    self.log("Quá trình active learning đã hoàn tất")
                    self.training_active = False
                    self.last_training_time = time.time()
                    
                    # Làm sạch thư mục pseudo_labeled sau khi huấn luyện
                    self._clean_processed_data()
                except Exception as e:
                    self.log(f"Lỗi trong tiến trình huấn luyện: {e}")
                    self.training_active = False
            
            threading.Thread(target=wait_for_training, daemon=True).start()
        
        except Exception as e:
            self.log(f"Lỗi khi bắt đầu huấn luyện: {e}")
            self.training_active = False
    
    def _clean_processed_data(self):
        """Làm sạch dữ liệu đã được xử lý sau khi huấn luyện"""
        try:
            # Xóa file trong thư mục pseudo_labeled
            for f in self.pseudo_labeled_dir.glob('*.jpg'):
                os.remove(f)
            for f in self.pseudo_labeled_dir.glob('*.txt'):
                os.remove(f)
            
            self.log("Đã dọn dẹp dữ liệu đã xử lý")
        except Exception as e:
            self.log(f"Lỗi khi dọn dẹp dữ liệu: {e}")
    
    def _show_stats(self, detailed=False):
        """Hiển thị thông tin trạng thái hiện tại"""
        try:
            # Đếm số lượng ảnh trong các thư mục
            data_count = len(list(self.data_dir.glob('*.jpg')))
            unlabeled_count = len(list(self.unlabeled_dir.glob('*.jpg')))
            pseudo_count = len(list(self.pseudo_labeled_dir.glob('*.jpg')))
            manual_count = len(list(self.manual_review_dir.glob('*.jpg')))
            
            self.log("\n=== THỐNG KÊ HỆ THỐNG ===")
            self.log(f"Trạng thái huấn luyện: {'Đang huấn luyện' if self.training_active else 'Đang chờ'}")
            self.log(f"Tổng số ảnh đã thu thập: {data_count}")
            self.log(f"Ảnh đang chờ gán nhãn: {unlabeled_count}")
            self.log(f"Ảnh đã tự động gán nhãn: {pseudo_count}")
            self.log(f"Ảnh cần gán nhãn thủ công: {manual_count}")
            
            # Hiển thị thời gian đến lần huấn luyện tiếp theo
            time_since_last = time.time() - self.last_training_time
            time_to_next = max(0, self.cycle_interval - time_since_last)
            hours, remainder = divmod(time_to_next, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if self.training_active:
                self.log("Đang huấn luyện...")
            else:
                self.log(f"Thời gian đến lần huấn luyện tiếp: {int(hours)}h {int(minutes)}m {int(seconds)}s")
            
            if detailed:
                # Thông tin chi tiết về mô hình hiện tại
                model_info = self._get_model_info()
                self.log(f"Model hiện tại: {model_info.get('path', 'Không có')}")
                if 'last_modified' in model_info:
                    self.log(f"Thời gian cập nhật model: {model_info['last_modified']}")
            
            self.log("=========================")
        
        except Exception as e:
            self.log(f"Lỗi khi hiển thị thống kê: {e}")
    
    def _get_model_info(self):
        """Lấy thông tin về model hiện tại"""
        info = {}
        try:
            model_dir = Path('runs/train')
            if model_dir.exists():
                exp_dirs = [d for d in os.listdir(model_dir) if os.path.isdir(model_dir / d)]
                if exp_dirs:
                    latest_exp = max(exp_dirs, key=lambda x: os.path.getmtime(model_dir / x))
                    model_path = model_dir / latest_exp / 'weights' / 'best.pt'
                    
                    if not model_path.exists():
                        model_path = model_dir / latest_exp / 'weights' / 'last.pt'
                    
                    if model_path.exists():
                        info['path'] = str(model_path)
                        mtime = os.path.getmtime(model_path)
                        info['last_modified'] = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            self.log(f"Lỗi khi lấy thông tin model: {e}")
        
        return info

def main():
    """Hàm chính chạy automation"""
    parser = argparse.ArgumentParser(description='Tự động hóa toàn bộ quy trình active learning')
    parser.add_argument('--config', default="../../config.json", help='Đường dẫn đến file cấu hình camera')
    parser.add_argument('--cycle', type=int, default=3600, help='Thời gian giữa các chu kỳ huấn luyện (giây)')
    parser.add_argument('--interval', type=int, default=10, help='Thời gian giữa các lần chụp ảnh (giây)')
    parser.add_argument('--confidence', type=float, default=0.8, help='Ngưỡng tin cậy cho pseudo-labeling')
    
    args = parser.parse_args()
    
    # Tạo và bắt đầu Automation Manager
    manager = AutomationManager(
        config_path=args.config,
        cycle_interval=args.cycle,
        collection_interval=args.interval,
        confidence_threshold=args.confidence
    )
    
    manager.start_automation()

if __name__ == "__main__":
    main() 