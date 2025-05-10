# YOLOv8 - Nhận diện hàng hóa

Module này sử dụng YOLOv8 để huấn luyện mô hình phát hiện hàng hóa (box, container, package) từ hình ảnh camera.

## Cấu trúc thư mục

```
yolov8/
├── README.md             # File này
├── dataset_setup.py      # Script chuẩn bị dữ liệu
├── train.py              # Script huấn luyện mô hình
├── detect.py             # Script nhận diện đối tượng
├── active_learning.py    # Script quản lý active learning
├── annotation_guide.md   # Hướng dẫn gán nhãn
├── datasets/             # Thư mục chứa dữ liệu đã chuẩn bị
├── unlabeled/            # Thư mục chứa ảnh chưa gán nhãn
├── pseudo_labeled/       # Thư mục chứa ảnh đã pseudo-label
├── manual_review/        # Thư mục chứa ảnh cần review thủ công
└── runs/                 # Thư mục chứa kết quả huấn luyện và phát hiện
```

## Cài đặt

1. Chuẩn bị môi trường:

```bash
# Tạo môi trường ảo (nếu chưa có)
python -m venv yolo_env

# Kích hoạt môi trường ảo
# Windows:
yolo_env\Scripts\activate
# Linux/Mac:
# source yolo_env/bin/activate

# Cài đặt các thư viện cần thiết
pip install -r requirements.txt
```

## Quy trình cơ bản

### 1. Chuẩn bị dữ liệu

Chạy script `dataset_setup.py` để chuẩn bị dữ liệu từ thư mục `data` vào cấu trúc phù hợp cho YOLOv8:

```bash
python dataset_setup.py
```

Script này sẽ:
- Tạo cấu trúc thư mục cho dataset (train/val/test)
- Tạo file `data.yaml` cần thiết cho YOLOv8
- Copy các hình ảnh từ thư mục `data` vào các thư mục tương ứng
- Tạo các file nhãn giả cho mục đích demo

### 2. Huấn luyện mô hình

Chạy script `train.py` để huấn luyện mô hình YOLOv8:

```bash
python train.py
```

Script này sẽ:
- Sử dụng file `yolov8n.pt` làm pretrained model
- Huấn luyện trên dataset đã chuẩn bị
- Lưu mô hình tốt nhất vào thư mục `runs/train`
- Xuất mô hình sang định dạng ONNX cho inference nhanh hơn

### 3. Nhận diện đối tượng

Chạy script `detect.py` để thử nghiệm nhận diện đối tượng:

```bash
python detect.py
```

Script này sẽ:
- Tải mô hình đã huấn luyện hoặc pretrained model
- Thực hiện nhận diện trên một số hình ảnh trong thư mục `data`
- Hiển thị và lưu kết quả vào thư mục `runs/detect`

## Quy trình Active Learning

### Giới thiệu

Module này triển khai quy trình active learning và pseudo-labeling để cải thiện mô hình theo thời gian với lượng nhãn thủ công tối thiểu.

### Quy trình hoạt động

1. **Bắt đầu với tập dữ liệu ban đầu** - Gán nhãn thủ công cho khoảng 100 ảnh
2. **Huấn luyện mô hình ban đầu** - Huấn luyện mô hình với dữ liệu đã gán nhãn
3. **Vòng lặp Active Learning**:
   - Thu thập ảnh mới chưa có nhãn
   - Chạy inference với mô hình hiện tại
   - Tự động gán nhãn (pseudo-labeling) cho các dự đoán có confidence ≥ 0.8
   - Đánh dấu ảnh có confidence < 0.8 để gán nhãn thủ công
   - Kết hợp dữ liệu mới với dữ liệu cũ
   - Huấn luyện lại mô hình

### Sử dụng Active Learning

Chạy script `active_learning.py` để bắt đầu quy trình:

```bash
python active_learning.py
```

Khi chạy, script sẽ hiển thị menu tương tác:

```
=== QUẢN LÝ QUY TRÌNH ACTIVE LEARNING ===
1. Thu thập dữ liệu chưa gán nhãn
2. Chạy pseudo-labeling
3. Cập nhật dataset với dữ liệu đã gán nhãn
4. Huấn luyện lại model
5. Chạy một chu kỳ active learning hoàn chỉnh
0. Thoát
```

Bạn có thể chọn thực hiện từng bước hoặc chạy toàn bộ quy trình.

### Gán nhãn thủ công

Khi cần gán nhãn thủ công:

1. Mở thư mục `manual_review` để xem các ảnh cần gán nhãn
2. Sử dụng công cụ gán nhãn như LabelImg để tạo file nhãn
3. Lưu file nhãn với cùng tên file ảnh (chỉ khác phần mở rộng .txt)
4. Xem chi tiết hơn trong file `annotation_guide.md`

## Tích hợp vào hệ thống

Để tích hợp vào hệ thống chính, bạn có thể:

1. Sao chép mô hình đã huấn luyện vào thư mục phù hợp
2. Import lớp `YOLOv8Detector` từ `detect.py` vào mã nguồn chính
3. Khởi tạo detector và sử dụng phương thức `detect()` để phát hiện đối tượng

Ví dụ:

```python
from detect import YOLOv8Detector

# Khởi tạo detector với model đã huấn luyện
detector = YOLOv8Detector(model_path="path/to/best.pt")

# Phát hiện đối tượng trong frame
frame = ... # Đọc frame từ camera
result_frame, detections = detector.detect(frame)
```

## Chú ý

- Active learning là quá trình lặp đi lặp lại để cải thiện mô hình theo thời gian
- Ngưỡng confidence 0.8 cho pseudo-labeling có thể điều chỉnh tùy theo nhu cầu
- Kiểm tra ngẫu nhiên các nhãn tự động để đảm bảo chất lượng
- Mô hình sẽ cải thiện hiệu suất khi có thêm dữ liệu đa dạng
- Định kỳ đánh giá mô hình trên tập test để kiểm tra sự cải thiện 