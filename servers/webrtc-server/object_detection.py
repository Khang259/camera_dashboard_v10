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
    VIDEO_TIME_BASE,
    PTS_INCREMENT,
)

class RTSPVideoStreamTrack(VideoStreamTrack):
    """Stream video from an RTSP source."""
    
    kind = "video"

    def __init__(self, rtsp_url, camera_id):
        super().__init__()
        self.camera_id = camera_id
        self.cap = self._initialize_capture(rtsp_url)
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