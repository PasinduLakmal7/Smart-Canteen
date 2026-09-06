import os
import argparse
import json
import cv2
from src.food_detection.detector import FoodDetector
from src.utils.logger import logger
from src.utils.image_utils import draw_detections, save_image
from src.utils.helpers import load_yaml

def main():
    parser = argparse.ArgumentParser(description="Run YOLO food detection inference on an image.")
    parser.add_argument(
        "--source",
        type=str,
        required=True,
        help="Path to the input image file."
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Path to YOLO model checkpoint (.pt). Defaults to path in app_config.yaml"
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=None,
        help="Confidence threshold override."
    )
    parser.add_argument(
        "--save-dir",
        type=str,
        default=None,
        help="Directory to save output image. Defaults to path in app_config.yaml"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        app_config = load_yaml("configs/app_config.yaml")
        default_model_path = os.path.join(
            app_config["paths"]["model_dir"], "best.pt"
        )
        default_save_dir = app_config["paths"]["output_dir"]
    except Exception as e:
        logger.warning(f"Could not load app_config.yaml: {e}. Using fallback defaults.")
        default_model_path = os.path.join("models", "food_detection", "best.pt")
        default_save_dir = os.path.join("outputs", "detections")

    model_path = args.model if args.model is not None else default_model_path
    save_dir = args.save_dir if args.save_dir is not None else default_save_dir

    logger.info(f"Target Source Image: {args.source}")
    logger.info(f"Model Checkpoint: {model_path}")

    # Check model path
    if not os.path.exists(model_path):
        logger.error(f"Model checkpoint file not found: {model_path}")
        logger.error("Please train the model first or place the 'best.pt' checkpoint inside the models folder.")
        print(f"\n[ERROR] Model file not found at: {os.path.abspath(model_path)}")
        print("Please check your model path or copy your Google Colab trained model 'best.pt' here.")
        return

    try:
        # Initialize detector
        detector = FoodDetector(model_path=model_path, conf_threshold=args.conf)
        
        # Load image (we do it here to capture raw frame for annotations)
        raw_image = cv2.imread(args.source)
        if raw_image is None:
            logger.error(f"Failed to read image from source path: {args.source}")
            print(f"\n[ERROR] Failed to load image: {args.source}")
            return

        # Perform detection
        detections = detector.detect_frame(raw_image)
        
        # Print results to stdout in structured format
        print("\n--- Detection Results ---")
        print(json.dumps(detections, indent=4))
        print("-------------------------\n")
        
        # Draw bounding boxes and save the image
        annotated_image = draw_detections(raw_image, detections)
        
        # Build destination filename
        filename = os.path.basename(args.source)
        name, ext = os.path.splitext(filename)
        out_filename = f"{name}_detected{ext}"
        out_path = os.path.join(save_dir, out_filename)
        
        # Save image
        save_success = save_image(annotated_image, out_path)
        if save_success:
            print(f"[SUCCESS] Annotated image saved to: {os.path.abspath(out_path)}")
            
    except Exception as e:
        logger.exception("An error occurred during CLI inference:")
        print(f"\n[ERROR] Inference failed: {e}")

if __name__ == "__main__":
    main()
