import cv2
import numpy as np
import os
from ultralytics import YOLO
from pathlib import Path
from config import logger

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
                yolo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'servers', 'ai-training', 'yolov8'))
                model_dir = os.path.join(yolo_path, 'runs/train')
                
                if os.path.exists(model_dir):
                    exp_dirs = [d for d in os.listdir(model_dir) if os.path.isdir(os.path.join(model_dir, d))]
                    if exp_dirs:
                        latest_exp = max(exp_dirs, key=lambda x: os.path.getmtime(os.path.join(model_dir, x)))
                        model_path = os.path.join(model_dir, latest_exp, 'weights', 'best.pt')
                        
                        if not os.path.exists(model_path):
                            model_path = os.path.join(model_dir, latest_exp, 'weights', 'last.pt')
                        
                        logger.info(f"Sử dụng model từ {model_path}")
                    else:
                        model_path = 'yolov8n.pt'
                        logger.info(f"Không tìm thấy model đã huấn luyện, sử dụng {model_path}")
                else:
                    model_path = 'yolov8n.pt'
                    logger.info(f"Không tìm thấy thư mục train, sử dụng {model_path}")
            except Exception as e:
                model_path = 'yolov8n.pt'
                logger.error(f"Lỗi khi tìm model: {e}, sử dụng {model_path}")
        
        # Tải model
        try:
            self.model = YOLO(model_path)
            self.class_names = self.model.names
            logger.info(f"Đã tải model với {len(self.class_names)} lớp: {self.class_names}")
        except Exception as e:
            logger.error(f"Lỗi khi tải model: {e}")
            raise
    
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