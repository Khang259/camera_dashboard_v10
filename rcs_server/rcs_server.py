from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn

app = FastAPI()

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả origins trong môi trường development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint GET để kiểm tra
@app.get("/testing_endpoint")
async def root():
    logger.info("Nhận yêu cầu GET tại /testing_endpoint")
    return {"message": "Hello World"}

# Endpoint POST để nhận dữ liệu JSON từ server phát hiện tay
@app.post("/testing_endpoint")
async def receive_hand_data(data: dict):
    logger.info(f"Dữ liệu nhận được từ server phát hiện tay: {data}")
    return {"status": "success", "received_data": data}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7000)