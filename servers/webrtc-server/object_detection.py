import cv2
import numpy as np
import av
import time
import os
import sys
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

# Import YOLOv8Detector từ module detector.py local
try:
    from detector import YOLOv8Detector
    HAS_YOLO = True
    logger.info("Đã load YOLOv8Detector từ module local")
except ImportError as e:
    HAS_YOLO = False
    logger.warning(f"Không thể import YOLOv8Detector: {e}. Không sử dụng chức năng nhận diện đối tượng.")


class ObjectDetector:
    """Detect objects using YOLOv8."""
    
    def __init__(self):
        # Cố gắng tải YOLOv8Detector nếu có
        if HAS_YOLO:
            try:
                self.detector = YOLOv8Detector()
                logger.info("Đã khởi tạo YOLOv8Detector thành công")
            except Exception as e:
                logger.error(f"Lỗi khi tải YOLOv8Detector: {e}")
                HAS_YOLO = False
    
    def detect_objects(self, frame):
        """Detect objects in the frame."""
        if not HAS_YOLO:
            return frame, []
        
        try:
            frame_with_boxes, detections = self.detector.detect(frame)
            logger.debug(f"Detected {len(detections)} objects")
            return frame_with_boxes, detections
        except Exception as e:
            logger.error(f"Error in object detection: {e}")
            return frame, []


class RTSPVideoStreamTrack(VideoStreamTrack):
    """Stream video from an RTSP source with object detection."""
    
    kind = "video"

    def __init__(self, rtsp_url, camera_id):
        super().__init__()
        self.camera_id = camera_id
        self.cap = self._initialize_capture(rtsp_url)
        self.object_detector = ObjectDetector() if HAS_YOLO else None
        self.frame_count = 0
        self.pts = 0

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
        
        # Phát hiện đối tượng mỗi DETECTION_INTERVAL frame
        if self.frame_count % DETECTION_INTERVAL == 0 and self.object_detector and HAS_YOLO:
            try:
                frame, object_detections = self.object_detector.detect_objects(frame)
                # Chuyển đổi định dạng phát hiện YOLOv8 sang định dạng bounding_boxes
                for det in object_detections:
                    x1, y1, x2, y2 = det["box"]
                    width = x2 - x1
                    height = y2 - y1
                    bounding_boxes.append({
                        "x": x1 / frame.shape[1] * 100,
                        "y": y1 / frame.shape[0] * 100,
                        "width": width / frame.shape[1] * 100,
                        "height": height / frame.shape[0] * 100,
                        "label": det["class_name"],
                        "confidence": det["confidence"],
                    })
                logger.debug(f"Camera {self.camera_id}: Detected {len(object_detections)} objects with YOLOv8")
            except Exception as e:
                logger.error(f"Camera {self.camera_id}: Error in detect_objects: {e}")

        # Ghi log khi phát hiện đối tượng
        if len(bounding_boxes) > 0:
            logger.info(f"Camera {self.camera_id}: Detected {len(bounding_boxes)} objects in frame")

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