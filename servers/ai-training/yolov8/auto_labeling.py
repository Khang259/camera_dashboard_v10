import os
import cv2
import time
import json
import threading
from pathlib import Path
import numpy as np
from ultralytics import YOLO
import datetime
import argparse
import shutil

class AutoLabeler:
    """
    Tự động gán nhãn cho ảnh từ thư mục unlabeled theo thời gian thực,
    kết hợp active learning để cải thiện mô hình liên tục.
    """
    
    def __init__(self, 
                 model_path=None,
                 unlabeled_dir="unlabeled",
                 pseudo_labeled_dir="pseudo_labeled",
                 manual_review_dir="manual_review",
                 confidence_threshold=0.8,
                 interval=5):
        """
        Khởi tạo Auto Labeler
        
        Args:
            model_path: Đường dẫn tới model YOLOv8, nếu None sẽ tìm model tốt nhất
            unlabeled_dir: Thư mục chứa ảnh chưa gán nhãn
            pseudo_labeled_dir: Thư mục chứa ảnh đã tự động gán nhãn (confidence cao)
            manual_review_dir: Thư mục chứa ảnh cần xem xét thủ công (confidence thấp)
            confidence_threshold: Ngưỡng tin cậy để quyết định tự động gán nhãn
            interval: Thời gian giữa các lần quét thư mục (giây)
        """
        self.unlabeled_dir = Path(unlabeled_dir)
        self.pseudo_labeled_dir = Path(pseudo_labeled_dir)
        self.manual_review_dir = Path(manual_review_dir)
        self.confidence_threshold = confidence_threshold
        self.interval = interval
        
        # Tạo các thư mục nếu chưa tồn tại
        os.makedirs(self.unlabeled_dir, exist_ok=True)
        os.makedirs(self.pseudo_labeled_dir, exist_ok=True)
        os.makedirs(self.manual_review_dir, exist_ok=True)
        
        # Tìm model tốt nhất nếu không được cung cấp
        self.model_path = self._find_best_model() if model_path is None else model_path
        print(f"Sử dụng model: {self.model_path}")
        
        # Tải model
        try:
            self.model = YOLO(self.model_path)
            print(f"Đã tải model thành công với {len(self.model.names)} lớp")
            self.classes = self.model.names
        except Exception as e:
            print(f"Lỗi khi tải model: {e}")
            self.model = None
            self.classes = {"0": "box", "1": "container", "2": "package"}
        
        # Cờ điều khiển
        self.stop_event = threading.Event()
        
        # Thống kê
        self.stats = {
            "processed": 0,
            "pseudo_labeled": 0,
            "manual_review": 0,
            "start_time": time.time()
        }
    
    def _find_best_model(self):
        """Tìm model tốt nhất trong thư mục runs/train"""
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
                        return str(model_path)
            
            # Nếu không tìm thấy, sử dụng model mặc định
            return 'yolov8n.pt'
        except Exception as e:
            print(f"Lỗi khi tìm model tốt nhất: {e}")
            return 'yolov8n.pt'
    
    def start_auto_labeling(self):
        """Bắt đầu quá trình tự động gán nhãn"""
        if self.model is None:
            print("Không thể bắt đầu tự động gán nhãn vì không có model")
            return
        
        print(f"Bắt đầu tự động gán nhãn với chu kỳ {self.interval} giây...")
        
        # Tạo thread cho việc gán nhãn
        labeling_thread = threading.Thread(
            target=self._auto_labeling_loop,
            daemon=True
        )
        labeling_thread.start()
        
        try:
            while not self.stop_event.is_set():
                # Hiển thị thống kê
                self._show_stats()
                
                # Chờ đầu vào từ người dùng
                try:
                    user_input = input("Nhập lệnh (q: thoát, r: reload model, s: thống kê): ")
                    if user_input.lower() == 'q':
                        print("Đang dừng tự động gán nhãn...")
                        self.stop_event.set()
                    elif user_input.lower() == 'r':
                        print("Đang tải lại model...")
                        self._reload_model()
                    elif user_input.lower() == 's':
                        self._show_stats(detailed=True)
                    
                    time.sleep(0.1)  # Tránh CPU cao
                except KeyboardInterrupt:
                    print("\nĐang dừng tự động gán nhãn...")
                    self.stop_event.set()
                except Exception:
                    pass  # Bỏ qua lỗi đầu vào
        
        except KeyboardInterrupt:
            print("\nĐang dừng tự động gán nhãn...")
            self.stop_event.set()
        
        # Chờ thread kết thúc
        labeling_thread.join()
        
        print("Đã dừng tự động gán nhãn.")
    
    def _auto_labeling_loop(self):
        """Vòng lặp chính cho việc tự động gán nhãn"""
        while not self.stop_event.is_set():
            try:
                # Tìm ảnh chưa gán nhãn
                unlabeled_images = list(self.unlabeled_dir.glob('*.jpg')) + list(self.unlabeled_dir.glob('*.jpeg')) + list(self.unlabeled_dir.glob('*.png'))
                if not unlabeled_images:
                    # Nếu không có ảnh nào, đợi một chút rồi thử lại
                    time.sleep(self.interval)
                    continue
                
                print(f"Tìm thấy {len(unlabeled_images)} ảnh chưa gán nhãn")
                
                # Xử lý từng ảnh
                for img_path in unlabeled_images:
                    if self.stop_event.is_set():
                        break
                    
                    self._process_image(img_path)
                    self.stats["processed"] += 1
                
                # Đợi chu kỳ tiếp theo
                for _ in range(int(self.interval * 10)):  # Chia thành các chunk nhỏ để phản ứng nhanh hơn khi stop
                    if self.stop_event.is_set():
                        break
                    time.sleep(0.1)
            
            except Exception as e:
                print(f"Lỗi trong chu trình gán nhãn: {e}")
                time.sleep(5)  # Đợi một lúc sau khi gặp lỗi
    
    def _process_image(self, img_path):
        """
        Xử lý và gán nhãn cho một ảnh
        
        Args:
            img_path: Đường dẫn đến ảnh cần xử lý
        """
        try:
            print(f"Đang xử lý ảnh: {img_path}")
            
            # Dự đoán với model
            results = self.model(img_path, conf=0.1)  # Đặt ngưỡng thấp để bắt nhiều dự đoán
            
            boxes = []
            high_confidence_boxes = []
            
            # Phân tích kết quả dự đoán
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    width, height = x2 - x1, y2 - y1
                    
                    cls_id = int(box.cls[0].item())
                    conf = float(box.conf[0].item())
                    
                    # Chuyển đổi sang định dạng YOLOv8 (chuẩn hóa và lấy tâm)
                    img_width, img_height = result.orig_shape[1], result.orig_shape[0]
                    
                    x_center = (x1 + x2) / 2 / img_width
                    y_center = (y1 + y2) / 2 / img_height
                    norm_width = width / img_width
                    norm_height = height / img_height
                    
                    box_info = {
                        "class_id": cls_id,
                        "x_center": x_center,
                        "y_center": y_center,
                        "width": norm_width,
                        "height": norm_height,
                        "confidence": conf
                    }
                    
                    boxes.append(box_info)
                    if conf >= self.confidence_threshold:
                        high_confidence_boxes.append(box_info)
            
            # Quyết định điều hướng ảnh
            if high_confidence_boxes:
                # Có ít nhất một box có confidence cao -> pseudo-labeling
                target_dir = self.pseudo_labeled_dir
                self.stats["pseudo_labeled"] += 1
                
                # Tạo file nhãn với định dạng YOLO
                label_path = target_dir / f"{img_path.stem}.txt"
                with open(label_path, 'w') as f:
                    for box in high_confidence_boxes:
                        f.write(f"{box['class_id']} {box['x_center']} {box['y_center']} {box['width']} {box['height']}\n")
                
                # Vẽ bounding box lên ảnh để thuận tiện cho việc xem xét
                self._draw_predictions(img_path, high_confidence_boxes, target_dir)
            else:
                # Không có box nào có confidence cao -> cần review thủ công
                target_dir = self.manual_review_dir
                self.stats["manual_review"] += 1
                
                # Lưu thông tin box cho việc gán nhãn thủ công sau này
                if boxes:
                    metadata_path = target_dir / f"{img_path.stem}.json"
                    with open(metadata_path, 'w') as f:
                        json.dump(boxes, f, indent=2)
                    
                    # Vẽ box với độ tin cậy thấp để gợi ý cho người dùng
                    self._draw_predictions(img_path, boxes, target_dir, low_confidence=True)
            
            # Di chuyển ảnh gốc đến thư mục tương ứng
            shutil.copy2(img_path, target_dir / img_path.name)
            
            # Xóa ảnh gốc từ thư mục unlabeled
            os.remove(img_path)
            
            print(f"Đã xử lý xong ảnh: {img_path}")
        
        except Exception as e:
            print(f"Lỗi khi xử lý ảnh {img_path}: {e}")
    
    def _draw_predictions(self, img_path, boxes, target_dir, low_confidence=False):
        """
        Vẽ bounding box lên ảnh cho việc xem xét
        
        Args:
            img_path: Đường dẫn ảnh gốc
            boxes: Danh sách các bounding box
            target_dir: Thư mục lưu ảnh đã vẽ
            low_confidence: Có phải là box có độ tin cậy thấp không
        """
        try:
            # Đọc ảnh
            img = cv2.imread(str(img_path))
            height, width, _ = img.shape
            
            # Màu cho các lớp khác nhau (BGR)
            colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0)]
            
            # Vẽ bounding boxes
            for box in boxes:
                cls_id = box["class_id"]
                conf = box["confidence"]
                
                # Chuyển đổi từ tọa độ chuẩn hóa sang pixel
                x_center = box["x_center"] * width
                y_center = box["y_center"] * height
                w = box["width"] * width
                h = box["height"] * height
                
                x1 = int(x_center - w/2)
                y1 = int(y_center - h/2)
                x2 = int(x_center + w/2)
                y2 = int(y_center + h/2)
                
                # Vẽ box
                color = colors[cls_id % len(colors)]
                if low_confidence:
                    # Đường đứt nét cho độ tin cậy thấp
                    thickness = 1
                    line_type = cv2.LINE_DASH
                else:
                    thickness = 2
                    line_type = cv2.LINE_AA
                
                cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness, line_type)
                
                # Vẽ nhãn
                cls_name = self.classes.get(str(cls_id), f"Class {cls_id}")
                label = f"{cls_name}: {conf:.2f}"
                cv2.putText(img, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Lưu ảnh đã vẽ
            vis_dir = target_dir / "visualized"
            os.makedirs(vis_dir, exist_ok=True)
            cv2.imwrite(str(vis_dir / img_path.name), img)
        
        except Exception as e:
            print(f"Lỗi khi vẽ dự đoán cho ảnh {img_path}: {e}")
    
    def _reload_model(self):
        """Tải lại model (hữu ích khi huấn luyện lại model trong quá trình active learning)"""
        try:
            # Tìm model mới nhất
            new_model_path = self._find_best_model()
            
            if new_model_path != self.model_path:
                print(f"Tìm thấy model mới: {new_model_path}")
                self.model_path = new_model_path
                
                # Tải model mới
                self.model = YOLO(self.model_path)
                print(f"Đã tải lại model thành công với {len(self.model.names)} lớp")
                self.classes = self.model.names
            else:
                print("Không tìm thấy model mới")
        
        except Exception as e:
            print(f"Lỗi khi tải lại model: {e}")
    
    def _show_stats(self, detailed=False):
        """Hiển thị thống kê về quá trình gán nhãn"""
        runtime = time.time() - self.stats["start_time"]
        hours, remainder = divmod(runtime, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        print("\n=== THỐNG KÊ GÁN NHÃN ===")
        print(f"Thời gian chạy: {int(hours)}h {int(minutes)}m {int(seconds)}s")
        print(f"Tổng số ảnh đã xử lý: {self.stats['processed']}")
        print(f"Tự động gán nhãn: {self.stats['pseudo_labeled']} ({self.stats['pseudo_labeled']/max(1, self.stats['processed'])*100:.1f}%)")
        print(f"Cần xem xét thủ công: {self.stats['manual_review']} ({self.stats['manual_review']/max(1, self.stats['processed'])*100:.1f}%)")
        
        if detailed:
            # Số lượng ảnh còn lại chưa xử lý
            unlabeled_count = len(list(self.unlabeled_dir.glob('*.jpg'))) + len(list(self.unlabeled_dir.glob('*.jpeg'))) + len(list(self.unlabeled_dir.glob('*.png')))
            print(f"Ảnh chưa xử lý: {unlabeled_count}")
            
            # Tốc độ xử lý
            if runtime > 0:
                rate = self.stats['processed'] / (runtime / 3600)
                print(f"Tốc độ xử lý: {rate:.1f} ảnh/giờ")
            
            print(f"Model hiện tại: {self.model_path}")
            print("===========================")

def main():
    """Hàm chính chạy trình tự động gán nhãn"""
    parser = argparse.ArgumentParser(description='Tự động gán nhãn cho ảnh từ thư mục unlabeled')
    parser.add_argument('--model', default=None, help='Đường dẫn đến model (nếu không cung cấp sẽ tìm model tốt nhất)')
    parser.add_argument('--unlabeled-dir', default="unlabeled", help='Thư mục chứa ảnh chưa gán nhãn')
    parser.add_argument('--pseudo-dir', default="pseudo_labeled", help='Thư mục chứa ảnh đã tự động gán nhãn')
    parser.add_argument('--manual-dir', default="manual_review", help='Thư mục chứa ảnh cần xem xét thủ công')
    parser.add_argument('--confidence', type=float, default=0.8, help='Ngưỡng tin cậy để quyết định tự động gán nhãn')
    parser.add_argument('--interval', type=int, default=5, help='Thời gian giữa các lần quét thư mục (giây)')
    
    args = parser.parse_args()
    
    labeler = AutoLabeler(
        model_path=args.model,
        unlabeled_dir=args.unlabeled_dir,
        pseudo_labeled_dir=args.pseudo_dir,
        manual_review_dir=args.manual_dir,
        confidence_threshold=args.confidence,
        interval=args.interval
    )
    
    labeler.start_auto_labeling()

if __name__ == "__main__":
    main() 