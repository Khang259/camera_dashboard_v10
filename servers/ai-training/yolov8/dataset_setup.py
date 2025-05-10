import os
import shutil
import random
from pathlib import Path

# Đường dẫn dữ liệu nguồn và đích
SOURCE_DATA_DIR = '../data'
DEST_DATA_DIR = 'datasets/items'

# Danh sách các lớp cần phát hiện
CLASSES = ["box", "container", "package"]

def create_dataset_structure():
    """Tạo cấu trúc thư mục cho dataset YOLOv8"""
    # Tạo thư mục chính và thư mục con
    for split in ['train', 'val', 'test']:
        for subdir in ['images', 'labels']:
            os.makedirs(os.path.join(DEST_DATA_DIR, split, subdir), exist_ok=True)
    
    # Tạo file classes.txt
    with open(os.path.join(DEST_DATA_DIR, 'classes.txt'), 'w') as f:
        for cls in CLASSES:
            f.write(f"{cls}\n")
    
    print(f"Đã tạo cấu trúc thư mục cho dataset tại {DEST_DATA_DIR}")

def create_data_yaml():
    """Tạo file data.yaml cho YOLOv8"""
    yaml_content = f"""
# YOLOv8 dataset config
path: {DEST_DATA_DIR}
train: train/images
val: val/images
test: test/images

# Classes
names:
"""
    
    for i, cls in enumerate(CLASSES):
        yaml_content += f"  {i}: {cls}\n"
    
    with open(os.path.join(DEST_DATA_DIR, 'data.yaml'), 'w') as f:
        f.write(yaml_content)
    
    print(f"Đã tạo file data.yaml tại {DEST_DATA_DIR}/data.yaml")

def copy_sample_images():
    """Copy các hình ảnh mẫu từ thư mục data vào dataset"""
    source_path = Path(SOURCE_DATA_DIR)
    image_files = list(source_path.glob('*.jpg'))
    
    if not image_files:
        print(f"Không tìm thấy hình ảnh nào trong {SOURCE_DATA_DIR}")
        return
    
    # Chia tỷ lệ train:val:test = 70:20:10
    random.shuffle(image_files)
    n_files = len(image_files)
    train_end = int(n_files * 0.7)
    val_end = int(n_files * 0.9)
    
    train_files = image_files[:train_end]
    val_files = image_files[train_end:val_end]
    test_files = image_files[val_end:]
    
    # Copy files vào thư mục tương ứng
    for split, files in [('train', train_files), ('val', val_files), ('test', test_files)]:
        for file in files:
            destination = os.path.join(DEST_DATA_DIR, split, 'images', file.name)
            shutil.copy2(file, destination)
            
            # Tạo file label giả cho mục đích demo (sẽ cần annotation thật sau)
            # Format: class_id x_center y_center width height
            with open(os.path.join(DEST_DATA_DIR, split, 'labels', file.stem + '.txt'), 'w') as f:
                # Giả lập một bounding box ở giữa hình
                cls_id = random.randint(0, len(CLASSES) - 1)
                f.write(f"{cls_id} 0.5 0.5 0.3 0.3\n")
    
    print(f"Đã copy {len(train_files)} hình train, {len(val_files)} hình val, {len(test_files)} hình test")

def main():
    print("=== Bắt đầu thiết lập dataset YOLOv8 ===")
    create_dataset_structure()
    create_data_yaml()
    copy_sample_images()
    print("=== Hoàn tất thiết lập dataset YOLOv8 ===")

if __name__ == "__main__":
    main() 