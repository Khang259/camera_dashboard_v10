import os
import shutil
import glob
import json
import random
import numpy as np
from pathlib import Path
from ultralytics import YOLO

class ActiveLearningManager:
    """
    Quản lý quy trình Active Learning và Pseudo-Labeling cho YOLOv8
    """
    
    def __init__(self, 
                 base_dir='.',
                 data_dir='../data',
                 dataset_dir='datasets/items',
                 model_path=None,
                 confidence_threshold=0.8):
        """
        Khởi tạo Active Learning Manager
        
        Args:
            base_dir: Thư mục cơ sở cho dự án
            data_dir: Thư mục chứa dữ liệu gốc (ảnh chưa gán nhãn)
            dataset_dir: Thư mục lưu dataset đã chuẩn bị
            model_path: Đường dẫn đến model, nếu None sẽ tìm model tốt nhất
            confidence_threshold: Ngưỡng tin cậy cho pseudo-labeling
        """
        self.base_dir = Path(base_dir)
        self.data_dir = Path(data_dir)
        self.dataset_dir = Path(dataset_dir)
        self.confidence_threshold = confidence_threshold
        
        # Tạo và kiểm tra thư mục
        self.unlabeled_dir = self.base_dir / 'unlabeled'
        self.pseudo_labeled_dir = self.base_dir / 'pseudo_labeled'
        self.manual_review_dir = self.base_dir / 'manual_review'
        
        os.makedirs(self.unlabeled_dir, exist_ok=True)
        os.makedirs(self.pseudo_labeled_dir, exist_ok=True)
        os.makedirs(self.manual_review_dir, exist_ok=True)
        
        for split in ['train', 'val']:
            for subdir in ['images', 'labels']:
                os.makedirs(self.dataset_dir / split / subdir, exist_ok=True)
        
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
    
    def _find_best_model(self):
        """Tìm model tốt nhất trong thư mục runs/train"""
        try:
            model_dir = self.base_dir / 'runs/train'
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
    
    def collect_unlabeled_data(self):
        """Thu thập dữ liệu chưa gán nhãn từ thư mục data"""
        # Tìm tất cả các file ảnh trong thư mục data
        image_files = list(self.data_dir.glob('*.jpg')) + list(self.data_dir.glob('*.jpeg')) + list(self.data_dir.glob('*.png'))
        
        # Kiểm tra xem ảnh đã có trong dataset chưa
        existing_images = []
        for split in ['train', 'val']:
            existing_images.extend([os.path.basename(p) for p in glob.glob(str(self.dataset_dir / split / 'images' / '*.*'))])
        
        # Copy các ảnh chưa gán nhãn vào thư mục unlabeled
        count = 0
        for img_path in image_files:
            if img_path.name not in existing_images and not (self.unlabeled_dir / img_path.name).exists():
                shutil.copy2(img_path, self.unlabeled_dir)
                count += 1
        
        print(f"Đã thu thập {count} ảnh mới chưa gán nhãn")
    
    def run_pseudo_labeling(self):
        """Chạy pseudo-labeling trên dữ liệu chưa gán nhãn"""
        if self.model is None:
            print("Không thể chạy pseudo-labeling vì không có model")
            return
        
        # Lấy danh sách ảnh chưa gán nhãn
        unlabeled_images = list(self.unlabeled_dir.glob('*.jpg')) + list(self.unlabeled_dir.glob('*.jpeg')) + list(self.unlabeled_dir.glob('*.png'))
        
        if not unlabeled_images:
            print("Không tìm thấy ảnh chưa gán nhãn")
            return
        
        print(f"Chạy pseudo-labeling trên {len(unlabeled_images)} ảnh...")
        
        high_confidence_count = 0
        low_confidence_count = 0
        
        # Xử lý từng ảnh
        for img_path in unlabeled_images:
            # Dự đoán đối tượng
            results = self.model(img_path, conf=0.1)  # Đặt ngưỡng thấp để bắt nhiều dự đoán
            
            boxes = []
            high_confidence_boxes = []
            
            # Kiểm tra kết quả dự đoán
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
                high_confidence_count += 1
                
                # Tạo file nhãn với định dạng YOLO
                label_path = target_dir / f"{img_path.stem}.txt"
                with open(label_path, 'w') as f:
                    for box in high_confidence_boxes:
                        f.write(f"{box['class_id']} {box['x_center']} {box['y_center']} {box['width']} {box['height']}\n")
            else:
                # Không có box nào có confidence cao -> cần review thủ công
                target_dir = self.manual_review_dir
                low_confidence_count += 1
                
                # Lưu thông tin box cho việc gán nhãn thủ công sau này
                if boxes:
                    metadata_path = target_dir / f"{img_path.stem}.json"
                    with open(metadata_path, 'w') as f:
                        json.dump(boxes, f, indent=2)
            
            # Di chuyển ảnh đến thư mục tương ứng
            shutil.copy2(img_path, target_dir / img_path.name)
            
            # Xóa ảnh từ thư mục unlabeled
            os.remove(img_path)
        
        print(f"Đã xử lý xong {len(unlabeled_images)} ảnh:")
        print(f"- {high_confidence_count} ảnh đã được pseudo-label với confidence ≥ {self.confidence_threshold}")
        print(f"- {low_confidence_count} ảnh cần gán nhãn thủ công")
    
    def update_dataset(self, val_split=0.2):
        """
        Cập nhật dataset với dữ liệu đã gán nhãn (tự động và thủ công)
        
        Args:
            val_split: Tỷ lệ dữ liệu dành cho validation
        """
        # Thu thập ảnh đã gán nhãn
        pseudo_images = [(p, self.pseudo_labeled_dir / f"{p.stem}.txt") 
                         for p in self.pseudo_labeled_dir.glob('*.jpg') 
                         if (self.pseudo_labeled_dir / f"{p.stem}.txt").exists()]
        
        manual_images = [(p, self.manual_review_dir / f"{p.stem}.txt") 
                         for p in self.manual_review_dir.glob('*.jpg') 
                         if (self.manual_review_dir / f"{p.stem}.txt").exists()]
        
        all_labeled_images = pseudo_images + manual_images
        
        if not all_labeled_images:
            print("Không tìm thấy ảnh đã gán nhãn để cập nhật dataset")
            return
        
        # Xáo trộn dữ liệu
        random.shuffle(all_labeled_images)
        
        # Chia tập train/val
        split_idx = int(len(all_labeled_images) * (1 - val_split))
        train_images = all_labeled_images[:split_idx]
        val_images = all_labeled_images[split_idx:]
        
        # Thêm vào dataset
        for split, images in [('train', train_images), ('val', val_images)]:
            for img_path, label_path in images:
                # Copy ảnh và nhãn
                shutil.copy2(img_path, self.dataset_dir / split / 'images' / img_path.name)
                shutil.copy2(label_path, self.dataset_dir / split / 'labels' / label_path.name)
                
                # Xóa file gốc sau khi đã thêm vào dataset (tùy chọn)
                # os.remove(img_path)
                # os.remove(label_path)
        
        print(f"Đã cập nhật dataset với {len(train_images)} ảnh train và {len(val_images)} ảnh validation")
    
    def create_data_yaml(self):
        """Tạo hoặc cập nhật file data.yaml cho YOLOv8"""
        yaml_content = f"""
# YOLOv8 dataset config
path: {str(self.dataset_dir)}
train: train/images
val: val/images

# Classes
names:
"""
        
        # Thêm thông tin về các lớp
        for cls_id, cls_name in self.classes.items():
            yaml_content += f"  {cls_id}: {cls_name}\n"
        
        # Ghi ra file
        with open(self.dataset_dir / 'data.yaml', 'w') as f:
            f.write(yaml_content)
        
        print(f"Đã tạo/cập nhật file data.yaml tại {self.dataset_dir / 'data.yaml'}")
    
    def train_model(self, epochs=20, batch_size=16, device='0'):
        """
        Huấn luyện model với dữ liệu mới
        
        Args:
            epochs: Số lượng epochs
            batch_size: Kích thước batch
            device: GPU device (0, 1, 2, etc.) hoặc 'cpu'
        """
        yaml_path = self.dataset_dir / 'data.yaml'
        if not yaml_path.exists():
            self.create_data_yaml()
        
        # Sử dụng model hiện tại làm pretrained
        model = YOLO(self.model_path)
        
        # Huấn luyện model
        results = model.train(
            data=str(yaml_path),
            epochs=epochs,
            imgsz=640,
            batch=batch_size,
            patience=5,
            device=device,
            project='runs/train',
            name=f'active_learning_{len(os.listdir("runs/train")) + 1}',
            exist_ok=True,
            verbose=True
        )
        
        print(f"Đã huấn luyện xong model. Kết quả được lưu tại {results.save_dir}")
        
        # Cập nhật model hiện tại
        self.model_path = str(Path(results.save_dir) / 'weights' / 'best.pt')
        self.model = YOLO(self.model_path)
        
        return results
    
    def run_active_learning_cycle(self, train_after_update=True):
        """
        Chạy một chu kỳ active learning hoàn chỉnh
        
        Args:
            train_after_update: Có huấn luyện lại model sau khi cập nhật dataset không
        """
        print("=== Bắt đầu chu kỳ Active Learning ===")
        
        # Bước 1: Thu thập dữ liệu chưa gán nhãn
        print("\n1. Thu thập dữ liệu chưa gán nhãn")
        self.collect_unlabeled_data()
        
        # Bước 2: Chạy pseudo-labeling
        print("\n2. Chạy pseudo-labeling với dữ liệu chưa gán nhãn")
        self.run_pseudo_labeling()
        
        # Bước 3: Hiển thị thông báo cần gán nhãn thủ công
        manual_count = len(list(self.manual_review_dir.glob('*.jpg')))
        print(f"\n3. Bạn cần gán nhãn thủ công cho {manual_count} ảnh trong thư mục {self.manual_review_dir}")
        print("   Sau khi gán nhãn xong, hãy tiếp tục với bước tiếp theo.")
        
        # Tạm dừng để người dùng gán nhãn thủ công
        input("\nNhấn Enter sau khi đã gán nhãn thủ công xong...")
        
        # Bước 4: Cập nhật dataset
        print("\n4. Cập nhật dataset với dữ liệu đã gán nhãn")
        self.update_dataset()
        
        # Bước 5: Huấn luyện lại model (tùy chọn)
        if train_after_update:
            print("\n5. Huấn luyện lại model với dữ liệu mới")
            self.train_model()
        
        print("\n=== Hoàn tất chu kỳ Active Learning ===")

def main():
    """Hàm chính demo quy trình Active Learning"""
    manager = ActiveLearningManager()
    
    while True:
        print("\n=== QUẢN LÝ QUY TRÌNH ACTIVE LEARNING ===")
        print("1. Thu thập dữ liệu chưa gán nhãn")
        print("2. Chạy pseudo-labeling")
        print("3. Cập nhật dataset với dữ liệu đã gán nhãn")
        print("4. Huấn luyện lại model")
        print("5. Chạy một chu kỳ active learning hoàn chỉnh")
        print("0. Thoát")
        
        choice = input("\nChọn chức năng (0-5): ")
        
        if choice == '1':
            manager.collect_unlabeled_data()
        elif choice == '2':
            manager.run_pseudo_labeling()
        elif choice == '3':
            manager.update_dataset()
        elif choice == '4':
            manager.train_model()
        elif choice == '5':
            manager.run_active_learning_cycle()
        elif choice == '0':
            break
        else:
            print("Lựa chọn không hợp lệ, vui lòng thử lại.")

if __name__ == "__main__":
    main() 