
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
    allow_origins=["*"],  
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