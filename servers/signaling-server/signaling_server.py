# import asyncio
# import websockets
# import json
# import logging
# import uuid
# import uvicorn
# import os
# from fastapi import FastAPI, WebSocket
# from fastapi.middleware.cors import CORSMiddleware
# from datetime import datetime, timedelta

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# LOG_DIR = "logs"
# os.makedirs(LOG_DIR, exist_ok=True)
# log_file = os.path.join(LOG_DIR, f"requests_signaling_{datetime.now().strftime('%Y%m%d')}.log")
# file_handler = logging.FileHandler(log_file)
# file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
# logger.addHandler(file_handler)

# clients = {}
# camera_states = {
#     "1": {"clientId": None, "state": "disconnected", "last_active": None},
#     "2": {"clientId": None, "state": "disconnected", "last_active": None},
#     "3": {"clientId": None, "state": "disconnected", "last_active": None},
# }
# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# async def cleanup_inactive_clients():
#     while True:
#         current_time = datetime.now()
#         for camera_id, state in camera_states.items():
#             if state["state"] == "connected" and state["last_active"]:
#                 if current_time - state["last_active"] > timedelta(seconds=30):
#                     logger.info(f"Camera {camera_id} timed out, resetting to disconnected")
#                     state["state"] = "disconnected"
#                     state["clientId"] = None
#                     state["last_active"] = None
#         await asyncio.sleep(10)

# @app.get("/camera_status")
# async def get_camera_status():
#     return camera_states

# @app.post("/update")
# async def update_camera(data: dict):
#     camera = data.get("camera", {})
#     action = data.get("action", "update")
#     for client_id, client in clients.items():
#         if client["type"] == "webrtc-server":
#             try:
#                 await client["websocket"].send(json.dumps({"type": "camera_update", "camera": camera, "action": action}))
#                 logger.info(f"Notified WebRTC server {client_id} about camera {action}")
#             except Exception as e:
#                 logger.error(f"Failed to notify WebRTC server {client_id}: {str(e)}")
#     return {"message": f"Camera {action} notified"}

# async def signaling_server(websocket, path):
#     client_id = str(uuid.uuid4())
#     clients[client_id] = {"websocket": websocket, "type": "unknown", "cameraId": None}
#     logger.info(f"New client connected: {client_id}, Path: {path}, Total clients: {len(clients)}")

#     try:
#         await websocket.send(json.dumps({"type": "id", "id": client_id}))
#         logger.info(f"Sent client ID {client_id} to client")

#         async for message in websocket:
#             try:
#                 data = json.loads(message)
#                 logger.info(f"Received message from {client_id}: {data}")

#                 if data.get("type") == "register" and data.get("role") == "webrtc-server":
#                     clients[client_id]["type"] = "webrtc-server"
#                     logger.info(f"Client {client_id} registered as webrtc-server")

#                 if "cameraId" in data and data.get("type") != "answer":
#                     clients[client_id]["cameraId"] = data["cameraId"]
#                     logger.info(f"Assigned cameraId {data['cameraId']} to client {client_id}")

#                 if data.get("type") == "offer":
#                     camera_id = data.get("cameraId")
#                     if camera_id not in camera_states:
#                         camera_states[camera_id] = {"clientId": None, "state": "disconnected", "last_active": None}
#                     logger.info(f"Current camera states: {camera_states}")
#                     if camera_states[camera_id]["state"] == "connected":
#                         logger.info(f"Rejecting offer for camera {camera_id} as it is already connected to client {camera_states[camera_id]['clientId']}")
#                         await websocket.send(json.dumps({
#                             "type": "error",
#                             "message": f"Camera {camera_id} is already connected",
#                             "cameraId": camera_id,
#                             "clientId": client_id,
#                             "target": client_id,
#                         }))
#                         continue
#                     camera_states[camera_id]["last_active"] = datetime.now()

#                 if data.get("type") in ["offer", "answer", "candidate", "error"]:
#                     target_id = data.get("target")
#                     target_client = None
#                     if data["type"] == "offer" or (data["type"] == "candidate" and data.get("target") == "webrtc-server"):
#                         for cid, client in clients.items():
#                             if client["type"] == "webrtc-server":
#                                 target_client = client["websocket"]
#                                 target_id = cid
#                                 break
#                     else:
#                         for cid, client in clients.items():
#                             if cid == target_id:
#                                 target_client = client["websocket"]
#                                 target_id = cid
#                                 break
#                     if target_client:
#                         await target_client.send(json.dumps(data))
#                         logger.info(f"Relayed {data['type']} from {client_id} to {target_id}")
#                         if data["type"] == "answer" and data.get("cameraId"):
#                             camera_states[data["cameraId"]] = {
#                                 "clientId": data.get("clientId"),
#                                 "state": "connected",
#                                 "last_active": datetime.now()
#                             }
#                             logger.info(f"Camera {data['cameraId']} marked as connected to client {client_id}")
#                     else:
#                         logger.error(f"No target client {target_id} found for {data['type']}")
#             except json.JSONDecodeError:
#                 logger.error(f"Invalid JSON message received from {client_id}")
#             except Exception as e:
#                 logger.error(f"Error processing message from {client_id}: {str(e)}")
#     except websockets.exceptions.ConnectionClosed:
#         logger.info(f"Client {client_id} disconnected")
#         for camera_id, state in list(camera_states.items()):
#             if state["clientId"] == client_id:
#                 camera_states[camera_id]["state"] = "disconnected"
#                 camera_states[camera_id]["clientId"] = None
#                 camera_states[camera_id]["last_active"] = None
#                 logger.info(f"Camera {camera_id} marked as disconnected")
#     finally:
#         logger.info(f"Cleaning up client {client_id}, Remaining clients: {len(clients) - 1}")
#         if client_id in clients:
#             del clients[client_id]

# async def start_servers():
#     websocket_server = await websockets.serve(
#         signaling_server,
#         "0.0.0.0",
#         9000,
#         ping_interval=20,
#         ping_timeout=60
#     )
#     logger.info("Signaling Server running on ws://localhost:9000")
#     asyncio.create_task(cleanup_inactive_clients())
#     config = uvicorn.Config(app, host="0.0.0.0", port=9001)
#     server = uvicorn.Server(config)
#     await server.serve()

# if __name__ == "__main__":
#     asyncio.run(start_servers())


import asyncio
import websockets
import json
import logging
import uuid
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn, os
from datetime import datetime


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

clients = {}
app = FastAPI()


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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong sản xuất, thay bằng danh sách cụ thể như ["http://localhost:3000", "http://localhost:7000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/update")
async def update_camera(camera: dict):
    for client_id, client in clients.items():
        if client["type"] == "webrtc-server":
            try:
                await client["websocket"].send(json.dumps({"type": "camera_update", "camera": camera}))
                logger.info(f"Notified WebRTC server {client_id} about camera update")
            except Exception as e:
                logger.error(f"Failed to notify WebRTC server {client_id}: {str(e)}")
    return {"message": "Camera update notified"}

async def signaling_server(websocket, path):
    client_id = str(uuid.uuid4())
    clients[client_id] = {"websocket": websocket, "type": "unknown", "cameraId": None}
    logger.info(f"New client connected: {client_id}, Path: {path}")

    try:
        await websocket.send(json.dumps({"type": "id", "id": client_id}))
        logger.info(f"Sent client ID {client_id} to client")

        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received message from {client_id}: {data}")

                if data.get("type") == "register" and data.get("role") == "webrtc-server":
                    clients[client_id]["type"] = "webrtc-server"
                    logger.info(f"Client {client_id} registered as webrtc-server")

                if "cameraId" in data and data.get("type") != "answer":
                    clients[client_id]["cameraId"] = data["cameraId"]
                    logger.info(f"Assigned cameraId {data['cameraId']} to client {client_id}")

                if data.get("type") in ["offer", "answer", "candidate"]:
                    target_id = data.get("target")
                    target_client = None

                    if data["type"] == "offer" or (data["type"] == "candidate" and data.get("target") == "webrtc-server"):
                        for cid, client in clients.items():
                            if client["type"] == "webrtc-server":
                                target_client = client["websocket"]
                                target_id = cid
                                break
                    else:
                        for cid, client in clients.items():
                            if cid == target_id:
                                target_client = client["websocket"]
                                target_id = cid
                                break

                    if target_client:
                        await target_client.send(json.dumps(data))
                        logger.info(f"Relayed {data['type']} from {client_id} to {target_id}")
                    else:
                        logger.error(f"No target client {target_id} found for {data['type']}")
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON message received from {client_id}")
            except Exception as e:
                logger.error(f"Error processing message from {client_id}: {str(e)}")
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    finally:
        logger.info(f"Cleaning up client {client_id}")
        if client_id in clients:
            del clients[client_id]

async def start_servers():
    # Khởi động WebSocket server
    websocket_server = await websockets.serve(
        signaling_server,
        "0.0.0.0",
        9000,
        ping_interval=20,
        ping_timeout=60
    )
    logger.info("Signaling Server running on ws://localhost:9000")

    # Khởi động FastAPI server
    config = uvicorn.Config(app, host="0.0.0.0", port=9001)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    # Chạy cả WebSocket và FastAPI trong cùng một event loop
    asyncio.run(start_servers())