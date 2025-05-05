import asyncio
import websockets
import json
import logging
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#Biến lưu danh sách kết nối 
clients = {}

#Hàm xử lý khi có client kết nối tới Websocket server
async def signaling_server(websocket, path):
    client_id = str(uuid.uuid4()) #Tạo id ngẫu nhiên
    clients[client_id] = {"websocket": websocket, "type": "unknown", "cameraId": None}
    logger.info(f"New client connected: {client_id}, Path: {path}")

    try:
        # Gửi ID về cho client sau khi kết nối
        await websocket.send(json.dumps({"type": "id", "id": client_id}))
        # Lặp liên tục để nhận message từ client này
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received message from {client_id}: {data}")

                # Lưu cameraId nếu có
                if "cameraId" in data:
                    clients[client_id]["cameraId"] = data["cameraId"]

                # Xác định loại client
                if "clientId" in data and data.get("clientId") == "client":
                    clients[client_id]["type"] = "frontend"
                elif "target" in data and data.get("target") == "webrtc-server":
                    clients[client_id]["type"] = "frontend"
                elif data.get("type") in ["answer", "candidate"] and data.get("target") != "webrtc-server":
                    clients[client_id]["type"] = "webrtc-server"

                # Xử lý khi nhận offer/answer/candidate để chuyển tiếp
                if data["type"] in ["offer", "answer", "candidate"]:
                    target_id = data.get("target")
                    target_client = None

                    # Tìm client đích
                    if data["type"] == "offer":
                        # Tìm webrtc-server
                        for cid, client in clients.items():
                            if client["type"] == "webrtc-server":
                                target_client = client["websocket"]
                                target_id = cid
                                break
                    else:
                        # Tìm frontend hoặc webrtc-server dựa trên target_id hoặc cameraId
                        for cid, client in clients.items():
                            if cid == target_id or (
                                data.get("cameraId") and client["cameraId"] == data["cameraId"]
                            ):
                                target_client = client["websocket"]
                                target_id = cid
                                break

                    if target_client:
                        await target_client.send(json.dumps(data))
                        logger.info(f"Relayed {data['type']} from {client_id} to {target_id}")
                    else:
                        logger.error(f"Target client {target_id} not found for {data['type']}")
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON message received from {client_id}")
            except Exception as e:
                logger.error(f"Error processing message from {client_id}: {str(e)}")
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    finally:
        logger.info(f"Cleaning up client {client_id}")
        del clients[client_id]

async def main():
    try:
        server = await websockets.serve(
            signaling_server,
            "0.0.0.0",
            9000,
            ping_interval=20,
            ping_timeout=60
        )
        logger.info("Signaling Server running on ws://localhost:9000")
        await server.wait_closed()
    except Exception as e:
        logger.error(f"Failed to start Signaling Server: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())