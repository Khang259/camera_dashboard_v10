import asyncio
import websockets
import json
import logging
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store connected clients
clients = {}

async def signaling_server(websocket, path):
    # Generate a unique client ID
    client_id = str(uuid.uuid4())
    clients[client_id] = websocket
    logger.info(f"New client connected: {client_id}, Path: {path}")

    # Send client ID to the client
    try:
        await websocket.send(json.dumps({"type": "id", "id": client_id}))
    except Exception as e:
        logger.error(f"Error sending client ID to {client_id}: {str(e)}")
        return

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received message from {client_id}: {data}")

                # Relay SDP or ICE candidate to the target client
                if data["type"] in ["offer", "answer", "candidate"]:
                    target_id = data.get("target")
                    if target_id in clients:
                        target_client = clients[target_id]
                        await target_client.send(json.dumps(data))
                        logger.info(f"Relayed {data['type']} to {target_id}")
                    else:
                        logger.error(f"Target client {target_id} not found")
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON message received from {client_id}")
            except Exception as e:
                logger.error(f"Error processing message from {client_id}: {str(e)}")
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Client {client_id} disconnected: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error for client {client_id}: {str(e)}")
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
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Signaling Server shutting down")
    except Exception as e:
        logger.error(f"Signaling Server crashed: {str(e)}")