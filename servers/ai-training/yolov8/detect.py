import cv2
import numpy as np
import os
from ultralytics import YOLO
from pathlib import Path

class YOLOv8Detector:
    """Lớp nhận diện đối tượng sử dụng YOLOv8"""
    
    def __init__(self, model_path=None, conf_threshold=0.25):
        """
        Khởi tạo detector với model đã huấn luyện
        
        Args:
            model_path: Đường dẫn đến model, mặc định là model tốt nhất trong runs/train
            conf_threshold: Ngưỡng tin cậy cho việc phát hiện
        """
        self.conf_threshold = conf_threshold
        
        # Tìm model mới nhất nếu không được cung cấp
        if model_path is None:
            try:
                exp_dirs = [d for d in os.listdir('runs/train') 
                           if os.path.isdir(os.path.join('runs/train', d))]
                if not exp_dirs:
                    # Sử dụng model pretrained nếu không tìm thấy model đã huấn luyện
                    model_path = 'yolov8n.pt'
                    print(f"Không tìm thấy model đã huấn luyện, sử dụng {model_path}")
                else:
                    latest_exp = max(exp_dirs, key=lambda x: os.path.getmtime(os.path.join('runs/train', x)))
                    model_path = os.path.join('runs/train', latest_exp, 'weights', 'best.pt')
                    
                    if not os.path.exists(model_path):
                        model_path = os.path.join('runs/train', latest_exp, 'weights', 'last.pt')
                    
                    print(f"Sử dụng model từ {model_path}")
            except Exception as e:
                model_path = 'yolov8n.pt'
                print(f"Lỗi khi tìm model: {e}, sử dụng {model_path}")
        
        # Tải model
        self.model = YOLO(model_path)
        
        # Tải danh sách lớp
        self.class_names = self.model.names
        print(f"Đã tải model với {len(self.class_names)} lớp: {self.class_names}")
    
    def detect(self, frame):
        """
        Phát hiện đối tượng trong khung hình
        
        Args:
            frame: Khung hình BGR từ OpenCV
            
        Returns:
            frame_with_boxes: Khung hình đã vẽ bounding box
            detections: Danh sách các phát hiện
        """
        # Chạy inference
        results = self.model(frame, conf=self.conf_threshold)
        
        # Vẽ kết quả lên frame
        frame_with_boxes = frame.copy()
        
        detections = []
        
        # Xử lý từng kết quả phát hiện
        for result in results:
            boxes = result.boxes
            
            for box in boxes:
                # Tọa độ và kích thước box
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                
                # Chỉ số lớp và độ tin cậy
                cls_id = int(box.cls[0].item())
                conf = box.conf[0].item()
                
                # Tên lớp
                class_name = self.class_names[cls_id]
                
                # Vẽ box và nhãn
                cv2.rectangle(frame_with_boxes, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Nhãn với tên lớp và độ tin cậy
                label = f"{class_name}: {conf:.2f}"
                cv2.putText(
                    frame_with_boxes, 
                    label, 
                    (x1, y1 - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.5, 
                    (0, 255, 0), 
                    2
                )
                
                # Thêm vào danh sách phát hiện
                detections.append({
                    "class_id": cls_id,
                    "class_name": class_name,
                    "confidence": conf,
                    "box": [x1, y1, x2, y2]
                })
        
        return frame_with_boxes, detections

def test_on_image(detector, image_path):
    """Test detector trên một hình ảnh và hiển thị kết quả"""
    img = cv2.imread(image_path)
    if img is None:
        print(f"Không thể đọc hình ảnh từ {image_path}")
        return
    
    # Phát hiện đối tượng
    result_img, detections = detector.detect(img)
    
    # In kết quả
    print(f"Phát hiện {len(detections)} đối tượng:")
    for i, det in enumerate(detections):
        print(f"  {i+1}. {det['class_name']} ({det['confidence']:.2f}): {det['box']}")
    
    # Hiển thị hoặc lưu kết quả
    output_dir = "runs/detect"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, os.path.basename(image_path))
    cv2.imwrite(output_path, result_img)
    
    print(f"Đã lưu kết quả vào {output_path}")

def main():
    """Hàm chính để chạy thử nghiệm phát hiện đối tượng"""
    print("=== Khởi tạo YOLOv8 detector ===")
    detector = YOLOv8Detector()
    
    # Tìm một số hình ảnh để test
    data_dir = Path("../data")
    image_files = list(data_dir.glob("*.jpg"))[:5]  # Lấy 5 ảnh đầu tiên để test
    
    if not image_files:
        print(f"Không tìm thấy hình ảnh nào trong {data_dir}")
        return
    
    print(f"=== Test trên {len(image_files)} hình ảnh ===")
    for img_path in image_files:
        print(f"\nPhát hiện đối tượng trong {img_path}:")
        test_on_image(detector, str(img_path))
    
    print("\n=== Hoàn tất demo phát hiện đối tượng ===")

if __name__ == "__main__":
    main() 