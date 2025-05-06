import asyncio
import websockets
import json
import logging
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

clients = {}

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
                    else:  # answer or candidate for frontend
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