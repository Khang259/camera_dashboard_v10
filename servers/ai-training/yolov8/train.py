import os
from ultralytics import YOLO
import yaml
import shutil

def train_model():
    """Huấn luyện mô hình YOLOv8 với dataset đã chuẩn bị"""
    # Kiểm tra xem dataset đã được chuẩn bị chưa
    dataset_path = os.path.join('datasets', 'items')
    yaml_path = os.path.join(dataset_path, 'data.yaml')
    
    if not os.path.exists(yaml_path):
        print(f"Không tìm thấy file data.yaml tại {yaml_path}")
        print("Vui lòng chạy dataset_setup.py trước")
        return
    
    # Đọc thông tin từ file YAML
    with open(yaml_path, 'r') as f:
        data_config = yaml.safe_load(f)
    
    # Số lượng lớp cần phát hiện
    num_classes = len(data_config.get('names', {}))
    print(f"Huấn luyện mô hình phát hiện {num_classes} lớp đối tượng")
    
    # Tạo thư mục lưu kết quả
    os.makedirs('runs/train', exist_ok=True)
    
    # Copy model YOLOv8n.pt từ thư mục gốc nếu cần
    if not os.path.exists('yolov8n.pt'):
        try:
            shutil.copy2('../../yolov8n.pt', 'yolov8n.pt')
            print("Đã copy file yolov8n.pt từ thư mục gốc")
        except FileNotFoundError:
            print("Không tìm thấy file yolov8n.pt, mô hình sẽ được tải từ internet")
    
    # Thiết lập mô hình YOLOv8 
    model = YOLO('yolov8n.pt')  # Sử dụng mô hình YOLOv8 Nano làm pretrained
    
    # Huấn luyện mô hình
    results = model.train(
        data=yaml_path,         # Đường dẫn đến file data.yaml
        epochs=50,              # Số lượng epochs
        imgsz=640,              # Kích thước ảnh đầu vào
        batch=16,               # Kích thước batch
        patience=10,            # Early stopping patience
        device='0',             # GPU device (0, 1, 2, etc.) hoặc 'cpu'
        project='runs/train',   # Thư mục lưu kết quả
        name='exp',             # Tên thử nghiệm
        exist_ok=True,          # Ghi đè lên thư mục exp nếu đã tồn tại
        verbose=True            # In thông tin chi tiết
    )
    
    print(f"Đã huấn luyện xong mô hình. Kết quả được lưu tại {results.save_dir}")
    return results

def export_model(results=None):
    """Xuất mô hình đã huấn luyện sang các định dạng khác nhau"""
    # Nếu không có kết quả, tìm mô hình mới nhất
    if results is None:
        # Tìm mô hình mới nhất trong thư mục runs/train
        try:
            exp_dirs = [d for d in os.listdir('runs/train') if os.path.isdir(os.path.join('runs/train', d))]
            latest_exp = max(exp_dirs, key=lambda x: os.path.getmtime(os.path.join('runs/train', x)))
            model_path = os.path.join('runs/train', latest_exp, 'weights', 'best.pt')
            
            if not os.path.exists(model_path):
                model_path = os.path.join('runs/train', latest_exp, 'weights', 'last.pt')
            
            if not os.path.exists(model_path):
                print("Không tìm thấy mô hình đã huấn luyện")
                return
                
            print(f"Sử dụng mô hình từ {model_path}")
            model = YOLO(model_path)
        except (FileNotFoundError, ValueError):
            print("Không tìm thấy thư mục huấn luyện hoặc mô hình")
            return
    else:
        # Sử dụng mô hình từ kết quả huấn luyện
        model = YOLO(results.best if hasattr(results, 'best') else results.last)
    
    # Xuất mô hình sang định dạng ONNX (cho inference nhanh hơn)
    onnx_path = os.path.join('runs', 'export', 'model.onnx')
    os.makedirs(os.path.dirname(onnx_path), exist_ok=True)
    
    try:
        model.export(format='onnx', imgsz=640)
        print(f"Đã xuất mô hình sang định dạng ONNX tại {onnx_path}")
    except Exception as e:
        print(f"Lỗi xuất mô hình: {e}")

def main():
    """Hàm chính để huấn luyện và xuất mô hình"""
    print("=== Bắt đầu huấn luyện mô hình YOLOv8 ===")
    results = train_model()
    
    if results:
        print("=== Bắt đầu xuất mô hình ===")
        export_model(results)
    else:
        print("Huấn luyện không thành công, không xuất mô hình")
    
    print("=== Hoàn tất quá trình huấn luyện ===")

if __name__ == "__main__":
    main() 