from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import cv2
import mediapipe as mp
import numpy as np
import asyncio
import json
import logging
import requests
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load configuration
with open("../config.json", "r") as f:
    config = json.load(f)
    cameras = config["cameras"]
    DETECT_SERVER_URL = config["detect_server_url"]  # For video_feed endpoint

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HandDetector class from main.py
class HandDetector:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils

    def detect_hands(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        bounding_boxes = []

        if results.multi_hand_landmarks:
            h, w, _ = frame.shape
            for hand_landmarks in results.multi_hand_landmarks:
                x_min = min([landmark.x for landmark in hand_landmarks.landmark])
                y_min = min([landmark.y for landmark in hand_landmarks.landmark])
                x_max = max([landmark.x for landmark in hand_landmarks.landmark])
                y_max = max([landmark.y for landmark in hand_landmarks.landmark])

                x_min_px = int(x_min * w)
                y_min_px = int(y_min * h)
                x_max_px = int(x_max * w)
                y_max_px = int(y_max * h)

                cv2.rectangle(frame, (x_min_px, y_min_px), (x_max_px, y_max_px), (0, 255, 0), 2)

                bounding_boxes.append({
                    "x": x_min * 100,
                    "y": y_min * 100,
                    "width": (x_max - x_min) * 100,
                    "height": (y_max - y_min) * 100,
                    "label": "Hand",
                    "confidence": 0.95
                })

                self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

        return frame, bounding_boxes

    def is_hand_in_center(self, frame, x_min, y_min, x_max, y_max):
        h, w, _ = frame.shape
        center_x = w // 2
        center_y = h // 2
        center_width = int(w * 0.3)
        center_height = int(h * 0.3)

        center_x_min = center_x - center_width // 2
        center_y_min = center_y - center_height // 2
        center_x_max = center_x + center_width // 2
        center_y_max = center_y + center_height // 2

        return (x_min >= center_x_min and x_max <= center_x_max and
                y_min >= center_y_min and y_max <= center_y_max)

# Global camera instance
cap = None
detector = HandDetector()

def get_camera(rtsp_url):
    global cap
    try:
        if cap is None or not cap.isOpened():
            logger.info(f"Connecting to camera at: {rtsp_url}")
            cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'H264'))
            cap.set(cv2.CAP_PROP_FPS, 30)
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 60000)

            if not cap.isOpened():
                logger.error("Failed to open camera")
                raise Exception("Failed to open camera")

            ret, frame = cap.read()
            if not ret or frame is None:
                logger.error("Failed to read frame from camera")
                raise Exception("Failed to read frame from camera")

            logger.info("Camera connected successfully")
            return cap
    except Exception as e:
        logger.error(f"Error connecting to camera: {str(e)}")
        if cap is not None:
            cap.release()
            cap = None
        raise HTTPException(status_code=500, detail=f"Camera connection error: {str(e)}")
    return cap

def generate_frames(rtsp_url, camera_id):
    try:
        camera = get_camera(rtsp_url)
        logger.info("Starting frame streaming")
        last_sent_time = 0

        while True:
            try:
                ret, frame = camera.read()
                if not ret or frame is None:
                    logger.error("Failed to read frame, reconnecting...")
                    camera = get_camera(rtsp_url)
                    continue

                frame = cv2.flip(frame, 1)
                frame, bounding_boxes = detector.detect_hands(frame)

                for box in bounding_boxes:
                    h, w, _ = frame.shape
                    x_min_px = int(box["x"] * w / 100)
                    y_min_px = int(box["y"] * h / 100)
                    x_max_px = int((box["x"] + box["width"]) * w / 100)
                    y_max_px = int((box["y"] + box["height"]) * h / 100)

                    if detector.is_hand_in_center(frame, x_min_px, y_min_px, x_max_px, y_max_px):
                        current_time = time.time()
                        if current_time - last_sent_time > 5:
                            data = {
                                "event": "hand_in_center",
                                "timestamp": current_time,
                                "camera_id": camera_id,
                            }
                            try:
                                response = requests.post(f"{DETECT_SERVER_URL}/testing_endpoint", json=data, timeout=5)
                                if response.status_code == 200:
                                    logger.info(f"Data sent successfully: {data}")
                                    last_sent_time = current_time
                                else:
                                    logger.error(f"Error sending data: {response.status_code} - {response.text}")
                            except Exception as e:
                                logger.error(f"Error sending request: {str(e)}")

                ret, buffer = cv2.imencode('.jpg', frame)
                if not ret:
                    logger.error("Failed to encode frame")
                    continue

                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

                time.sleep(0.033)  # ~30 FPS
            except Exception as e:
                logger.error(f"Error generating frame: {str(e)}")
                time.sleep(1)
                continue
    except Exception as e:
        logger.error(f"Critical error in generate_frames: {str(e)}")
        raise Exception(str(e))

# APIs from main.py
@app.get("/api/cameras/{camera_id}/stream")
async def get_camera_stream(camera_id: str):
    camera = next((cam for cam in cameras if cam["id"] == camera_id), None)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    try:
        logger.info(f"Stream request for camera {camera_id}")
        camera = get_camera(camera["rtsp_url"])
        logger.info(f"Stream for camera {camera_id} ready")
        return {
            "streamUrl": f"{DETECT_SERVER_URL}/video_feed/{camera_id}",
            "cameraId": camera_id,
            "status": "connected"
        }
    except Exception as e:
        logger.error(f"Error getting stream for camera {camera_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Camera error: {str(e)}")

@app.get("/video_feed/{camera_id}")
async def video_feed(camera_id: str):
    camera = next((cam for cam in cameras if cam["id"] == camera_id), None)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    return StreamingResponse(
        generate_frames(camera["rtsp_url"], camera_id),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/test_image")
async def test_image():
    frame = cv2.imread("test.jpg")
    if frame is None:
        raise HTTPException(status_code=404, detail="Test image not found")
    ret, buffer = cv2.imencode('.jpg', frame)
    return Response(content=buffer.tobytes(), media_type="image/jpeg")

@app.post("/testing_endpoint")
async def testing_endpoint(data: dict):
    logger.info(f"Received testing endpoint data: {data}")
    return {"status": "received", "data": data}

# Existing APIs from utils_server.py
@app.get("/api/cameras")
async def get_cameras():
    return {"cameras": cameras}

@app.get("/api/cameras/{camera_id}/status")
async def check_camera_status(camera_id: str):
    camera = next((cam for cam in cameras if cam["id"] == camera_id), None)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    try:
        cap = cv2.VideoCapture(camera["rtsp_url"], cv2.CAP_FFMPEG)
        if not cap.isOpened():
            raise Exception("Failed to connect")
        ret, _ = cap.read()
        cap.release()
        return {"camera_id": camera_id, "status": "connected" if ret else "disconnected"}
    except Exception as e:
        logger.error(f"Error checking camera {camera_id}: {str(e)}")
        return {"camera_id": camera_id, "status": "disconnected", "error": str(e)}

@app.post("/api/cameras")
async def add_camera(camera: dict):
    cameras.append(camera)
    with open("../config.json", "w") as f:
        json.dump(config, f, indent=2)
    return {"message": "Camera added", "camera": camera}

@app.get("/api/config")
async def get_config():
    return config

@app.on_event("shutdown")
async def shutdown_event():
    global cap
    if cap is not None:
        cap.release()
        cap = None
        logger.info("Camera released")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7000)