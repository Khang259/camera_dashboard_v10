import cv2
import numpy as np
import mediapipe as mp
import requests
import av
import time
from aiortc import VideoStreamTrack
from config import (
    logger,
    FRAME_RATE,
    FRAME_WIDTH,
    FRAME_HEIGHT,
    BUFFER_SIZE,
    VIDEO_FOURCC,
    DETECTION_INTERVAL,
    VIDEO_TIME_BASE,
    PTS_INCREMENT,
)

class HandDetector:
    """Detect hands in video frames using MediaPipe."""
    
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.mp_draw = mp.solutions.drawing_utils

    def detect_hands(self, frame):
        height, width, _ = frame.shape
        logger.debug(f"Processing frame with dimensions: {width}x{height}")
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        try:
            results = self.hands.process(rgb_frame)
        except Exception as e:
            logger.error(f"Error processing frame with MediaPipe: {e}")
            return frame, [], []

        bounding_boxes = []
        hand_details = []

        if results.multi_hand_landmarks:
            logger.info(f"Detected {len(results.multi_hand_landmarks)} hand(s) in frame")
            for hand_landmarks in results.multi_hand_landmarks:
                try:
                    x_min = min(landmark.x for landmark in hand_landmarks.landmark)
                    y_min = min(landmark.y for landmark in hand_landmarks.landmark)
                    x_max = max(landmark.x for landmark in hand_landmarks.landmark)
                    y_max = max(landmark.y for landmark in hand_landmarks.landmark)

                    x_min_px = int(x_min * width)
                    y_min_px = int(y_min * height)
                    x_max_px = int(x_max * width)
                    y_max_px = int(y_max * height)

                    cv2.rectangle(frame, (x_min_px, y_min_px), (x_max_px, y_max_px), (0, 255, 0), 2)

                    logger.debug(f"Detected hand at position ({x_min_px}, {y_min_px}, {x_max_px}, {y_max_px})")

                    bounding_boxes.append({
                        "x": x_min * 100,
                        "y": y_min * 100,
                        "width": (x_max - x_min) * 100,
                        "height": (y_max - y_min) * 100,
                        "label": "Hand",
                        "confidence": 0.95,
                    })

                    hand_details.append({
                        "x_min_px": x_min_px,
                        "y_min_px": y_min_px,
                        "x_max_px": x_max_px,
                        "y_max_px": y_max_px,
                    })

                    self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                except Exception as e:
                    logger.error(f"Error processing hand landmarks: {e}")
                    continue

        else:
            logger.debug("No hands detected in frame")

        return frame, bounding_boxes, hand_details

class RTSPVideoStreamTrack(VideoStreamTrack):
    """Stream video from an RTSP source with hand detection."""
    
    kind = "video"
    TASK_ORDER_ENDPOINT = "http://192.168.1.168:7000/ics/taskOrder/addTask"

    def __init__(self, rtsp_url, camera_id):
        super().__init__()
        self.camera_id = camera_id
        self.cap = self._initialize_capture(rtsp_url)
        self.detector = HandDetector()
        self.frame_count = 0
        self.pts = 0
        self.order_count = 0  # Khởi tạo order_count

    def _initialize_capture(self, rtsp_url):
        cap = cv2.VideoCapture(rtsp_url + "?tcp", cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, BUFFER_SIZE)
        cap.set(cv2.CAP_PROP_FOURCC, VIDEO_FOURCC)
        cap.set(cv2.CAP_PROP_FPS, FRAME_RATE)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        if not cap.isOpened():
            raise Exception(f"Failed to open RTSP stream for camera {self.camera_id}")
        return cap

    def _reconnect(self):
        self.cap.release()
        self.cap = self._initialize_capture(self.cap.get(cv2.CAP_PROP_POS_AVI_RATIO))
        ret, _ = self.cap.read()
        if not ret:
            raise Exception(f"Failed to reconnect RTSP stream for camera {self.camera_id}")

    async def _send_task_order(self):
        self.order_count += 1
        data = {
            "modelProcessCode": "office_test",
            "fromSystem": "MS_2",
            "orderId": f"142857_{self.order_count}",
            "taskOrderDetail": [
                {
                    "taskPath": "10000015"
                }
            ]
        }
        try:
            logger.info(f"Camera {self.camera_id}: Preparing to send task order: {data}")
            response = requests.post(self.TASK_ORDER_ENDPOINT, json=data, timeout=5)
            if response.status_code == 200:
                logger.info(f"Camera {self.camera_id}: Task order sent successfully: {data}")
            else:
                logger.error(f"Camera {self.camera_id}: Error sending task order: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Camera {self.camera_id}: Error sending task order request: {e}")

    async def recv(self):
        ret, frame = self.cap.read()
        if not ret:
            logger.error(f"Camera {self.camera_id}: Failed to read frame, reconnecting...")
            self._reconnect()
            ret, frame = self.cap.read()
            if not ret:
                raise Exception(f"Failed to reconnect RTSP stream for camera {self.camera_id}")

        self.frame_count += 1
        bounding_boxes = []
        hand_details = []
        if self.frame_count % DETECTION_INTERVAL == 0:
            try:
                frame, bounding_boxes, hand_details = self.detector.detect_hands(frame)
                logger.debug(f"Camera {self.camera_id}: Detected {len(bounding_boxes)} bounding boxes and {len(hand_details)} hand details")
            except Exception as e:
                logger.error(f"Camera {self.camera_id}: Error in detect_hands: {e}")
                bounding_boxes = []
                hand_details = []

        # Gửi task order ngay khi phát hiện bàn tay
        if len(bounding_boxes) > 0:
            logger.info(f"Camera {self.camera_id}: Hand detected, sending task order")
            await self._send_task_order()

        # Convert to YUV420P and create AV frame
        try:
            frame_yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV_I420)
            height, width = frame.shape[:2]
            av_frame = av.VideoFrame(width=width, height=height, format="yuv420p")

            planes = frame_yuv.reshape((height * 3 // 2, width))
            av_frame.planes[0].update(planes[:height])
            av_frame.planes[1].update(planes[height : height + height // 4].reshape(height // 2, width // 2))
            av_frame.planes[2].update(planes[height + height // 4 :].reshape(height // 2, width // 2))

            av_frame.pts = self.pts
            av_frame.time_base = VIDEO_TIME_BASE
            self.pts += PTS_INCREMENT
        except Exception as e:
            logger.error(f"Camera {self.camera_id}: Error creating AV frame: {e}")
            raise

        return av_frame