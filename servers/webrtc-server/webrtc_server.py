import asyncio
import cv2
import json
import websockets
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack, RTCConfiguration, RTCIceServer, RTCIceCandidate
import mediapipe as mp
import numpy as np
import logging
import time
import os
import requests
import av
from fractions import Fraction

# Tắt log MediaPipe không cần thiết
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
with open("../config.json", "r") as f:
    config = json.load(f)
    SIGNALING_SERVER = config["signaling_server_url"]
    DETECT_SERVER_URL = config["detect_server_url"]
    cameras = config["cameras"]

# Hàm phân tích chuỗi candidate (giữ nguyên)
def parse_candidate(candidate_str):
    parts = candidate_str.split()
    if len(parts) < 8:
        raise ValueError(f"Invalid candidate string: {candidate_str}")

    candidate_info = {
        "foundation": parts[0],
        "component": int(parts[1]),
        "protocol": parts[2].lower(),
        "priority": int(parts[3]),
        "ip": parts[4],
        "port": int(parts[5]),
        "type": parts[7],
    }

    for i in range(8, len(parts), 2):
        if i + 1 < len(parts):
            key = parts[i]
            value = parts[i + 1]
            if key == "raddr":
                candidate_info["relatedAddress"] = value
            elif key == "rport":
                candidate_info["relatedPort"] = int(value)
            elif key == "generation":
                candidate_info["generation"] = int(value)
            elif key == "ufrag":
                candidate_info["usernameFragment"] = value

    return candidate_info

# HandDetector class (giữ nguyên)
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
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        bounding_boxes = []

        if results.multi_hand_landmarks:
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

# RTSPVideoStreamTrack class (cập nhật)
class RTSPVideoStreamTrack(VideoStreamTrack):
    kind = "video"

    def __init__(self, rtsp_url, camera_id):
        super().__init__()
        self.cap = cv2.VideoCapture(rtsp_url + "?tcp", cv2.CAP_FFMPEG)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 10)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'H264'))
        self.cap.set(cv2.CAP_PROP_FPS, 15)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
        self.camera_id = camera_id
        if not self.cap.isOpened():
            raise Exception(f"Failed to open RTSP stream for camera {camera_id}")
        self.detector = HandDetector()
        self.last_sent_time = 0
        self.frame_count = 0
        self.pts = 0  # Presentation timestamp
        self.time_base = Fraction(1, 90000)  # Thời gian cơ số cho video

    async def recv(self):
        ret, frame = self.cap.read()
        if not ret:
            logger.error(f"Failed to read frame for camera {self.camera_id}, reconnecting...")
            self.cap.release()
            self.cap = cv2.VideoCapture(self.cap.get(cv2.CAP_PROP_POS_AVI_RATIO) + "?tcp", cv2.CAP_FFMPEG)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 10)
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'H264'))
            self.cap.set(cv2.CAP_PROP_FPS, 15)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
            ret, frame = self.cap.read()
            if not ret:
                raise Exception(f"Failed to reconnect RTSP stream for camera {self.camera_id}")

        self.frame_count += 1
        bounding_boxes = []
        if self.frame_count % 5 == 0:
            frame, bounding_boxes = self.detector.detect_hands(frame)

        for box in bounding_boxes:
            h, w, _ = frame.shape
            x_min_px = int(box["x"] * w / 100)
            y_min_px = int(box["y"] * h / 100)
            x_max_px = int((box["x"] + box["width"]) * w / 100)
            y_max_px = int((box["y"] + box["height"]) * h / 100)

            if self.detector.is_hand_in_center(frame, x_min_px, y_min_px, x_max_px, y_max_px):
                current_time = time.time()
                if current_time - self.last_sent_time > 5:
                    data = {
                        "event": "hand_in_center",
                        "timestamp": current_time,
                        "camera_id": self.camera_id,
                    }
                    try:
                        response = requests.post(f"{DETECT_SERVER_URL}/testing_endpoint", json=data, timeout=5)
                        if response.status_code == 200:
                            logger.info(f"Data sent successfully: {data}")
                            self.last_sent_time = current_time
                        else:
                            logger.error(f"Error sending data: {response.status_code} - {response.text}")
                    except Exception as e:
                        logger.error(f"Error sending request: {str(e)}")

        # Chuyển frame sang định dạng YUV_I420 và tạo av.Frame
        frame_yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV_I420)
        height, width = frame.shape[:2]
        
        # Tạo av.Frame
        av_frame = av.VideoFrame(width=width, height=height, format="yuv420p")
        
        # Sao chép dữ liệu YUV từ NumPy array vào av.Frame
        planes = frame_yuv.reshape((height * 3 // 2, width))
        av_frame.planes[0].update(planes[:height])  # Y plane
        av_frame.planes[1].update(planes[height:height + height // 4].reshape(height // 2, width // 2))  # U plane
        av_frame.planes[2].update(planes[height + height // 4:].reshape(height // 2, width // 2))  # V plane

        # Gán timestamp
        av_frame.pts = self.pts
        av_frame.time_base = self.time_base
        self.pts += int(90000 / 15)  # Tăng PTS dựa trên FPS (15 fps)

        return av_frame

async def run_webrtc_server():
    pcs = {}
    max_retries = 5
    retry_delay = 5

    async def connect_websocket():
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to connect to Signaling Server ({attempt + 1}/{max_retries})")
                async with websockets.connect(SIGNALING_SERVER, ping_interval=20, ping_timeout=60) as ws:
                    logger.info("Connected to Signaling Server")
                    initial_message = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
                    logger.info(f"Received initial message: {initial_message}")

                    server_id = initial_message.get("id") if initial_message.get("type") == "id" else None
                    if server_id is None:
                        logger.error("Invalid initial message format, missing 'id' or 'type'")
                        continue
                    logger.info(f"WebRTC Server ID: {server_id}")

                    await ws.send(json.dumps({"type": "register", "role": "webrtc-server"}))
                    logger.info("Registered as webrtc-server")

                    async def send_to_signaling(data):
                        await ws.send(json.dumps(data))
                        logger.info(f"Sent message to Signaling Server: {data}")

                    async def handle_signaling():
                        async for message in ws:
                            try:
                                data = json.loads(message)
                                logger.info(f"Received message: {data}")

                                if data.get("type") == "offer":
                                    camera_id = data.get("cameraId")
                                    client_id = data.get("clientId")
                                    if not camera_id or not client_id:
                                        logger.error("Missing cameraId or clientId in offer")
                                        continue

                                    pc = RTCPeerConnection(RTCConfiguration(iceServers=[
                                        RTCIceServer(urls="stun:stun.l.google.com:19302"),
                                        RTCIceServer(urls="turn:openrelay.metered.ca:80", username="openrelayproject", credential="openrelayproject"),
                                        RTCIceServer(urls="turn:openrelay.metered.ca:443", username="openrelayproject", credential="openrelayproject")
                                    ]))
                                    pcs[camera_id] = pc
                                    camera = next((cam for cam in cameras if cam["id"] == camera_id), None)
                                    if not camera:
                                        logger.error(f"Camera {camera_id} not found")
                                        continue

                                    try:
                                        video_track = RTSPVideoStreamTrack(camera["rtsp_url"], camera_id)
                                        pc.addTrack(video_track)
                                        logger.info(f"Added video track for camera {camera_id}")
                                    except Exception as e:
                                        logger.error(f"Failed to add video track for camera {camera_id}: {str(e)}")
                                        continue

                                    pc.onicecandidate = lambda candidate: asyncio.ensure_future(
                                        send_to_signaling({
                                            "type": "candidate",
                                            "candidate": {
                                                "candidate": candidate.candidate,
                                                "sdpMid": candidate.sdp_mid,
                                                "sdpMLineIndex": candidate.sdp_mline_index,
                                                "usernameFragment": candidate.username_fragment
                                            },
                                            "clientId": client_id,
                                            "cameraId": camera_id,
                                            "target": client_id,
                                        })
                                    )

                                    pc.onconnectionstatechange = lambda: logger.info(
                                        f"Connection state for camera {camera_id}: {pc.connectionState}"
                                    )

                                    await pc.setRemoteDescription(RTCSessionDescription(sdp=data["sdp"], type="offer"))
                                    logger.info(f"Set remote description for camera {camera_id}")
                                    answer = await pc.createAnswer()
                                    await pc.setLocalDescription(answer)
                                    await send_to_signaling({
                                        "type": "answer",
                                        "sdp": answer.sdp,
                                        "clientId": client_id,
                                        "cameraId": camera_id,
                                        "target": client_id,
                                    })
                                    logger.info(f"Sent answer for camera {camera_id} to client {client_id}")

                                elif data.get("type") == "candidate":
                                    camera_id = data.get("cameraId")
                                    if camera_id in pcs:
                                        candidate = data["candidate"]
                                        try:
                                            candidate_info = parse_candidate(candidate["candidate"])
                                            ice_candidate = RTCIceCandidate(
                                                foundation=candidate_info["foundation"],
                                                component=candidate_info["component"],
                                                protocol=candidate_info["protocol"],
                                                priority=candidate_info["priority"],
                                                ip=candidate_info["ip"],
                                                port=candidate_info["port"],
                                                type=candidate_info["type"],
                                                relatedAddress=candidate_info.get("relatedAddress"),
                                                relatedPort=candidate_info.get("relatedPort"),
                                                sdpMid=candidate["sdpMid"],
                                                sdpMLineIndex=candidate["sdpMLineIndex"]
                                            )
                                            await pcs[camera_id].addIceCandidate(ice_candidate)
                                            logger.info(f"Added ICE candidate for camera {camera_id}")
                                        except Exception as e:
                                            logger.error(f"Failed to add ICE candidate for camera {camera_id}: {str(e)}")

                            except Exception as e:
                                logger.error(f"Error processing message: {str(e)}")

                    await handle_signaling()
            except Exception as e:
                logger.error(f"Connection failed: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    raise Exception("Could not connect to Signaling Server")

    await connect_websocket()

if __name__ == "__main__":
    asyncio.run(run_webrtc_server())