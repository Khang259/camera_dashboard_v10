import requests
import threading
import time
import logging
from threading import Lock
from collections import deque

# Setup logging
logger = logging.getLogger('logic_sending')
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('logs/rtsp_reader.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Dictionary to store thread states
pending_threads = {}

# Global lock for creating delayed_post_request threads
global_post_lock = Lock()

# Dictionary to store Locks for each end_task_path
end_task_locks = {
    "10000170": Lock(),
    "10000171": Lock(),
    "10000140": Lock(),
    "10000141": Lock(),
    "10000164": Lock(),
    "10000147": Lock()
}

# Round-Robin queue for start_task_paths (per end_task_path)
start_task_queues = {}  # {end_task_path: deque}
start_task_queue_lock = Lock()

def send_post_request(start_task_path, end_task_path, camera_idx, bbox_idx, api_url):
    logger.debug(f"[Camera {camera_idx + 1}] Preparing to send POST request to {api_url}")
    json_data = {
        "modelProcessCode": "checking_camera_work",
        "fromSystem": "testing_one",
        "orderId": f"thado_1_1_{int(time.time())}",
        "taskOrderDetail": [
            {
                "taskPath": f"{start_task_path},{end_task_path}"
            }
        ]
    }
    try:
        response = requests.post(api_url, json=json_data, timeout=5)
        logger.info(f"[Camera {camera_idx + 1}] Sent POST request for Bounding box {bbox_idx + 1}:")
        logger.info(f"  - StartTaskPath: {start_task_path}, EndTaskPath: {end_task_path}")
        logger.info(f"  - Status code: {response.status_code}")
        logger.info(f"  - Response: {response.text}")
        print(f"\n[Camera {camera_idx + 1}] Sent POST request for Bounding box {bbox_idx + 1}:")
        print(f"  - StartTaskPath: {start_task_path}, EndTaskPath: {end_task_path}")
        print(f"  - Status code: {response.status_code}")
        print(f"  - Response: {response.text}")
        return response.status_code, response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"[Camera {camera_idx + 1}] Error sending POST request: {e}")
        print(f"\n[Camera {camera_idx + 1}] Error sending POST request: {e}")
        return None, None

def check_and_send_post_request(camera_idx, idx, task_path, bbox_states, post_sent, empty_end_task_paths, has_start_task_paths, task_path_constraints, api_url):
    logger.debug(f"[Camera {camera_idx + 1}] Checking task_path={task_path}, bbox_states[{camera_idx}][{idx}]={bbox_states[camera_idx][idx]}, post_sent[{camera_idx}][{idx}]={post_sent[camera_idx][idx]}")
    if task_path in task_path_constraints and not bbox_states[camera_idx][idx] and not post_sent[camera_idx][idx]:
        with global_post_lock:
            if task_path not in end_task_locks:
                logger.warning(f"[Camera {camera_idx + 1}] Adding missing task_path {task_path} to end_task_locks")
                end_task_locks[task_path] = Lock()
            # Khởi tạo hàng đợi Round-Robin cho end_task_path nếu chưa có
            if task_path not in start_task_queues:
                allowed_start_paths = task_path_constraints.get(task_path, [])
                valid_start_paths = [
                    start_task_path for start_task_path in has_start_task_paths.get(0, set())
                    if start_task_path in allowed_start_paths
                ]
                if camera_idx != 0:  # Kiểm tra camera khác nếu cần
                    for cam_idx in has_start_task_paths:
                        if cam_idx != 0:
                            valid_start_paths.extend([
                                start_task_path for start_task_path in has_start_task_paths[cam_idx]
                                if start_task_path in allowed_start_paths
                            ])
                start_task_queues[task_path] = deque(sorted(set(valid_start_paths)))
                logger.debug(f"[Camera {camera_idx + 1}] Initialized start_task_queue for {task_path}: {list(start_task_queues[task_path])}")
        with end_task_locks[task_path]:
            logger.debug(f"[Camera {camera_idx + 1}] Acquired lock for {task_path}")
            # Lấy start_task_path từ hàng đợi
            selected_start_path = None
            with start_task_queue_lock:
                if task_path in start_task_queues and start_task_queues[task_path]:
                    selected_start_path = start_task_queues[task_path].popleft()
                    start_task_queues[task_path].append(selected_start_path)  # Đẩy lại cuối hàng đợi
                    logger.debug(f"[Camera {camera_idx + 1}] Selected start_task_path: {selected_start_path}, new queue for {task_path}: {list(start_task_queues[task_path])}")
            if not selected_start_path:
                logger.debug(f"[Camera {camera_idx + 1}] No valid start_task_path available for {task_path}")
                return
            # Kiểm tra ràng buộc task_path_constraints
            allowed_start_paths = task_path_constraints.get(task_path, [])
            if selected_start_path not in allowed_start_paths:
                logger.error(f"[Camera {camera_idx + 1}] Invalid pair: {selected_start_path} not in allowed_start_paths for {task_path}: {allowed_start_paths}")
                return
            logger.info(f"[Camera {camera_idx + 1}] Detected empty end_task_path {task_path} and start_task_path {selected_start_path} with cargo")
            print(f"\n[Camera {camera_idx + 1}] Detected empty end_task_path {task_path} and start_task_path {selected_start_path} with cargo")
            def delayed_post_request():
                logger.debug(f"[Camera {camera_idx + 1}] Started delayed_post_request for {task_path}")
                try:
                    start_time = time.time()
                    with global_post_lock:
                        initial_empty_state = task_path in empty_end_task_paths[camera_idx]
                        initial_start_state = any(selected_start_path in has_start_task_paths.get(cam_idx, set()) for cam_idx in has_start_task_paths)
                    time.sleep(2)
                    end_time = time.time()
                    logger.debug(f"[Camera {camera_idx + 1}] Waited {end_time - start_time}s")
                    with end_task_locks[task_path]:
                        current_empty_state = task_path in empty_end_task_paths[camera_idx]
                        current_start_state = any(selected_start_path in has_start_task_paths.get(cam_idx, set()) for cam_idx in has_start_task_paths)
                        logger.info(f"[Camera {camera_idx + 1}] Condition: task_path={task_path} in empty_end_task_paths={current_empty_state}, start_task_path={selected_start_path} in has_start_task_paths={current_start_state}")
                        logger.debug(f"[Camera {camera_idx + 1}] Initial states: empty={initial_empty_state}, start={initial_start_state}")
                        if current_empty_state and current_start_state:
                            logger.info(f"[Camera {camera_idx + 1}] Using current states to send POST")
                            status_code, response = send_post_request(selected_start_path, task_path, camera_idx, idx, api_url)
                            if status_code == 200 and response and response.get('code') == 1000:
                                post_sent[camera_idx][idx] = True
                                empty_end_task_paths[camera_idx].discard(task_path)
                            else:
                                logger.debug(f"[Camera {camera_idx + 1}] POST failed, will retry with next start_task_path")
                                # Không xóa pending_threads để thử lại
                        else:
                            logger.debug(f"[Camera {camera_idx + 1}] POST not sent: empty={current_empty_state}, start={current_start_state}")
                    with global_post_lock:
                        if task_path in pending_threads:
                            del pending_threads[task_path]
                            logger.debug(f"[Camera {camera_idx + 1}] Removed thread state for {task_path}")
                except Exception as e:
                    logger.error(f"[Camera {camera_idx + 1}] Error in delayed_post_request: {e}")
                    with global_post_lock:
                        if task_path in pending_threads:
                            del pending_threads[task_path]
                            logger.debug(f"[Camera {camera_idx + 1}] Removed thread state for {task_path}")
            with global_post_lock:
                if task_path not in pending_threads:
                    pending_threads[task_path] = True
                    logger.debug(f"[Camera {camera_idx + 1}] Creating thread for delayed_post_request for {task_path}")
                    threading.Thread(target=delayed_post_request, daemon=True).start()
    else:
        logger.debug(f"[Camera {camera_idx + 1}] Conditions not met for {task_path}: in_constraints={task_path in task_path_constraints}, bbox_states={not bbox_states[camera_idx][idx]}, post_sent={not post_sent[camera_idx][idx]}")