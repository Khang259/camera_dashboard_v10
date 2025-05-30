import cv2
import numpy as np
import requests
import threading
import time
import json
import queue
import ffmpeg
import logging

# Thiết lập logging
logging.basicConfig(filename='rtsp_reader.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Danh sách bounding box
bboxes_27 = [
    (420, 474, 538, 609),   # 10000160
    (652, 454, 849, 575),   # 10000161
    (947, 445, 1174, 562),  # 10000162
    (1276, 434, 1495, 562), # 10000163
    (1603, 429, 1756, 537)  # 10000164
]

bboxes_28 = [
    (1139, 635, 1318, 728), # 10000146
    (1170, 849, 1385, 968), # 10000234
    (860, 388, 976, 460)    # 10000147
]

bboxes_29 = [
    (983, 255, 1108, 420),  # 10000141
    (1306, 250, 1420, 430), # 10000140
    (964, 580, 1110, 742),  # 10000171
    (1293, 578, 1424, 742), # 10000170
    (666, 576, 777, 728)    # 10000172
]

# Ánh xạ bounding box với taskPath
bbox_to_taskpath = {
    (420, 474, 538, 609): "10000160",
    (652, 454, 849, 575): "10000161",
    (947, 445, 1174, 562): "10000162",
    (1276, 434, 1495, 562): "10000163",
    (1603, 429, 1756, 537): "10000164",
    (1139, 635, 1318, 728): "10000146",
    (1170, 849, 1385, 968): "10000234",
    (860, 388, 976, 460): "10000147",
    (983, 255, 1108, 420): "10000141",
    (1306, 250, 1420, 430): "10000140",
    (964, 580, 1110, 742): "10000171",
    (1293, 578, 1424, 742): "10000170",
    (666, 576, 777, 728): "10000172"
}

# Danh sách start_task_path và end_task_path
start_task_paths = ["10000160", "10000161", "10000162", "10000163", "10000172", "10000234", "10000146"]
end_task_paths = ["10000170", "10000171", "10000140", "10000141", "10000164"]

# Ràng buộc start_task_path và end_task_path
task_path_constraints = {
    "10000170": ["10000160", "10000161", "10000162", "10000163"],
    "10000171": ["10000160", "10000161", "10000162", "10000163"],
    "10000140": ["10000160", "10000161", "10000162", "10000163"],
    "10000141": ["10000160", "10000161", "10000162", "10000163"],
    "10000164": ["10000234", "10000146"],
    "10000147": ["10000172"]
}

# Danh sách ánh xạ bounding box cho từng camera
bboxes_list = [bboxes_27, bboxes_28, bboxes_29]

# URL API
api_url = "http://192.168.1.169:7000/ics/taskOrder/addTask"

# Danh sách URL RTSP
rtsp_urls = [
    "rtsp://admin:Soncave1!@192.168.1.27:554/streaming/channels/101",
    "rtsp://admin:Soncave1!@192.168.1.28:554/streaming/channels/101",
    "rtsp://admin:Soncave1!@192.168.1.29:554/streaming/channels/101"
]

# Hàm gửi POST request
def send_post_request(start_task_path, end_task_path, camera_idx, bbox_idx):
    json_data = {
        "modelProcessCode": "checking_camera_work",
        "fromSystem": "testing_one",
        "orderId": f"thado_1_1_{int(time.time())}",
        "taskOrderDetail": [
            {
                "taskPath": f"{start_task_path},{end_task_path}"
            }
        ]
    }
    try:
        response = requests.post(api_url, json=json_data, timeout=5)
        logging.info(f"[Camera {camera_idx + 1}] Gửi POST request cho Bounding box {bbox_idx + 1}:")
        logging.info(f"  - Status code: {response.status_code}")
        logging.info(f"  - Response: {response.text}")
        print(f"\n[Camera {camera_idx + 1}] Gửi POST request cho Bounding box {bbox_idx + 1}:")
        print(f"  - Status code: {response.status_code}")
        print(f"  - Response: {response.text}")
    except requests.exceptions.RequestException as e:
        logging.error(f"[Camera {camera_idx + 1}] Lỗi khi gửi POST request: {e}")
        print(f"\n[Camera {camera_idx + 1}] Lỗi khi gửi POST request: {e}")

# Hàm đọc luồng RTSP và đưa frame vào queue
def read_rtsp_stream(rtsp_url, frame_queue, camera_idx, width=1920, height=1080, stop_event=None):
    while not (stop_event and stop_event.is_set()):
        try:
            process = (
                ffmpeg
                .input(rtsp_url, rtsp_transport='tcp', rtsp_flags='prefer_tcp', buffer_size=500000, max_delay=500000, timeout=5000000)
                .output('pipe:', format='rawvideo', pix_fmt='bgr24', loglevel='error')
                .run_async(pipe_stdout=True)
            )
            logging.info(f"[Camera {camera_idx + 1}] Đã khởi tạo FFmpeg cho RTSP: {rtsp_url}")
            print(f"[Camera {camera_idx + 1}] Đã khởi tạo FFmpeg cho RTSP: {rtsp_url}")

            while not (stop_event and stop_event.is_set()):
                in_bytes = process.stdout.read(width * height * 3)
                if not in_bytes:
                    logging.error(f"[Camera {camera_idx + 1}] Không đọc được dữ liệu từ FFmpeg, thử kết nối lại")
                    print(f"[Camera {camera_idx + 1}] Không đọc được dữ liệu từ FFmpeg, thử kết nối lại")
                    break
                frame = np.frombuffer(in_bytes, np.uint8).reshape((height, width, 3))
                if frame is None or frame.size == 0:
                    logging.error(f"[Camera {camera_idx + 1}] Frame không hợp lệ hoặc rỗng")
                    continue
                try:
                    frame_queue.put((camera_idx, frame), timeout=1)
                    logging.debug(f"[Camera {camera_idx + 1}] Đưa frame vào queue")
                except queue.Full:
                    logging.warning(f"[Camera {camera_idx + 1}] Queue đầy, bỏ qua frame")
                time.sleep(0.01)  # Giảm tải CPU
            process.communicate()
        except Exception as e:
            logging.error(f"[Camera {camera_idx + 1}] Lỗi FFmpeg: {str(e)}, thử kết nối lại sau 1 giây")
            print(f"[Camera {camera_idx + 1}] Lỗi FFmpeg: {str(e)}, thử kết nối lại sau 1 giây")
            time.sleep(1)

# Hàm xử lý frame và phát hiện hàng hóa
def process_frame(camera_idx, frame_queue, bboxes, bbox_states, last_detection_time, post_sent, empty_end_task_paths, has_start_task_paths):
    frame_count = 0
    while True:
        try:
            cam_idx, frame = frame_queue.get(timeout=3)
            if cam_idx != camera_idx:
                continue
            frame_count += 1
            if frame_count % 3 != 0:  # Bỏ qua 3/5 frame 
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            output_frame = frame.copy()

            for idx, (x1, y1, x2, y2) in enumerate(bboxes):
                roi = gray[y1:y2, x1:x2]
                blurred = cv2.GaussianBlur(roi, (5, 5), 0)
                edges = cv2.Canny(blurred, 100, 200)
                lines = cv2.HoughLinesP(
                    edges,
                    rho=1,
                    theta=np.pi/180,
                    threshold=50,
                    minLineLength=50,
                    maxLineGap=10
                )

                task_path = bbox_to_taskpath.get((x1, y1, x2, y2), "Unknown")
                current_time = time.time()

                if lines is not None:
                    # Có hàng hóa
                    if not bbox_states[camera_idx][idx]:
                        bbox_states[camera_idx][idx] = True
                        last_detection_time[camera_idx][idx] = current_time
                        post_sent[camera_idx][idx] = False
                        logging.info(f"[Camera {camera_idx + 1}] Bounding box {idx + 1}: Có hàng")
                        logging.info(f"  - TaskPath: {task_path}")
                        print(f"\n[Camera {camera_idx + 1}] Bounding box {idx + 1}: Có hàng")
                        print(f"  - TaskPath: {task_path}")
                        
                        for i, line in enumerate(lines):
                            x1_line, y1_line, x2_line, y2_line = line[0]
                            print(f"    Đường {i + 1}: ({x1_line}, {y1_line}) -> ({x2_line}, {y2_line})")

                        # Nếu task_path thuộc start_task_paths, thêm vào has_start_task_paths
                        if task_path in start_task_paths:
                            has_start_task_paths[camera_idx].add(task_path)

                    # Vẽ đường thẳng và văn bản
                    for i, line in enumerate(lines):
                        x1_line, y1_line, x2_line, y2_line = line[0]
                        cv2.line(
                            output_frame[y1:y2, x1:x2],
                            (x1_line, y1_line),
                            (x2_line, y2_line),
                            (0, 255, 0),
                            2
                        )

                    cv2.putText(
                        output_frame,
                        "Co hang",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2
                    )
                else:
                    # Không có hàng hóa
                    if bbox_states[camera_idx][idx]:
                        bbox_states[camera_idx][idx] = False
                        post_sent[camera_idx][idx] = False
                        logging.info(f"[Camera {camera_idx + 1}] Bounding box {idx + 1}: Không có hàng")
                        logging.info(f"  - TaskPath: {task_path}")
                        print(f"\n[Camera {camera_idx + 1}] Bounding box {idx + 1}: Không có hàng")
                        print(f"  - TaskPath: {task_path}")

                        # Nếu task_path thuộc end_task_paths, thêm vào empty_end_task_paths
                        if task_path in end_task_paths:
                            empty_end_task_paths[camera_idx].add(task_path)
                        # Nếu task_path thuộc start_task_paths, xóa khỏi has_start_task_paths
                        if task_path in start_task_paths:
                            has_start_task_paths[camera_idx].discard(task_path)

                # Kiểm tra điều kiện gửi POST request
                if task_path in end_task_paths and not bbox_states[camera_idx][idx] and not post_sent[camera_idx][idx]:
                    # Điểm trong end_task_paths trống, kiểm tra start_task_paths
                    allowed_start_paths = task_path_constraints.get(task_path, [])
                    for start_camera_idx in range(len(rtsp_urls)):
                        for start_task_path in has_start_task_paths[start_camera_idx]:
                            # Kiểm tra ràng buộc start_task_path
                            if start_task_path in allowed_start_paths:
                                logging.info(f"[Camera {camera_idx + 1}] Phát hiện end_task_path {task_path} trống và start_task_path {start_task_path} có hàng")
                                print(f"\n[Camera {camera_idx + 1}] Phát hiện end_task_path {task_path} trống và start_task_path {start_task_path} có hàng")

                                def delayed_post_request():
                                    time.sleep(15)
                                    # Kiểm tra lại trạng thái sau 15 giây
                                    if task_path in empty_end_task_paths[camera_idx] and start_task_path in has_start_task_paths[start_camera_idx]:
                                        send_post_request(start_task_path, task_path, camera_idx, idx)
                                        post_sent[camera_idx][idx] = True
                                        empty_end_task_paths[camera_idx].discard(task_path)  # Xóa sau khi gửi

                                threading.Thread(target=delayed_post_request, daemon=True).start()
                                break

                cv2.rectangle(output_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

            try:
                display_queue.put((camera_idx, output_frame), timeout=1)
                logging.debug(f"[Camera {camera_idx + 1}] Đã gửi frame đã xử lý đến display queue")
            except queue.Full:
                logging.warning(f"[Camera {camera_idx + 1}] Display queue đầy, bỏ qua frame")
        except queue.Empty:
            logging.warning(f"[Camera {camera_idx + 1}] Frame queue rỗng, chờ frame mới")

# Main process
def main():
    frame_queues = [queue.Queue(maxsize=20) for _ in rtsp_urls]
    global display_queue
    display_queue = queue.Queue(maxsize=20)
    stop_event = threading.Event()

    # Khởi tạo trạng thái cho mỗi camera
    bbox_states = {i: {j: False for j in range(len(bboxes_list[i]))} for i in range(len(rtsp_urls))}
    last_detection_time = {i: {j: 0 for j in range(len(bboxes_list[i]))} for i in range(len(rtsp_urls))}
    post_sent = {i: {j: False for j in range(len(bboxes_list[i]))} for i in range(len(rtsp_urls))}
    empty_end_task_paths = {i: set() for i in range(len(rtsp_urls))}  # Lưu các end_task_path trống
    has_start_task_paths = {i: set() for i in range(len(rtsp_urls))}  # Lưu các start_task_path có hàng

    threads = []
    for i, rtsp_url in enumerate(rtsp_urls):
        t = threading.Thread(target=read_rtsp_stream, args=(rtsp_url, frame_queues[i], i, 1920, 1080, stop_event))
        t.daemon = True
        t.start()
        threads.append(t)
        logging.info(f"[Camera {i + 1}] Khởi động thread đọc RTSP")
        print(f"[Camera {i + 1}] Khởi động thread đọc RTSP")

    for i in range(len(rtsp_urls)):
        t = threading.Thread(target=process_frame, args=(i, frame_queues[i], bboxes_list[i], bbox_states, last_detection_time, post_sent, empty_end_task_paths, has_start_task_paths))
        t.daemon = True
        t.start()
        threads.append(t)
        logging.info(f"[Camera {i + 1}] Khởi động thread xử lý frame")
        print(f"[Camera {i + 1}] Khởi động thread xử lý frame")

    try:
        while not stop_event.is_set():
            try:
                camera_idx, frame = display_queue.get(timeout=1)
                output_frame_resized = cv2.resize(frame, (1920, 1080))
                cv2.imshow(f'Cargo Detection - Camera {camera_idx + 1}', output_frame_resized)
            except queue.Empty:
                pass

            if cv2.waitKey(1) & 0xFF == ord('q'):
                stop_event.set()
                break
    finally:
        for q in frame_queues:
            while not q.empty():
                q.get()
        while not display_queue.empty():
            display_queue.get()
        cv2.destroyAllWindows()
        logging.info("Đã dừng tất cả thread và đóng cửa sổ")
        print("Đã dừng tất cả thread và đóng cửa sổ")

if __name__ == '__main__':
    main()