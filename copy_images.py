import os
import shutil
import rarfile
import tempfile

# Đường dẫn thư mục nguồn và đích
source_dir = r"D:/Honda/Data-cargo_3/Data"
dest_dir = r"D:/Honda/camera_dashboard_v10/ai-training/data"

# Đảm bảo thư mục đích tồn tại
if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)

# Danh sách định dạng ảnh cần tìm
image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')

# Hàm tìm và copy ảnh từ một thư mục
def find_and_copy_images(src, dst):
    copied_files = 0
    for root, dirs, files in os.walk(src):
        for file in files:
            if file.lower().endswith(image_extensions):
                src_file = os.path.join(root, file)
                dst_file = os.path.join(dst, file)
                
                # Xử lý trường hợp trùng tên file
                base, ext = os.path.splitext(file)
                counter = 1
                while os.path.exists(dst_file):
                    new_filename = f"{base}_{counter}{ext}"
                    dst_file = os.path.join(dst, new_filename)
                    counter += 1
                
                try:
                    shutil.copy2(src_file, dst_file)
                    copied_files += 1
                    print(f"Đã copy: {src_file} -> {dst_file}")
                except Exception as e:
                    print(f"Lỗi khi copy {src_file}: {e}")
    
    return copied_files

# Hàm giải nén file .rar và tìm ảnh
def extract_rar_and_find_images(rar_path, temp_dir, dst):
    copied_files = 0
    try:
        with rarfile.RarFile(rar_path) as rf:
            # Giải nén file .rar vào thư mục tạm
            rf.extractall(temp_dir)
            print(f"Đã giải nén: {rar_path} vào {temp_dir}")
            # Tìm và copy ảnh từ thư mục tạm
            copied_files = find_and_copy_images(temp_dir, dst)
    except Exception as e:
        print(f"Lỗi khi giải nén {rar_path}: {e}")
    return copied_files

# Hàm chính để duyệt thư mục và xử lý
def process_directory(src, dst):
    total_copied = 0
    # Tạo thư mục tạm để giải nén .rar
    with tempfile.TemporaryDirectory() as temp_dir:
        for root, dirs, files in os.walk(src):
            for file in files:
                file_path = os.path.join(root, file)
                if file.lower().endswith('.rar'):
                    # Xử lý file .rar
                    total_copied += extract_rar_and_find_images(file_path, temp_dir, dst)
                elif file.lower().endswith(image_extensions):
                    # Xử lý file ảnh trực tiếp
                    dst_file = os.path.join(dst, file)
                    base, ext = os.path.splitext(file)
                    counter = 1
                    while os.path.exists(dst_file):
                        new_filename = f"{base}_{counter}{ext}"
                        dst_file = os.path.join(dst, new_filename)
                        counter += 1
                    try:
                        shutil.copy2(file_path, dst_file)
                        total_copied += 1
                        print(f"Đã copy: {file_path} -> {dst_file}")
                    except Exception as e:
                        print(f"Lỗi khi copy {file_path}: {e}")
    
    return total_copied

# Thực thi script
print("Bắt đầu tìm, giải nén và copy ảnh...")
total_copied = process_directory(source_dir, dest_dir)
print(f"Hoàn tất! Đã copy {total_copied} file ảnh.")