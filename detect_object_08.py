import cv2
import numpy as np
import requests
import time

# Thông tin RTSP camera
RTSP_URL = "rtsp://admin:Soncave1!@192.168.1.27:554/streaming/channels/101/"
API_URL = "http://192.168.1.168:7000/ics/taskOrder/addTask"

# Counter và biến trạng thái
order_count = 0
nhan_dien = 1  # Biến nhận diện: 1 nếu có hàng, 0 nếu không (đặt ban đầu là 1 để kiểm tra)
last_nhan_dien = None  # Lưu trạng thái trước để kiểm tra thay đổi
last_detection_time = 0  # Thời điểm phát hiện cuối cùng (giây)
last_send_time = 0  # Thời điểm gửi lệnh cuối cùng (giây)

# Toạ độ bounding box cố định (vị trí kiện hàng)
bbox_x1, bbox_y1 = 530, 370
bbox_x2, bbox_y2 = 660, 460

def has_red_or_orange(bgr_crop):
    hsv_crop = cv2.cvtColor(bgr_crop, cv2.COLOR_BGR2HSV)
    
    # Ngưỡng màu đỏ
    red_lower1 = np.array([0, 70, 50])
    red_upper1 = np.array([10, 255, 255])
    red_lower2 = np.array([160, 70, 50])
    red_upper2 = np.array([180, 255, 255])
    
    # Ngưỡng màu cam
    orange_lower = np.array([10, 100, 100])
    orange_upper = np.array([25, 255, 255])
    
    # Tạo mask cho màu đỏ và cam
    mask_red = cv2.inRange(hsv_crop, red_lower1, red_upper1) | cv2.inRange(hsv_crop, red_lower2, red_upper2)
    mask_orange = cv2.inRange(hsv_crop, orange_lower, orange_upper)

    # Đếm pixel đỏ hoặc cam
    red_or_orange_pixels = cv2.countNonZero(mask_red) + cv2.countNonZero(mask_orange)
    total_pixels = bgr_crop.shape[0] * bgr_crop.shape[1]
    
    return red_or_orange_pixels / total_pixels > 0.15  # điều chỉnh ngưỡng nếu cần

def send_task_order(order_id):
    data = {
        "modelProcessCode": "office_test",
        "fromSystem": "MS_2",
        "orderId": f"sha275_{order_id}",
        "taskOrderDetail": [{"taskPath": "10000015"}]
    }
    try:
        response = requests.post(API_URL, json=data, timeout=5)
        print(f"✅ Sent task sha256_{order_id}, status: {response.status_code}")
    except requests.RequestException as e:
        print(f"❌ Error sending data: {e}")

def main():
    global order_count, nhan_dien, last_nhan_dien, last_detection_time, last_send_time
    cap = cv2.VideoCapture(RTSP_URL)

    if not cap.isOpened():
        print("⚠️ Cannot open RTSP stream.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            nhan_dien = 0
            print("⚠️ Mất tín hiệu camera.")
            print("Không có hàng")
            print("0")
            continue

        # Cắt vùng cần kiểm tra từ bounding box cố định
        crop = frame[bbox_y1:bbox_y2, bbox_x1:bbox_x2]
        if crop.size == 0:
            print("⚠️ Vùng bounding box không hợp lệ.")
            continue

        # Kiểm tra màu đỏ hoặc cam trong vùng
        current_nhan_dien = 1 if has_red_or_orange(crop) else 0

        # Vẽ bounding box và nhãn
        color = (0, 255, 0) if current_nhan_dien else (0, 0, 255)
        cv2.rectangle(frame, (bbox_x1, bbox_y1), (bbox_x2, bbox_y2), color, 2)
        label = "CO HANG" if current_nhan_dien else "KHONG CO HANG"
        cv2.putText(frame, label, (bbox_x1, bbox_y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # In thông báo
        if current_nhan_dien == 1:
            print("Red/Orange bag detected in bounding box.")
            print("1")
        else:
            print("Không có hàng")
            print("0")

        # Chỉ cập nhật nhan_dien nếu đã qua 3 giây kể từ lần thay đổi trước
        current_time = time.time()
        if current_time - last_detection_time >= 3:
            nhan_dien = current_nhan_dien
            last_detection_time = current_time

        # Gửi lệnh khi nhan_dien chuyển từ 0 thành 1
        if (last_nhan_dien is None or (last_nhan_dien == 0 and nhan_dien == 1)) and current_time - last_send_time >= 3:
            order_count += 1
            order_id = f"142857_{order_count}"
            send_task_order(order_id)
            last_send_time = current_time  # Cập nhật thời điểm gửi lệnh cuối cùng
        last_nhan_dien = nhan_dien

        # Hiển thị khung hình
        cv2.imshow("Camera", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()