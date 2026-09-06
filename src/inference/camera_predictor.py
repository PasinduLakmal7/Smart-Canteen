import time
from pathlib import Path
from typing import Optional, Union
import cv2

from src.utils.logging import app_logger
from src.inference.detector import FoodDetector
from src.inference.image_predictor import draw_annotations

def run_camera_stream(
    camera_index: int = 0,
    model_path: Optional[Union[str, Path]] = None,
    conf_threshold: Optional[float] = None
):
    """
    Opens live webcam stream and performs real-time food recognition.
    """
    app_logger.info(f"Initializing FoodDetector for webcam index {camera_index}...")
    detector = FoodDetector(model_path=model_path, conf_threshold=conf_threshold)

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        app_logger.error(f"Cannot open webcam with index {camera_index}")
        print(f"\n[ERROR] Unable to access camera at index {camera_index}. Please check device permissions.\n")
        return

    window_name = "Smart Canteen - Realtime Food Recognition"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 960, 720)

    print("\n" + "=" * 60)
    print(" 📹 Smart Canteen Real-Time Food Detection Active")
    print(" Press 'Q' or 'ESC' in the camera window to EXIT.")
    print("=" * 60 + "\n")

    prev_time = time.time()
    fps = 0.0

    while True:
        ret, frame = cap.read()
        if not ret:
            app_logger.warning("Failed to grab video frame.")
            break

        # Inference
        t0 = time.time()
        detections = detector.detect(frame)
        latency_ms = (time.time() - t0) * 1000.0

        # Calculate FPS
        curr_time = time.time()
        fps = 0.9 * fps + 0.1 * (1.0 / max(1e-5, (curr_time - prev_time)))
        prev_time = curr_time

        # Draw detections
        annotated_frame = draw_annotations(frame, detections)

        # Draw HUD info overlay
        h, w = annotated_frame.shape[:2]
        cv2.rectangle(annotated_frame, (0, 0), (w, 40), (20, 20, 20), cv2.FILLED)
        info_str = f"FPS: {fps:.1f} | Latency: {latency_ms:.1f}ms | Detected: {len(detections)} items"
        cv2.putText(annotated_frame, info_str, (15, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 200), 2)

        cv2.imshow(window_name, annotated_frame)
        key = cv2.waitKey(1) & 0xFF
        if key in [ord('q'), ord('Q'), 27]:
            break

    cap.release()
    cv2.destroyAllWindows()
    app_logger.info("Webcam stream terminated by user.")
