import os
import cv2
import time
import json
import argparse
import datetime
import threading
from pathlib import Path
import numpy as np
import rtsp
import sys
sys.path.append('../..')  # Để có thể import từ thư mục gốc

class RealTimeDataCollector:
    """
    Thu thập dữ liệu hình ảnh theo thời gian thực từ camera RTSP
    và lưu trữ để huấn luyện mô hình YOLOv8
    """
    
    def __init__(self, 
                 config_path=r"D:\Honda\camera_dashboard_v10\servers\config.json", 
                 output_dir=r"D:\Honda\camera_dashboard_v10\servers\ai-training\yolov8\datasets\pre-train\data",
                 interval=5,
                 capture_frames=3,
                 detection_dir="unlabeled"):
        """
        Khởi tạo Data Collector
        
        Args:
            config_path: Đường dẫn đến file cấu hình camera
            output_dir: Thư mục lưu dữ liệu thu thập
            interval: Khoảng thời gian giữa các lần chụp (giây)
            capture_frames: Số lượng frame liên tiếp thu thập mỗi lần
            detection_dir: Thư mục đưa ảnh vào quá trình nhận diện
        """
        self.output_dir = Path(output_dir)
        self.interval = interval
        self.capture_frames = capture_frames
        self.detection_dir = Path(detection_dir)
        
        # Tạo thư mục output và detection nếu chưa tồn tại
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.detection_dir, exist_ok=True)
        
        # Sử dụng đường dẫn tuyệt đối đến file cấu hình
        config_path = Path(config_path)
        print(f"Đang tìm file cấu hình tại: {config_path}")
        
        # Đọc cấu hình camera
        self.config = self._load_config(config_path)
        self.cameras = self.config.get("cameras", [])
        
        if not self.cameras:
            print("Không tìm thấy camera nào trong file cấu hình!")
        else:
            print(f"Đã tìm thấy {len(self.cameras)} camera trong cấu hình.")
        
        # Khởi tạo kết nối RTSP cho các camera
        self.camera_captures = {}
        self.stop_event = threading.Event()
        
    def _load_config(self, config_path):
        """Tải cấu hình camera từ file JSON"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Lỗi khi đọc file cấu hình tại {config_path}: {e}")
            return {"cameras": []}
    
    def _connect_camera(self, camera_config):
        """
        Kết nối đến camera qua RTSP
        
        Args:
            camera_config: Cấu hình của camera (dict với rtsp_url)
            
        Returns:
            Đối tượng kết nối đến camera hoặc None nếu lỗi
        """
        camera_id = camera_config.get("id")
        rtsp_url = camera_config.get("rtsp_url")
        
        if not rtsp_url:
            print(f"Không tìm thấy RTSP URL cho camera {camera_id}")
            return None
        
        try:
            print(f"Đang kết nối đến camera {camera_id} ({rtsp_url})...")
            # Thử kết nối với OpenCV
            cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
            
            if not cap.isOpened():
                print(f"Không thể kết nối đến camera {camera_id} với OpenCV, thử dùng RTSP client...")
                # Nếu OpenCV không thành công, thử dùng thư viện RTSP
                try:
                    cap = rtsp.Client(rtsp_url)
                except:
                    print(f"Không thể kết nối đến camera {camera_id}")
                    return None
            
            print(f"Đã kết nối thành công đến camera {camera_id}")
            return cap
        except Exception as e:
            print(f"Lỗi khi kết nối đến camera {camera_id}: {e}")
            return None
    
    def start_collecting(self):
        """Bắt đầu thu thập dữ liệu từ tất cả camera"""
        print(f"Bắt đầu thu thập dữ liệu với chu kỳ {self.interval} giây...")
        
        # Tạo thread cho mỗi camera
        threads = []
        
        for camera in self.cameras:
            thread = threading.Thread(
                target=self._collect_from_camera,
                args=(camera,),
                daemon=True
            )
            threads.append(thread)
            thread.start()
        
        try:
            while not self.stop_event.is_set():
                # Hiển thị số lượng ảnh đã thu thập
                data_count = len(list(self.output_dir.glob('*.jpg')))
                detect_count = len(list(self.detection_dir.glob('*.jpg')))
                print(f"Đã thu thập: {data_count} ảnh (data), {detect_count} ảnh (unlabeled)")
                
                # Chờ đầu vào từ người dùng
                try:
                    user_input = input("Nhấn 'q' để dừng, 'c' để chụp ngay lập tức: ")
                    if user_input.lower() == 'q':
                        print("Đang dừng thu thập dữ liệu...")
                        self.stop_event.set()
                    elif user_input.lower() == 'c':
                        print("Đang chụp ảnh từ tất cả camera...")
                        for camera in self.cameras:
                            self._capture_frames(camera)
                    
                    time.sleep(0.1)  # Tránh CPU cao
                except KeyboardInterrupt:
                    print("\nĐang dừng thu thập dữ liệu...")
                    self.stop_event.set()
                except Exception:
                    pass  # Bỏ qua lỗi đầu vào
        
        except KeyboardInterrupt:
            print("\nĐang dừng thu thập dữ liệu...")
            self.stop_event.set()
        
        # Chờ các thread kết thúc
        for thread in threads:
            thread.join()
        
        # Đóng tất cả kết nối camera
        for cap in self.camera_captures.values():
            if isinstance(cap, cv2.VideoCapture):
                cap.release()
        
        print("Đã dừng thu thập dữ liệu.")
    
    def _collect_from_camera(self, camera):
        """
        Thu thập dữ liệu từ một camera cụ thể
        
        Args:
            camera: Cấu hình camera (dict)
        """
        camera_id = camera.get("id")
        
        # Kết nối đến camera
        cap = self._connect_camera(camera)
        if cap is None:
            print(f"Bỏ qua camera {camera_id} do không thể kết nối")
            return
        
        self.camera_captures[camera_id] = cap
        
        # Bắt đầu chu kỳ thu thập
        while not self.stop_event.is_set():
            try:
                # Thu thập frames
                self._capture_frames(camera)
                
                # Chờ đến chu kỳ tiếp theo
                for _ in range(int(self.interval * 10)):  # Chia thành các chunk nhỏ hơn để phản ứng nhanh hơn khi stop
                    if self.stop_event.is_set():
                        break
                    time.sleep(0.1)
            
            except Exception as e:
                print(f"Lỗi khi thu thập từ camera {camera_id}: {e}")
                # Thử kết nối lại
                time.sleep(5)
                cap = self._connect_camera(camera)
                if cap:
                    self.camera_captures[camera_id] = cap
    
    def _capture_frames(self, camera):
        """
        Chụp một loạt frames từ camera
        
        Args:
            camera: Cấu hình camera (dict)
        """
        camera_id = camera.get("id")
        cap = self.camera_captures.get(camera_id)
        
        if cap is None:
            return
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for i in range(self.capture_frames):
            try:
                # Đọc frame
                if isinstance(cap, cv2.VideoCapture):
                    ret, frame = cap.read()
                    if not ret:
                        print(f"Không thể đọc frame từ camera {camera_id}, thử kết nối lại...")
                        # Thử kết nối lại
                        cap = self._connect_camera(camera)
                        if cap:
                            self.camera_captures[camera_id] = cap
                        continue
                else:  # rtsp.Client
                    frame = cap.read()
                    ret = frame is not None
                    if not ret:
                        print(f"Không thể đọc frame từ camera {camera_id}, thử kết nối lại...")
                        cap = self._connect_camera(camera)
                        if cap:
                            self.camera_captures[camera_id] = cap
                        continue
                
                # Tạo tên file duy nhất
                # Format: YYYYMMDD_HHMMSS_cameraID_index.jpg
                filename = f"{timestamp}_{camera_id}_{i}.jpg"
                
                # Lưu frame
                output_path = self.output_dir / filename
                cv2.imwrite(str(output_path), frame)
                
                # Sao chép vào thư mục phát hiện nếu là frame đầu tiên
                if i == 0:
                    detect_path = self.detection_dir / filename
                    cv2.imwrite(str(detect_path), frame)
                
                print(f"Đã lưu frame vào {output_path}")
                
                # Chờ một chút giữa các lần chụp
                time.sleep(0.1)
            
            except Exception as e:
                print(f"Lỗi khi chụp frame từ camera {camera_id}: {e}")

def main():
    """Hàm chính chạy trình thu thập dữ liệu"""
    parser = argparse.ArgumentParser(description='Thu thập dữ liệu thời gian thực từ camera RTSP')
    parser.add_argument('--config', default=r"D:\Honda\camera_dashboard_v10\servers\config.json", 
                        help='Đường dẫn đến file cấu hình')
    parser.add_argument('--output', default=r"D:\Honda\camera_dashboard_v10\servers\ai-training\yolov8\datasets\pre-train\data", 
                        help='Thư mục lưu dữ liệu')
    parser.add_argument('--interval', type=int, default=10, help='Chu kỳ thu thập (giây)')
    parser.add_argument('--frames', type=int, default=3, help='Số lượng frame mỗi chu kỳ')
    parser.add_argument('--detect-dir', default="unlabeled", help='Thư mục cho quá trình phát hiện')
    
    args = parser.parse_args()
    
    collector = RealTimeDataCollector(
        config_path=args.config,
        output_dir=args.output,
        interval=args.interval,
        capture_frames=args.frames,
        detection_dir=args.detect_dir
    )
    
    collector.start_collecting()

if __name__ == "__main__":
    main()