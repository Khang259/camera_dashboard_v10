import cv2
import numpy as np
import ffmpeg
import threading
import queue
import json
import logging
import time
import os
from logic_sending import send_post_request, check_and_send_post_request

# Setup logger
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)
logger = logging.getLogger('checking_corner')
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(os.path.join(log_dir, 'checking_corner.log'))
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

rtsp_urls = config['rtsp_urls']
bboxes_list = [np.array(bbox, dtype=int) for bbox in config['bboxes']]
frame_size = config['frame_size']
bbox_to_taskpath = {tuple(map(int, k.split('_'))): v for k, v in config['bbox_to_taskpath'].items()}
start_task_paths = set(config['start_task_paths'])
end_task_paths = set(config['end_task_paths'])
task_path_constraints = config['task_path_constraints']

# Global display queue
display_queue = queue.Queue(maxsize=20)

def read_rtsp_stream(rtsp_url, frame_queue, camera_idx, width, height, stop_event):
    """Read RTSP stream and put frames into the queue."""
    while not stop_event.is_set():
        try:
            process = (
                ffmpeg
                .input(rtsp_url, rtsp_transport='tcp', rtsp_flags='prefer_tcp', buffer_size=500000, max_delay=500000, timeout=5000000)
                .output('pipe:', format='rawvideo', pix_fmt='bgr24', loglevel='error')
                .run_async(pipe_stdout=True)
            )
            logger.info(f"[Camera {camera_idx + 1}] Initialized FFmpeg for RTSP: {rtsp_url}")
            print(f"[Camera {camera_idx + 1}] Initialized FFmpeg for RTSP: {rtsp_url}")

            while not stop_event.is_set():
                in_bytes = process.stdout.read(width * height * 3)
                if not in_bytes:
                    logger.error(f"[Camera {camera_idx + 1}] No data read from FFmpeg, retrying")
                    print(f"[Camera {camera_idx + 1}] No data read from FFmpeg, retrying")
                    break
                frame = np.frombuffer(in_bytes, np.uint8).reshape((height, width, 3))
                if frame is None or frame.size == 0:
                    logger.error(f"[Camera {camera_idx + 1}] Invalid or empty frame")
                    continue
                try:
                    frame_queue.put((camera_idx, frame), timeout=1)
                    # logger.debug(f"[Camera {camera_idx + 1}] Frame added to queue")
                except queue.Full:
                    logger.warning(f"[Camera {camera_idx + 1}] Frame queue full, skipping frame")
                time.sleep(0.01)  # Reduce CPU usage
            process.communicate()
        except Exception as e:
            logger.error(f"[Camera {camera_idx + 1}] FFmpeg error: {str(e)}, retrying in 1 second")
            print(f"[Camera {camera_idx + 1}] FFmpeg error: {str(e)}, retrying in 1 second")
            time.sleep(1)

def process_frame(camera_idx, frame_queue, bboxes, bbox_states, last_detection_time, post_sent, empty_end_task_paths, has_start_task_paths):
    """Process frames, detect cargo, and handle task path logic."""
    frame_count = 0
    while True:
        try:
            cam_idx, frame = frame_queue.get(timeout=3)
            if cam_idx != camera_idx:
                continue
            frame_count += 1
            if frame_count % 3 != 0:  # Skip 3/5 frames
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            output_frame = frame.copy()

            for idx, (x1, y1, x2, y2) in enumerate(bboxes):
                roi = gray[y1:y2, x1:x2]
                blurred = cv2.GaussianBlur(roi, (5, 5), 0)
                edges = cv2.Canny(blurred, 100, 200)
                lines = cv2.HoughLinesP(
                    edges,
                    rho=1,
                    theta=np.pi/180,
                    threshold=50,
                    minLineLength=50,
                    maxLineGap=10
                )

                task_path = bbox_to_taskpath.get((x1, y1, x2, y2), "Unknown")
                current_time = time.time()

                if lines is not None:
                    logger.debug(f"[Camera {camera_idx + 1}] detected cargo for task_path={task_path}")
                    # Cargo detected
                    if not bbox_states[camera_idx][idx]:
                        bbox_states[camera_idx][idx] = True
                        last_detection_time[camera_idx][idx] = current_time
                        post_sent[camera_idx][idx] = False
                        logger.info(f"[Camera {camera_idx + 1}] Bounding box {idx + 1}: Cargo detected")
                        logger.info(f"  - TaskPath: {task_path}")
                        print(f"\n[Camera {camera_idx + 1}] Bounding box {idx + 1}: Cargo detected")
                        print(f"  - TaskPath: {task_path}")
                        for i, line in enumerate(lines):
                            x1_line, y1_line, x2_line, y2_line = line[0]

                        if task_path in start_task_paths:
                            has_start_task_paths[camera_idx].add(task_path)
                            logger.debug(f"[Camera {camera_idx + 1}] Added {task_path} to has_start_task_paths={has_start_task_paths[camera_idx]}")

                    for i, line in enumerate(lines):
                        x1_line, y1_line, x2_line, y2_line = line[0]
                        cv2.line(
                            output_frame[y1:y2, x1:x2],
                            (x1_line, y1_line),
                            (x2_line, y2_line),
                            (0, 255, 0),
                            2
                        )
                    cv2.putText(
                        output_frame,
                        "Cargo",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2
                    )
                else:
                    # No cargo
                    logger.debug(f"[Camera {camera_idx + 1}] No cargo for task_path={task_path}")
                    if bbox_states[camera_idx][idx]:
                        bbox_states[camera_idx][idx] = False
                        post_sent[camera_idx][idx] = False
                        logger.info(f"[Camera {camera_idx + 1}] Bounding box {idx + 1}: No cargo")
                        logger.info(f"  - TaskPath: {task_path}")
                        print(f"\n[Camera {camera_idx + 1}] Bounding box {idx + 1}: No cargo")
                        print(f"  - TaskPath: {task_path}")

                        if task_path in end_task_paths:
                            empty_end_task_paths[camera_idx].add(task_path)
                            logger.debug(f"[Camera {camera_idx + 1}] Added {task_path} to empty_end_task_  paths")
                        if task_path in start_task_paths:
                            has_start_task_paths[camera_idx].discard(task_path)
                            logger.debug(f"[Camera {camera_idx + 1}] Removed {task_path} from has_start_task_paths")

                check_and_send_post_request(
                    camera_idx, idx, task_path, bbox_states, post_sent,
                    empty_end_task_paths, has_start_task_paths, task_path_constraints, config['api_url']
                )

                cv2.rectangle(output_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

            try:
                display_queue.put((camera_idx, output_frame), timeout=1)
                logger.debug(f"[Camera {camera_idx + 1}] Processed frame sent to display queue")
            except queue.Full:
                logger.warning(f"[Camera {camera_idx + 1}] Display queue full, skipping frame")
        except queue.Empty:
            logger.warning(f"[Camera {camera_idx + 1}] Frame queue empty, waiting for new frame")

def main():
    """Main function to initialize and run the cargo detection system."""
    frame_queues = [queue.Queue(maxsize=20) for _ in rtsp_urls]
    stop_event = threading.Event()

    # Initialize states
    bbox_states = {i: {j: False for j in range(len(bboxes_list[i]))} for i in range(len(rtsp_urls))}
    last_detection_time = {i: {j: 0 for j in range(len(bboxes_list[i]))} for i in range(len(rtsp_urls))}
    post_sent = {i: {j: False for j in range(len(bboxes_list[i]))} for i in range(len(rtsp_urls))}
    empty_end_task_paths = {i: set() for i in range(len(rtsp_urls))}
    has_start_task_paths = {i: set() for i in range(len(rtsp_urls))}

    threads = []
    for i, rtsp_url in enumerate(rtsp_urls):
        t = threading.Thread(
            target=read_rtsp_stream,
            args=(rtsp_url, frame_queues[i], i, frame_size['width'], frame_size['height'], stop_event)
        )
        t.daemon = True
        t.start()
        threads.append(t)
        logger.info(f"[Camera {i + 1}] Started RTSP reading thread")
        print(f"[Camera {i + 1}] Started RTSP reading thread")

    for i in range(len(rtsp_urls)):
        t = threading.Thread(
            target=process_frame,
            args=(i, frame_queues[i], bboxes_list[i], bbox_states, last_detection_time, post_sent, empty_end_task_paths, has_start_task_paths)
        )
        t.daemon = True
        t.start()
        threads.append(t)
        logger.info(f"[Camera {i + 1}] Started frame processing thread")
        print(f"[Camera {i + 1}] Started frame processing thread")

    try:
        while not stop_event.is_set():
            try:
                camera_idx, frame = display_queue.get(timeout=1)
                output_frame_resized = cv2.resize(frame, (frame_size['width'], frame_size['height']))
                cv2.imshow(f'Cargo Detection - Camera {camera_idx + 1}', output_frame_resized)
            except queue.Empty:
                pass

            if cv2.waitKey(1) & 0xFF == ord('q'):
                stop_event.set()
                break
    finally:
        for q in frame_queues:
            while not q.empty():
                q.get()
        while not display_queue.empty():
            display_queue.get()
        cv2.destroyAllWindows()
        logger.info("Stopped all threads and closed windows")
        print("Stopped all threads and closed windows")

if __name__ == '__main__':
    main()