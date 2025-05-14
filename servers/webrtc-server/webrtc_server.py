# #webrtc-server.py
# import asyncio
# import json
# import websockets
# from aiortc import (
#     RTCPeerConnection,
#     RTCSessionDescription,
#     RTCConfiguration,
#     RTCIceServer,
#     RTCIceCandidate,
# )
# from config import logger, SIGNALING_SERVER_URL, CAMERAS, RETRY_MAX_ATTEMPTS, RETRY_DELAY_SECONDS
# from object_detection import RTSPVideoStreamTrack
# import os
# from pymongo import MongoClient
# from datetime import datetime
# import logging

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# LOG_DIR = "logs"
# os.makedirs(LOG_DIR, exist_ok=True)
# log_file = os.path.join(LOG_DIR, f"requests_webrtc_server_{datetime.now().strftime('%Y%m%d')}.log")
# file_handler = logging.FileHandler(log_file)
# file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
# logger.addHandler(file_handler)

# MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
# mongo_client = MongoClient(MONGODB_URI)
# db = mongo_client["HONDA_HN"]
# collection = db["config"]

# def sync_cameras_from_mongo():
#     global CAMERAS
#     CAMERAS[:] = list(collection.find({}, {"_id": 0}))
#     logger.info("Synced CAMERAS from MongoDB")

# class CandidateParser:
#     @staticmethod
#     def parse(candidate_str):
#         parts = candidate_str.split()
#         if len(parts) < 8:
#             raise ValueError(f"Invalid candidate string: {candidate_str}")

#         candidate_info = {
#             "foundation": parts[0],
#             "component": int(parts[1]),
#             "protocol": parts[2].lower(),
#             "priority": int(parts[3]),
#             "ip": parts[4],
#             "port": int(parts[5]),
#             "type": parts[7],
#         }

#         for i in range(8, len(parts), 2):
#             if i + 1 < len(parts):
#                 key, value = parts[i], parts[i + 1]
#                 if key == "raddr":
#                     candidate_info["relatedAddress"] = value
#                 elif key == "rport":
#                     candidate_info["relatedPort"] = int(value)
#                 elif key == "generation":
#                     candidate_info["generation"] = int(value)
#                 elif key == "ufrag":
#                     candidate_info["usernameFragment"] = value

#         return candidate_info

# class WebRTCServer:
#     def __init__(self):
#         self.peer_connections = {}
#         self.ice_servers = [
#             RTCIceServer(urls="stun:stun.l.google.com:19302"),
#             RTCIceServer(urls="turn:openrelay.metered.ca:80", username="openrelayproject", credential="openrelayproject"),
#             RTCIceServer(urls="turn:openrelay.metered.ca:443", username="openrelayproject", credential="openrelayproject"),
#         ]

#     async def _send_message(self, websocket, message):
#         await websocket.send(json.dumps(message))
#         logger.info(f"Sent message to Signaling Server: {message}")

#     async def _handle_offer(self, websocket, data):
#         camera_id = data.get("cameraId")
#         client_id = data.get("clientId")
#         if not camera_id or not client_id:
#             logger.error("Missing cameraId or clientId in offer")
#             await self._send_message(
#                 websocket,
#                 {
#                     "type": "error",
#                     "message": "Missing cameraId or clientId",
#                     "clientId": client_id,
#                     "cameraId": camera_id,
#                     "target": client_id,
#                 }
#             )
#             return
#         logger.info(f"Processing offer for camera {camera_id} from client {client_id}")

#         if camera_id in self.peer_connections:
#             pc = self.peer_connections[camera_id]
#             if pc.connectionState == "connected":
#                 logger.info(f"Camera {camera_id} is already connected, rejecting new offer")
#                 await self._send_message(
#                     websocket,
#                     {
#                         "type": "error",
#                         "message": f"Camera {camera_id} is already connected",
#                         "clientId": client_id,
#                         "cameraId": camera_id,
#                         "target": client_id,
#                     }
#                 )
#                 return
#             else:
#                 await pc.close()
#                 del self.peer_connections[camera_id]
#                 logger.info(f"Closed existing peer connection for camera {camera_id}")

#         sync_cameras_from_mongo()
#         camera = next((cam for cam in CAMERAS if cam["id"] == camera_id), None)
#         if not camera:
#             logger.error(f"Camera {camera_id} not found")
#             await self._send_message(
#                 websocket,
#                 {
#                     "type": "error",
#                     "message": f"Camera {camera_id} not found",
#                     "clientId": client_id,
#                     "cameraId": camera_id,
#                     "target": client_id,
#                 }
#             )
#             return

#         pc = RTCPeerConnection(RTCConfiguration(iceServers=self.ice_servers))
#         self.peer_connections[camera_id] = pc

#         try:
#             video_track = RTSPVideoStreamTrack(camera["rtsp_url"], camera_id)
#             pc.addTrack(video_track)
#             logger.info(f"Successfully added video track for camera {camera_id} from RTSP URL: {camera['rtsp_url']}")
#         except Exception as e:
#             logger.error(f"Failed to add video track for camera {camera_id}: {e}")
#             await self._send_message(
#                 websocket,
#                 {
#                     "type": "error",
#                     "message": f"Failed to add video track: {str(e)}",
#                     "clientId": client_id,
#                     "cameraId": camera_id,
#                     "target": client_id,
#                 }
#             )
#             return

#         # NEW: Log ICE candidates and failures
#         pc.onicecandidate = lambda candidate: asyncio.ensure_future(
#             self._send_message(
#                 websocket,
#                 {
#                     "type": "candidate",
#                     "candidate": {
#                         "candidate": candidate.candidate,
#                         "sdpMid": candidate.sdp_mid,
#                         "sdpMLineIndex": candidate.sdp_mline_index,
#                         "usernameFragment": candidate.username_fragment,
#                     },
#                     "clientId": client_id,
#                     "cameraId": camera_id,
#                     "target": client_id,
#                 },
#             )
#         )

#         pc.onconnectionstatechange = lambda: logger.info(
#             f"Connection state for camera {camera_id}: {pc.connectionState}"
#         )

#         # NEW: Log ICE connection state changes and failures
#         pc.oniceconnectionstatechange = lambda : logger.info(
#             f"ICE connection state for camera {camera_id}: {pc.iceConnectionState}"
#         )

#         pc.oniceconnectionstatechange = lambda track: logger.info(
#             f"Received track for camera {camera_id}: {track.kind}, id: {track.id}"
#         )

#         pc.onicecandidateerror = lambda event: logger.error(
#             f"ICE candidate error for camera {camera_id}: {event}"
#         )

#         await pc.setRemoteDescription(RTCSessionDescription(sdp=data["sdp"], type="offer"))
#         logger.info(f"Set remote description for camera {camera_id}")
#         answer = await pc.createAnswer()
#         await pc.setLocalDescription(answer)
#         await self._send_message(
#             websocket,
#             {
#                 "type": "answer",
#                 "sdp": answer.sdp,
#                 "clientId": client_id,
#                 "cameraId": camera_id,
#                 "target": client_id,
#             },
#         )
#         logger.info(f"Sent answer for camera {camera_id} to client {client_id}")

#     async def _handle_candidate(self, data):
#         camera_id = data.get("cameraId")
#         if camera_id not in self.peer_connections:
#             logger.error(f"No peer connection for camera {camera_id}")
#             return

#         candidate = data["candidate"]
#         try:
#             candidate_info = CandidateParser.parse(candidate["candidate"])
#             ice_candidate = RTCIceCandidate(
#                 foundation=candidate_info["foundation"],
#                 component=candidate_info["component"],
#                 protocol=candidate_info["protocol"],
#                 priority=candidate_info["priority"],
#                 ip=candidate_info["ip"],
#                 port=candidate_info["port"],
#                 type=candidate_info["type"],
#                 relatedAddress=candidate_info.get("relatedAddress"),
#                 relatedPort=candidate_info.get("relatedPort"),
#                 sdpMid=candidate["sdpMid"],
#                 sdpMLineIndex=candidate["sdpMLineIndex"],
#             )
#             await self.peer_connections[camera_id].addIceCandidate(ice_candidate)
#             logger.info(f"Added ICE candidate for camera {camera_id}")
#         except Exception as e:
#             logger.error(f"Failed to add ICE candidate for camera {camera_id}: {e}")

#     async def _handle_camera_update(self, data):
#         camera = data.get("camera")
#         action = data.get("action", "update")
#         camera_id = camera.get("id")

#         sync_cameras_from_mongo()
#         if action == "delete":
#             # Xóa camera khỏi CAMERAS
#             CAMERAS[:] = [cam for cam in CAMERAS if cam["id"] != camera_id]
#             # Đóng peer connection nếu tồn tại
#             if camera_id in self.peer_connections:
#                 await self.peer_connections[camera_id].close()
#                 del self.peer_connections[camera_id]
#                 logger.info(f"Closed peer connection for deleted camera {camera_id}")
#             logger.info(f"Deleted camera {camera_id} from CAMERAS")
#         else:
#             # Cập nhật hoặc thêm camera
#             existing_camera = next((cam for cam in CAMERAS if cam["id"] == camera_id), None)
#             if existing_camera:
#                 existing_camera.update(camera)
#                 logger.info(f"Updated camera {camera_id} in CAMERAS")
#                 if camera_id in self.peer_connections:
#                     await self.peer_connections[camera_id].close()
#                     del self.peer_connections[camera_id]
#                     logger.info(f"Closed peer connection for updated camera {camera_id}")
#             else:
#                 CAMERAS.append(camera)
#                 logger.info(f"Added camera {camera_id} to CAMERAS")

#     async def _handle_signaling(self, websocket):
#         async for message in websocket:
#             try:
#                 data = json.loads(message)
#                 logger.info(f"Received message: {data}")

#                 if data.get("type") == "offer":
#                     await self._handle_offer(websocket, data)
#                 elif data.get("type") == "candidate":
#                     await self._handle_candidate(data)
#                 elif data.get("type") == "camera_update":
#                     await self._handle_camera_update(data)
#             except Exception as e:
#                 logger.error(f"Error processing message: {e}")

#     async def run(self):
#         for attempt in range(RETRY_MAX_ATTEMPTS):
#             try:
#                 logger.info(f"Attempting to connect to Signaling Server ({attempt + 1}/{RETRY_MAX_ATTEMPTS})")
#                 async with websockets.connect(
#                     SIGNALING_SERVER_URL, ping_interval=20, ping_timeout=60
#                 ) as websocket:
#                     logger.info("Connected to Signaling Server")
#                     initial_message = json.loads(await asyncio.wait_for(websocket.recv(), timeout=10))
#                     logger.info(f"Received initial message: {initial_message}")

#                     server_id = initial_message.get("id") if initial_message.get("type") == "id" else None
#                     if server_id is None:
#                         logger.error("Invalid initial message format, missing 'id' or 'type'")
#                         continue
#                     logger.info(f"WebRTC Server ID: {server_id}")

#                     await self._send_message(websocket, {"type": "register", "role": "webrtc-server"})
#                     logger.info("Registered as webrtc-server")
#                     await self._handle_signaling(websocket)
#             except Exception as e:
#                 logger.error(f"Connection failed: {e}")
#                 if attempt < RETRY_MAX_ATTEMPTS - 1:
#                     await asyncio.sleep(RETRY_DELAY_SECONDS)
#                 else:
#                     raise Exception("Could not connect to Signaling Server")

# async def main():
#     sync_cameras_from_mongo()
#     server = WebRTCServer()
#     await server.run()

# if __name__ == "__main__":
#     import os
#     os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
#     asyncio.run(main())


import asyncio
import json
import websockets
from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
    RTCConfiguration,
    RTCIceServer,
    RTCIceCandidate,
)
from config import logger, SIGNALING_SERVER_URL, CAMERAS, RETRY_MAX_ATTEMPTS, RETRY_DELAY_SECONDS
from object_detection import RTSPVideoStreamTrack
import os
from pymongo import MongoClient
import logging
from datetime import datetime


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Tạo thư mục logs
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, f"requests_{datetime.now().strftime('%Y%m%d')}.log")
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Kết nối MongoDB
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
mongo_client = MongoClient(MONGODB_URI)
db = mongo_client["HONDA_HN"]
collection = db["config"]

def sync_cameras_from_mongo():
    global CAMERAS
    CAMERAS[:] = list(collection.find({}, {"_id": 0}))
    logger.info("Synced CAMERAS from MongoDB")

class CandidateParser:
    """Parse ICE candidate strings into structured data."""
    
    @staticmethod
    def parse(candidate_str):
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
                key, value = parts[i], parts[i + 1]
                if key == "raddr":
                    candidate_info["relatedAddress"] = value
                elif key == "rport":
                    candidate_info["relatedPort"] = int(value)
                elif key == "generation":
                    candidate_info["generation"] = int(value)
                elif key == "ufrag":
                    candidate_info["usernameFragment"] = value

        return candidate_info

class WebRTCServer:
    """Manage WebRTC connections and signaling."""
    
    def __init__(self):
        self.peer_connections = {}
        self.ice_servers = [
            RTCIceServer(urls="stun:stun.l.google.com:19302"),
            RTCIceServer(urls="turn:openrelay.metered.ca:80", username="openrelayproject", credential="openrelayproject"),
            RTCIceServer(urls="turn:openrelay.metered.ca:443", username="openrelayproject", credential="openrelayproject"),
        ]

    async def _send_message(self, websocket, message):
        await websocket.send(json.dumps(message))
        logger.info(f"Sent message to Signaling Server: {message}")

    async def _handle_offer(self, websocket, data):
        camera_id = data.get("cameraId")
        client_id = data.get("clientId")
        if not camera_id or not client_id:
            logger.error("Missing cameraId or clientId in offer")
            return

        # Đồng bộ CAMERAS trước khi xử lý
        sync_cameras_from_mongo()
        camera = next((cam for cam in CAMERAS if cam["id"] == camera_id), None)
        if not camera:
            logger.error(f"Camera {camera_id} not found")
            return

        pc = RTCPeerConnection(RTCConfiguration(iceServers=self.ice_servers))
        self.peer_connections[camera_id] = pc

        try:
            video_track = RTSPVideoStreamTrack(camera["rtsp_url"], camera_id)
            pc.addTrack(video_track)
            logger.info(f"Added video track for camera {camera_id}")
        except Exception as e:
            logger.error(f"Failed to add video track for camera {camera_id}: {e}")
            return

        pc.onicecandidate = lambda candidate: asyncio.ensure_future(
            self._send_message(
                websocket,
                {
                    "type": "candidate",
                    "candidate": {
                        "candidate": candidate.candidate,
                        "sdpMid": candidate.sdp_mid,
                        "sdpMLineIndex": candidate.sdp_mline_index,
                        "usernameFragment": candidate.username_fragment,
                    },
                    "clientId": client_id,
                    "cameraId": camera_id,
                    "target": client_id,
                },
            )
        )

        pc.onconnectionstatechange = lambda: logger.info(
            f"Connection state for camera {camera_id}: {pc.connectionState}"
        )

        await pc.setRemoteDescription(RTCSessionDescription(sdp=data["sdp"], type="offer"))
        logger.info(f"Set remote description for camera {camera_id}")
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        await self._send_message(
            websocket,
            {
                "type": "answer",
                "sdp": answer.sdp,
                "clientId": client_id,
                "cameraId": camera_id,
                "target": client_id,
            },
        )
        logger.info(f"Sent answer for camera {camera_id} to client {client_id}")

    async def _handle_candidate(self, data):
        camera_id = data.get("cameraId")
        if camera_id not in self.peer_connections:
            logger.error(f"No peer connection for camera {camera_id}")
            return

        candidate = data["candidate"]
        try:
            candidate_info = CandidateParser.parse(candidate["candidate"])
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
                sdpMLineIndex=candidate["sdpMLineIndex"],
            )
            await self.peer_connections[camera_id].addIceCandidate(ice_candidate)
            logger.info(f"Added ICE candidate for camera {camera_id}")
        except Exception as e:
            logger.error(f"Failed to add ICE candidate for camera {camera_id}: {e}")

    async def _handle_camera_update(self, data):
        camera = data.get("camera")
        camera_id = camera.get("id")
        # Đồng bộ CAMERAS trước khi xử lý
        sync_cameras_from_mongo()
        existing_camera = next((cam for cam in CAMERAS if cam["id"] == camera_id), None)
        if existing_camera:
            existing_camera.update(camera)
            logger.info(f"Updated camera {camera_id} in CAMERAS")
            # Đóng peer connection cũ nếu tồn tại
            if camera_id in self.peer_connections:
                await self.peer_connections[camera_id].close()
                del self.peer_connections[camera_id]
                logger.info(f"Closed peer connection for camera {camera_id}")
        else:
            CAMERAS.append(camera)
            logger.info(f"Added camera {camera_id} to CAMERAS")

    async def _handle_signaling(self, websocket):
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received message: {data}")

                if data.get("type") == "offer":
                    await self._handle_offer(websocket, data)
                elif data.get("type") == "candidate":
                    await self._handle_candidate(data)
                elif data.get("type") == "camera_update":
                    await self._handle_camera_update(data)
            except Exception as e:
                logger.error(f"Error processing message: {e}")

    async def run(self):
        for attempt in range(RETRY_MAX_ATTEMPTS):
            try:
                logger.info(f"Attempting to connect to Signaling Server ({attempt + 1}/{RETRY_MAX_ATTEMPTS})")
                async with websockets.connect(
                    SIGNALING_SERVER_URL, ping_interval=20, ping_timeout=60
                ) as websocket:
                    logger.info("Connected to Signaling Server")
                    initial_message = json.loads(await asyncio.wait_for(websocket.recv(), timeout=10))
                    logger.info(f"Received initial message: {initial_message}")

                    server_id = initial_message.get("id") if initial_message.get("type") == "id" else None
                    if server_id is None:
                        logger.error("Invalid initial message format, missing 'id' or 'type'")
                        continue
                    logger.info(f"WebRTC Server ID: {server_id}")

                    await self._send_message(websocket, {"type": "register", "role": "webrtc-server"})
                    logger.info("Registered as webrtc-server")
                    await self._handle_signaling(websocket)
            except Exception as e:
                logger.error(f"Connection failed: {e}")
                if attempt < RETRY_MAX_ATTEMPTS - 1:
                    await asyncio.sleep(RETRY_DELAY_SECONDS)
                else:
                    raise Exception("Could not connect to Signaling Server")

async def main():
    # Đồng bộ CAMERAS khi khởi động
    sync_cameras_from_mongo()
    server = WebRTCServer()
    await server.run()

if __name__ == "__main__":
    import os
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
    asyncio.run(main())