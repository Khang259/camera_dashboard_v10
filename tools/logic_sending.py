import requests
import threading
import time
import logging
from threading import Lock

# Setup logging
logging.basicConfig(
    filename='logs/rtsp_reader.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Dictionary to store thread states
pending_threads = {}

# Dictionary to store Locks for each end_task_path
end_task_locks = {
    "10000170": Lock(),
    "10000171": Lock(),
    "10000140": Lock(),
    "10000141": Lock(),
    "10000164": Lock(),
    "10000147": Lock()
}

def send_post_request(start_task_path, end_task_path, camera_idx, bbox_idx, api_url):
    logging.debug(f"[Camera {camera_idx + 1}] Preparing to send POST request to {api_url}")
    """Send POST request to the API with task path details."""
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
        logging.info(f"[Camera {camera_idx + 1}] Sent POST request for Bounding box {bbox_idx + 1}:")
        logging.info(f"  - Status code: {response.status_code}")
        logging.info(f"  - Response: {response.text}")
        print(f"\n[Camera {camera_idx + 1}] Sent POST request for Bounding box {bbox_idx + 1}:")
        print(f"  - Status code: {response.status_code}")
        print(f"  - Response: {response.text}")
    except requests.exceptions.RequestException as e:
        logging.error(f"[Camera {camera_idx + 1}] Error sending POST request: {e}")
        print(f"\n[Camera {camera_idx + 1}] Error sending POST request: {e}")

def check_and_send_post_request(camera_idx, idx, task_path, bbox_states, post_sent, empty_end_task_paths, has_start_task_paths, task_path_constraints, api_url):
    """Check conditions and send POST request if applicable with Lock for each end_task_path."""
    if task_path in task_path_constraints and not bbox_states[camera_idx][idx] and not post_sent[camera_idx][idx]:
        # Acquire Lock for the specific end_task_path
        logging.debug(f"[Camera {camera_idx + 1}] Attempting to acquire lock for {task_path}")
        logging.debug(f"[Camera {camera_idx + 1}] task_path={task_path}, in_task_path_constraints={task_path in task_path_constraints}")
        logging.debug(f"[Camera {camera_idx + 1}] bbox_states[{camera_idx}][{idx}]={bbox_states[camera_idx][idx]}, post_sent[{camera_idx}][{idx}]={post_sent[camera_idx][idx]}")
        logging.debug(f"[Camera {camera_idx + 1}] allowed_start_paths={task_path_constraints.get(task_path, [])}, has_start_task_paths={has_start_task_paths}")
        with end_task_locks[task_path]:
            logging.debug(f"[Camera {camera_idx + 1}] Acquired lock for {task_path}")
            logging.debug(f"[Camera {camera_idx + 1}] pending_threads={pending_threads}")
            allowed_start_paths = task_path_constraints.get(task_path, [])
            for start_camera_idx in range(len(has_start_task_paths)):
                for start_task_path in has_start_task_paths[start_camera_idx]:
                    if start_task_path in allowed_start_paths:
                        logging.info(f"[Camera {camera_idx + 1}] Detected empty end_task_path {task_path} and start_task_path {start_task_path} with cargo")
                        print(f"\n[Camera {camera_idx + 1}] Detected empty end_task_path {task_path} and start_task_path {start_task_path} with cargo")

                        def delayed_post_request():
                            logging.debug(f"[Camera {camera_idx + 1}] Started delayed_post_request for {task_path}")
                            try:
                                logging.debug(f"[Camera {camera_idx + 1}] Started delayed at {time.time()}")
                                start_time = time.time()
                                initial_empty_state = task_path in empty_end_task_paths[camera_idx]
                                initial_start_state = start_task_path in has_start_task_paths[start_camera_idx]
                                time.sleep(5)  # Giảm thời gian chờ
                                end_time = time.time()
                                logging.debug(f"[Camera {camera_idx + 1}] Waited {end_time - start_time}s")
                                logging.info(f"[Camera {camera_idx + 1}] Checking conditions after 5s for {task_path}")
                                logging.debug(f"[Camera {camera_idx + 1}] Real time after sleep: {time.time()}")
                                with end_task_locks[task_path]:
                                    logging.info(f"[Camera {camera_idx + 1}] Condition: task_path={task_path} in empty_end_task_paths={task_path in empty_end_task_paths[camera_idx]}, start_task_path={start_task_path} in has_start_task_paths={start_task_path in has_start_task_paths[start_camera_idx]}")
                                    logging.debug(f"[Camera {camera_idx + 1}] Initial states: empty={initial_empty_state}, start={initial_start_state}")
                                    if initial_empty_state and initial_start_state:
                                        logging.info(f"[Camera {camera_idx + 1}] Using initial states to send POST")
                                        send_post_request(start_task_path, task_path, camera_idx, idx, api_url)
                                        post_sent[camera_idx][idx] = True
                                        empty_end_task_paths[camera_idx].discard(task_path)
                                if task_path in pending_threads:
                                    del pending_threads[task_path]
                                    logging.debug(f"[Camera {camera_idx + 1}] Removed thread state for {task_path}")
                            except Exception as e:
                                logging.error(f"[Camera {camera_idx + 1}] Error in delayed_post_request: {e}")
                                if task_path in pending_threads:
                                    del pending_threads[task_path]
                                    logging.debug(f"[Camera {camera_idx + 1}] Removed thread state for {task_path}")

                        if task_path not in pending_threads:
                            pending_threads[task_path] = True
                            logging.debug(f"[Camera {camera_idx + 1}] Creating thread for delayed_post_request for {task_path}")
                            threading.Thread(target=delayed_post_request, daemon=True).start()
                        break