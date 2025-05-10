# Hướng dẫn gán nhãn (Annotation Guide)

Tài liệu này hướng dẫn cách gán nhãn thủ công cho hình ảnh phục vụ quá trình Active Learning và Pseudo-Labeling trong YOLOv8.

## Quy trình làm việc

Trong quy trình Active Learning, bạn sẽ nhận được các hình ảnh cần gán nhãn thủ công trong thư mục `manual_review`. Đây là các hình ảnh mà mô hình chưa thể nhận diện với độ tin cậy cao.

### Các bước thực hiện:

1. Tìm các hình ảnh trong thư mục `manual_review`
2. Sử dụng công cụ gán nhãn để đánh dấu các đối tượng
3. Lưu file nhãn ở định dạng YOLOv8

## Định dạng nhãn YOLOv8

YOLOv8 sử dụng định dạng nhãn như sau:

```
<class_id> <x_center> <y_center> <width> <height>
```

Trong đó:
- `class_id`: ID của lớp đối tượng (0, 1, 2, ...)
- `x_center`, `y_center`: Tọa độ tâm của bounding box (đã chuẩn hóa từ 0-1)
- `width`, `height`: Kích thước của bounding box (đã chuẩn hóa từ 0-1)

Ví dụ:
```
0 0.5 0.5 0.3 0.4
1 0.2 0.7 0.1 0.2
```

## Các lớp đối tượng

Danh sách các lớp đối tượng cần gán nhãn:

| ID | Tên lớp    | Mô tả                                    |
|----|------------|------------------------------------------|
| 0  | box        | Hộp, thùng carton, hộp đóng gói          |
| 1  | container  | Container, thùng chứa lớn                |
| 2  | package    | Gói hàng, kiện hàng, bưu kiện            |

## Công cụ gán nhãn

Bạn có thể sử dụng một trong các công cụ sau để gán nhãn:

### 1. LabelImg

[LabelImg](https://github.com/heartexlabs/labelImg) là công cụ gán nhãn đơn giản và phổ biến.

Cài đặt:
```bash
pip install labelImg
```

Sử dụng:
```bash
labelImg path/to/manual_review path/to/classes.txt yolo
```

### 2. CVAT (Computer Vision Annotation Tool)

[CVAT](https://github.com/opencv/cvat) là công cụ gán nhãn mạnh mẽ hơn với giao diện web.

### 3. Roboflow

[Roboflow](https://roboflow.com/) cung cấp nền tảng đám mây để gán nhãn và quản lý dữ liệu.

## Hướng dẫn gán nhãn hiệu quả

1. **Chọn bounding box chính xác:**
   - Vẽ box bao quanh toàn bộ đối tượng, không quá lớn hoặc quá nhỏ
   - Đảm bảo box không bị che khuất phần lớn đối tượng

2. **Xử lý các trường hợp đặc biệt:**
   - Đối tượng bị che khuất một phần: vẽ bounding box cho phần nhìn thấy
   - Nhiều đối tượng chồng lên nhau: cố gắng gán nhãn cho từng đối tượng riêng biệt

3. **Lưu ý về tập tin:**
   - Đặt tên file nhãn trùng với tên file ảnh (chỉ khác phần mở rộng)
   - Ví dụ: image1.jpg sẽ có file nhãn là image1.txt

## Kiểm tra dữ liệu đã gán nhãn

Bạn có thể sử dụng script kiểm tra sau để xác minh các nhãn đã gán:

```python
import os
import cv2
import glob
from pathlib import Path

def visualize_labels(image_path, label_path):
    # Đọc ảnh
    img = cv2.imread(image_path)
    height, width, _ = img.shape
    
    # Đọc file nhãn
    with open(label_path, 'r') as f:
        lines = f.readlines()
    
    # Màu cho các lớp khác nhau (BGR)
    colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0)]
    
    # Vẽ bounding boxes
    for line in lines:
        values = line.strip().split()
        if len(values) != 5:
            continue
            
        class_id, x_center, y_center, w, h = map(float, values)
        class_id = int(class_id)
        
        # Chuyển đổi từ tọa độ chuẩn hóa sang pixel
        x1 = int((x_center - w/2) * width)
        y1 = int((y_center - h/2) * height)
        x2 = int((x_center + w/2) * width)
        y2 = int((y_center + h/2) * height)
        
        # Vẽ box
        color = colors[class_id % len(colors)]
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        
        # Vẽ nhãn
        label = f"Class {class_id}"
        cv2.putText(img, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    # Hiển thị ảnh
    cv2.imshow("Labeled Image", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
```

## Quá trình Pseudo-Labeling

Các ảnh được pseudo-label tự động (có độ tin cậy ≥ 0.8) được lưu trong thư mục `pseudo_labeled`. Nếu thời gian cho phép, bạn nên kiểm tra ngẫu nhiên một số ảnh trong thư mục này để đảm bảo chất lượng của nhãn tự động.

## Cập nhật Dataset

Sau khi hoàn tất việc gán nhãn thủ công, quay lại quy trình Active Learning để cập nhật dataset và tiếp tục huấn luyện mô hình. 