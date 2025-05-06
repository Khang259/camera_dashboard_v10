import json
import logging, cv2
from fractions import Fraction

# Constants
CONFIG_PATH = "../config.json"
LOG_LEVEL = logging.INFO
RETRY_MAX_ATTEMPTS = 5
RETRY_DELAY_SECONDS = 5
FRAME_RATE = 15
FRAME_WIDTH = 640
FRAME_HEIGHT = 360
BUFFER_SIZE = 10
VIDEO_FOURCC = cv2.VideoWriter_fourcc(*"H264")
DETECTION_INTERVAL = 5
SEND_INTERVAL_SECONDS = 5
CENTER_AREA_RATIO = 0.3
VIDEO_TIME_BASE = Fraction(1, 90000)
PTS_INCREMENT = int(90000 / FRAME_RATE)

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    filename='webrtc_server.log',
    filemode='a',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration
def load_config(file_path):
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load configuration: {e}")
        raise

config = load_config(CONFIG_PATH)
SIGNALING_SERVER_URL = config["signaling_server_url"]
DETECT_SERVER_URL = config["detect_server_url"]
CAMERAS = config["cameras"]