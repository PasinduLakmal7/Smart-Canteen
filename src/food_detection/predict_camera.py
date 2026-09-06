import os
import argparse
import cv2
from src.food_detection.detector import FoodDetector
from src.utils.logger import logger
from src.utils.image_utils import draw_detections
from src.utils.helpers import load_yaml

def run_camera_inference():
    parser = argparse.ArgumentParser(description="Run YOLO food detection inference on local webcam or video.")
    parser.add_argument(
        "--source",
        type=str,
        default="0",
        help="Camera index (e.g. 0) or path to a video file."
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Path to YOLO model checkpoint (.pt)."
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=None,
        help="Confidence threshold override."
    )
    
    args = parser.parse_args()

    # Load configuration
    try:
        app_config = load_yaml("configs/app_config.yaml")
        default_model_path = os.path.join(
            app_config["paths"]["model_dir"], "best.pt"
        )
    except Exception as e:
        logger.warning(f"Could not load app_config.yaml: {e}. Using fallback default model path.")
        default_model_path = os.path.join("models", "food_detection", "best.pt")

    model_path = args.model if args.model is not None else default_model_path

    # Check model path
    if not os.path.exists(model_path):
        logger.error(f"Model checkpoint file not found: {model_path}")
        print(f"\n[ERROR] Model file not found at: {os.path.abspath(model_path)}")
        print("Please train the model first or place the 'best.pt' checkpoint inside the models folder.")
        return

    try:
        # Initialize detector
        detector = FoodDetector(model_path=model_path, conf_threshold=args.conf)
        
        # Decide if source is camera index or file path
        source_input = args.source
        if source_input.isdigit():
            source_input = int(source_input)
            logger.info(f"Opening camera stream: Index {source_input}")
        else:
            logger.info(f"Opening video file: {source_input}")

        # Open video stream
        cap = cv2.VideoCapture(source_input)
        if not cap.isOpened():
            logger.error(f"Failed to open video source: {args.source}")
            print(f"\n[ERROR] Failed to open video source: {args.source}")
            return

        print("\n" + "="*50)
        print("Starting Live Food Detection...")
        print("Press 'q' key in the video window to EXIT.")
        print("="*50 + "\n")

        window_name = "AI Smart Canteen - Food Detection"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

        while True:
            ret, frame = cap.read()
            if not ret:
                logger.info("Video feed ended or failed to capture frame.")
                break

            # Perform detection
            detections = detector.detect_frame(frame)

            # Draw detections
            annotated_frame = draw_detections(frame, detections)

            # Show annotated frame
            cv2.imshow(window_name, annotated_frame)

            # Check for quit key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                logger.info("User closed live stream window.")
                break

        cap.release()
        cv2.destroyAllWindows()
        print("Video stream closed successfully.")
        
    except Exception as e:
        logger.exception("An error occurred during video inference:")
        print(f"\n[ERROR] Live inference failed: {e}")

if __name__ == "__main__":
    run_camera_inference()
