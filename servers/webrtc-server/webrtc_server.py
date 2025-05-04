import asyncio
import cv2
import json
import websockets
from aiortc import RTCPeerConnection, VideoStreamTrack, RTCConfiguration, RTCIceServer
from aiortc.contrib.media import MediaStreamTrack
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
with open("../config.json", "r") as f:
    config = json.load(f)
    SIGNALING_SERVER = config["signaling_server_url"]
    CAMERA_RTSP_URL = config["cameras"][0]["rtsp_url"]  # Use first camera for simplicity

# VideoStreamTrack for RTSP stream
class RTSPVideoStreamTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self):
        super().__init__()
        self.cap = cv2.VideoCapture(CAMERA_RTSP_URL, cv2.CAP_FFMPEG)
        if not self.cap.isOpened():
            raise Exception("Failed to open RTSP stream")

    async def recv(self):
        ret, frame = self.cap.read()
        if not ret:
            logger.error("Failed to read frame, reconnecting...")
            self.cap.release()
            self.cap = cv2.VideoCapture(CAMERA_RTSP_URL, cv2.CAP_FFMPEG)
            ret, frame = self.cap.read()
            if not ret:
                raise Exception("Failed to reconnect RTSP stream")

        # Convert frame to YUV
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV_I420)
        return frame

async def run_webrtc_server():
    pcs = set()

    async with websockets.connect(SIGNALING_SERVER) as ws:
        # Receive server ID
        server_id = None
        initial_message = json.loads(await ws.recv())
        if initial_message["type"] == "id":
            server_id = initial_message["id"]
            logger.info(f"WebRTC Server ID: {server_id}")

        async def send_to_signaling(data):
            await ws.send(json.dumps({**data, "target": data.get("clientId")}))

        async def handle_signaling():
            async for message in ws:
                data = json.loads(message)
                logger.info(f"Received message: {data}")

                if data["type"] == "offer":
                    pc = RTCPeerConnection(RTCConfiguration(iceServers=[RTCIceServer(urls="stun:stun.l.google.com:19302")]))
                    pcs.add(pc)

                    # Add video track
                    video_track = RTSPVideoStreamTrack()
                    pc.addTrack(video_track)

                    @pc.on("icecandidate")
                    async def on_icecandidate(candidate):
                        if candidate:
                            await send_to_signaling({
                                "type": "candidate",
                                "candidate": candidate.to_sdp(),
                                "clientId": data["clientId"],
                            })

                    @pc.on("connectionstatechange")
                    async def on_connectionstatechange():
                        logger.info(f"Connection state: {pc.connectionState}")
                        if pc.connectionState == "failed":
                            await pc.close()
                            pcs.discard(pc)

                    # Process offer
                    await pc.setRemoteDescription(data["sdp"])
                    answer = await pc.createAnswer()
                    await pc.setLocalDescription(answer)

                    # Send answer
                    await send_to_signaling({
                        "type": "answer",
                        "sdp": pc.localDescription.sdp,
                        "clientId": data["clientId"],
                    })

                elif data["type"] == "candidate":
                    for pc in pcs:
                        await pc.addIceCandidate(data["candidate"])

        await handle_signaling()

if __name__ == "__main__":
    asyncio.run(run_webrtc_server())