from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import json
import logging
import os

# Tắt log MediaPipe không cần thiết
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load configuration
with open("../config.json", "r") as f:
    config = json.load(f)
    cameras = config["cameras"]
    DETECT_SERVER_URL = config["detect_server_url"]

# Lifespan handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up")
    yield
    logger.info("Application shutting down")

app = FastAPI(lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# APIs
@app.get("/api/cameras")
async def get_cameras():
    return {"cameras": cameras}

@app.get("/api/cameras/{camera_id}/status")
async def check_camera_status(camera_id: str):
    import cv2
    camera = next((cam for cam in cameras if cam["id"] == camera_id), None)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    try:
        cap = cv2.VideoCapture(camera["rtsp_url"] + "?tcp", cv2.CAP_FFMPEG)
        if not cap.isOpened():
            raise Exception("Failed to connect")
        ret, _ = cap.read()
        cap.release()
        return {"camera_id": camera_id, "status": "connected" if ret else "disconnected"}
    except Exception as e:
        logger.error(f"Error checking camera {camera_id}: {str(e)}")
        return {"camera_id": camera_id, "status": "disconnected", "error": str(e)}

@app.post("/api/cameras")
async def add_camera(camera: dict):
    cameras.append(camera)
    with open("../config.json", "w") as f:
        json.dump(config, f, indent=2)
    return {"message": "Camera added", "camera": camera}

@app.get("/api/config")
async def get_config():
    return config

@app.post("/testing_endpoint")
async def testing_endpoint(data: dict):
    logger.info(f"Received testing endpoint data: {data}")
    return {"status": "received", "data": data}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7000)