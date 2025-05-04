import cv2
import mediapipe as mp
import numpy as np
from typing import List, Tuple
import asyncio
import json
import base64
from fastapi import FastAPI, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
import time
import logging
import requests

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả origins trong môi trường development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HandDetector:
    def __init__(self):
        # Khởi tạo MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,  # Nhận diện tối đa 2 bàn tay
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils

    def detect_hands(self, frame):
        # Chuyển đổi khung hình sang RGB vì MediaPipe yêu cầu
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        bounding_boxes = []

        if results.multi_hand_landmarks:
            h, w, _ = frame.shape
            for hand_landmarks in results.multi_hand_landmarks:
                # Tính toán bounding box từ các landmark
                x_min = min([landmark.x for landmark in hand_landmarks.landmark])
                y_min = min([landmark.y for landmark in hand_landmarks.landmark])
                x_max = max([landmark.x for landmark in hand_landmarks.landmark])
                y_max = max([landmark.y for landmark in hand_landmarks.landmark])

                # Chuyển đổi sang tọa độ pixel
                x_min_px = int(x_min * w)
                y_min_px = int(y_min * h)
                x_max_px = int(x_max * w)
                y_max_px = int(y_max * h)

                # Vẽ bounding box lên khung hình
                cv2.rectangle(frame, (x_min_px, y_min_px), (x_max_px, y_max_px), (0, 255, 0), 2)

                # Thêm thông tin bounding box vào danh sách
                bounding_boxes.append({
                    "x": x_min * 100,  # Chuyển sang phần trăm
                    "y": y_min * 100,
                    "width": (x_max - x_min) * 100,
                    "height": (y_max - y_min) * 100,
                    "label": "Hand",
                    "confidence": 0.95  # Giá trị giả định
                })

                # Vẽ các điểm landmark (tùy chọn)
                self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

        return frame, bounding_boxes

    def is_hand_in_center(self, frame, x_min, y_min, x_max, y_max):
        h, w, _ = frame.shape
        center_x = w // 2
        center_y = h // 2
        center_width = int(w * 0.3)  # 30% chiều rộng
        center_height = int(h * 0.3)  # 30% chiều cao

        # Tọa độ vùng trung tâm
        center_x_min = center_x - center_width // 2
        center_y_min = center_y - center_height // 2
        center_x_max = center_x + center_width // 2
        center_y_max = center_y + center_height // 2

        # Kiểm tra xem bounding box của tay có nằm hoàn toàn trong vùng trung tâm không
        return (x_min >= center_x_min and x_max <= center_x_max and
                y_min >= center_y_min and y_max <= center_y_max)

# Khởi tạo camera và detector
cap = None
detector = HandDetector()
camera_id = "camera_1"  # Định danh camera

def get_camera():
    global cap
    try:
        if cap is None or not cap.isOpened():
            rtsp_url = "rtsp://admin:admin@192.168.1.109:1935"
            logger.info(f"Bắt đầu kết nối camera tại: {rtsp_url}")
            
            # Thử kết nối với các tùy chọn khác nhau
            cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
            
            # Cấu hình các tham số RTSP
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)  # Tăng bộ đệm
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'H264'))
            cap.set(cv2.CAP_PROP_FPS, 30)
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 60000)  # Thời gian chờ 60 giây
            
            # Kiểm tra kết nối
            if not cap.isOpened():
                logger.error("Không thể mở camera")
                raise Exception("Không thể mở camera")
            
            # Đọc một frame để kiểm tra
            ret, frame = cap.read()
            if not ret or frame is None:
                logger.error("Không thể đọc frame từ camera")
                raise Exception("Không thể đọc frame từ camera")
            
            logger.info("Kết nối camera thành công")
            return cap
            
    except Exception as e:
        logger.error(f"Error connecting to camera: {str(e)}")
        if cap is not None:
            cap.release()
            cap = None
        raise HTTPException(status_code=500, detail=f"Camera connection error: {str(e)}")
    
    return cap

def generate_frames():
    try:
        camera = get_camera()
        logger.info("Bắt đầu tạo luồng frame từ camera")
        last_sent_time = 0  # Thời gian gửi dữ liệu lần cuối
        
        while True:
            try:
                ret, frame = camera.read()
                if not ret or frame is None:
                    logger.error("Không thể đọc frame, đang thử kết nối lại...")
                    camera = get_camera()  # Thử kết nối lại
                    continue
                
                frame = cv2.flip(frame, 1)
                frame, bounding_boxes = detector.detect_hands(frame)
                
                for box in bounding_boxes:
                    # Chuyển đổi từ phần trăm về pixel để kiểm tra
                    h, w, _ = frame.shape
                    x_min_px = int(box["x"] * w / 100)
                    y_min_px = int(box["y"] * h / 100)
                    x_max_px = int((box["x"] + box["width"]) * w / 100)
                    y_max_px = int((box["y"] + box["height"]) * h / 100)

                    if detector.is_hand_in_center(frame, x_min_px, y_min_px, x_max_px, y_max_px):
                        current_time = time.time()
                        # Chỉ gửi dữ liệu mỗi 5 giây để tránh spam
                        if current_time - last_sent_time > 5:
                            # Gửi dữ liệu JSON
                            data = {
                                "event": "hand_in_center",
                                "timestamp": current_time,
                                "camera_id": camera_id,
                            }
                            try:
                                response = requests.post("http://192.168.1.108:7000/testing_endpoint", json=data, timeout=5)
                                if response.status_code == 200:
                                    logger.info(f"Dữ liệu đã được gửi thành công: {data}")
                                    last_sent_time = current_time
                                else:
                                    logger.error(f"Lỗi khi gửi dữ liệu: {response.status_code} - {response.text}")
                            except Exception as e:
                                logger.error(f"Lỗi khi gửi yêu cầu: {str(e)}")

                ret, buffer = cv2.imencode('.jpg', frame)
                if not ret:
                    logger.error("Không thể mã hóa frame")
                    continue
                
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
                # Thêm độ trễ để giới hạn tốc độ khung hình (~30 FPS)
                time.sleep(0.033)
                
            except Exception as e:
                logger.error(f"Lỗi khi tạo frame: {str(e)}")
                logger.info("Đang thử sửa lỗi bằng cách tiếp tục vòng lặp")
                time.sleep(1)  # Đợi trước khi thử lại
                continue
                
    except Exception as e:
        logger.error(f"Lỗi nghiêm trọng trong generate_frames: {str(e)}")
        raise Exception(str(e))

@app.get("/api/cameras/{camera_id}/stream")
async def get_camera_stream(camera_id: str):
    try:
        logger.info(f"Yêu cầu stream từ camera {camera_id}")
        camera = get_camera()
        logger.info(f"Stream từ camera {camera_id} sẵn sàng")
        return {
            "streamUrl": f"http://192.168.1.108:8000/video_feed/{camera_id}",
            "cameraId": camera_id,
            "status": "connected"
        }
    except Exception as e:
        logger.error(f"Lỗi khi lấy stream camera {camera_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi camera: {str(e)}")

@app.get("/video_feed/{camera_id}")
async def video_feed(camera_id: str):
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/test_image")
async def test_image():
    frame = cv2.imread("test.jpg")
    ret, buffer = cv2.imencode('.jpg', frame)
    return Response(content=buffer.tobytes(), media_type="image/jpeg")

@app.on_event("shutdown")
async def shutdown_event():
    global cap
    if cap is not None:
        cap.release()
        cap = None
        logger.info("Camera released")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)