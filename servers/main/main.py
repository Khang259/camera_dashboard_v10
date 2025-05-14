from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pymongo import MongoClient
import json
import logging
import os
import httpx
from datetime import datetime
import asyncio

# Tắt log MediaPipe không cần thiết
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

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

# Load configuration
with open("../config.json", "r") as f:
    config = json.load(f)
    cameras = config["cameras"]
    DETECT_SERVER_URL = config["detect_server_url"]
    SIGNALING_SERVER_URL = config.get("signaling_server_url", "ws://localhost:9000")

# Kết nối MongoDB
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = MongoClient(MONGODB_URI)
db = client["HONDA_HN"]
collection = db["config"]

# Đồng bộ cameras từ MongoDB
def sync_cameras_from_mongo():
    global cameras
    mongo_cameras = list(collection.find({}, {"_id": 0}))
    cameras[:] = mongo_cameras
    with open("../config.json", "w") as f:
        config["cameras"] = cameras
        json.dump(config, f, indent=2)
    logger.info("Synced cameras from MongoDB")

sync_cameras_from_mongo()

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

# Middleware ghi log request
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_info = {
        "method": request.method,
        "url": str(request.url),
        "client": request.client.host if request.client else "unknown",
        "headers": dict(request.headers),
        "timestamp": datetime.now().isoformat(),
    }
    try:
        if request.method in ["POST", "PUT", "DELETE"]:
            request_info["body"] = await request.json()
    except Exception:
        request_info["body"] = None
    logger.info(f"Request: {json.dumps(request_info, indent=2)}")

    response = await call_next(request)
    logger.info(f"Response for {request.method} {request.url}: status={response.status_code}")
    return response

# Hàm gửi thông báo đến signaling server
async def notify_signaling_server(camera, action="update"):
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{SIGNALING_SERVER_URL.replace('ws', 'http')}:9001/update",
                json={"camera": camera, "action": action}
            )
            logger.info(f"Notified signaling server about camera {camera['id']} ({action})")
    except Exception as e:
        logger.error(f"Failed to notify signaling server: {str(e)}")

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
    try:
        camera_id = camera.get("id")
        if camera_id:
            # Nếu có id, chuyển sang xử lý PUT
            return await update_camera(camera_id, camera)
        
        # Thêm camera mới
        camera_id = str(int(collection.count_documents({}) + 1))
        camera["id"] = camera_id
        collection.insert_one({
            "id": camera_id,
            "name": camera["name"],
            "ipAddress": camera.get("ipAddress"),
            "rtsp_url": camera["rtsp_url"]
        })
        cameras.append(camera)
        logger.info(f"Added camera {camera_id}")

        # Cập nhật config.json
        with open("../config.json", "w") as f:
            config["cameras"] = cameras
            json.dump(config, f, indent=2)

        # Thông báo signaling server
        await notify_signaling_server(camera, "add")

        return {"message": "Camera added", "camera": camera}
    except Exception as e:
        logger.error(f"Error adding camera: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding camera: {str(e)}")

@app.put("/api/cameras")
async def update_camera(camera: dict):
    try:
        camera_id = camera.get("id")
        if not camera_id:
            raise HTTPException(status_code=400, detail="Camera ID is required")

        # Kiểm tra camera tồn tại
        existing_camera = next((cam for cam in cameras if cam["id"] == camera_id), None)
        if not existing_camera:
            raise HTTPException(status_code=404, detail="Camera not found")

        # Cập nhật MongoDB
        collection.update_one(
            {"id": camera_id},
            {"$set": {
                "name": camera["name"],
                "ipAddress": camera.get("ipAddress"),
                "rtsp_url": camera["rtsp_url"]
            }}
        )

        # Cập nhật danh sách cameras
        existing_camera.update({
            "name": camera["name"],
            "ipAddress": camera.get("ipAddress"),
            "rtsp_url": camera["rtsp_url"]
        })
        logger.info(f"Updated camera {camera_id}")

        # Cập nhật config.json
        with open("../config.json", "w") as f:
            config["cameras"] = cameras
            json.dump(config, f, indent=2)

        # Thông báo signaling server
        await notify_signaling_server(camera, "update")

        return {"message": "Camera updated", "camera": camera}
    except Exception as e:
        logger.error(f"Error updating camera: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating camera: {str(e)}")

@app.delete("/api/cameras/{camera_id}")
async def delete_camera(camera_id: str):
    try:
        # Kiểm tra camera tồn tại
        existing_camera = next((cam for cam in cameras if cam["id"] == camera_id), None)
        if not existing_camera:
            raise HTTPException(status_code=404, detail="Camera not found")

        # Xóa khỏi MongoDB
        result = collection.delete_one({"id": camera_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Camera not found in database")

        # Xóa khỏi danh sách cameras
        cameras[:] = [cam for cam in cameras if cam["id"] != camera_id]
        logger.info(f"Deleted camera {camera_id}")

        # Cập nhật config.json
        with open("../config.json", "w") as f:
            config["cameras"] = cameras
            json.dump(config, f, indent=2)

        # Thông báo signaling server
        await notify_signaling_server({"id": camera_id}, "delete")

        return {"message": "Camera deleted", "camera_id": camera_id}
    except Exception as e:
        logger.error(f"Error deleting camera: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting camera: {str(e)}")

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