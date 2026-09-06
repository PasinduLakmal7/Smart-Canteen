import os
import argparse
from ultralytics import YOLO
from src.utils.logger import logger
from src.utils.helpers import load_yaml, get_device

def run_training(epochs: int = None, batch_size: int = None, imgsz: int = None):
    """
    Run YOLO training locally.
    """
    # Load configuration
    logger.info("Loading configurations...")
    app_config = load_yaml("configs/app_config.yaml")
    model_config = load_yaml("configs/model_config.yaml")["yolo"]

    dataset_dir = app_config["paths"]["dataset_dir"]
    data_yaml_path = os.path.abspath(os.path.join(dataset_dir, "data.yaml"))

    if not os.path.exists(data_yaml_path):
        logger.error(f"Dataset descriptor file not found at: {data_yaml_path}")
        logger.error("Please ensure the Roboflow dataset is downloaded and in the right folder.")
        raise FileNotFoundError(f"data.yaml not found at {data_yaml_path}")

    # Override config params if arguments are supplied
    train_epochs = epochs if epochs is not None else model_config.get("epochs", 50)
    train_batch = batch_size if batch_size is not None else model_config.get("batch", 16)
    train_imgsz = imgsz if imgsz is not None else model_config.get("imgsz", 640)
    
    # Select hardware device
    device = get_device()
    
    logger.info(f"Base Model: {model_config['model_type']}")
    logger.info(f"Dataset path: {data_yaml_path}")
    logger.info(f"Parameters: Epochs={train_epochs}, Batch={train_batch}, Image Size={train_imgsz}, Device={device}")

    # Load YOLO model
    logger.info("Initializing pre-trained YOLO11 model...")
    model = YOLO(model_config["model_type"])

    # Train
    logger.info("Starting YOLO training pipeline...")
    results = model.train(
        data=data_yaml_path,
        epochs=train_epochs,
        batch=train_batch,
        imgsz=train_imgsz,
        device=device,
        workers=model_config.get("workers", 4),
        save_period=model_config.get("save_period", -1),
        val=model_config.get("val", True),
        project="smart-canteen",
        name="string_hoppers_yolo11"
    )

    logger.info("Training process completed successfully.")
    
    # Report best model path
    best_path = os.path.join("smart-canteen", "string_hoppers_yolo11", "weights", "best.pt")
    if os.path.exists(best_path):
        logger.info(f"Trained checkpoint saved to: {os.path.abspath(best_path)}")
        logger.info("You should copy this checkpoint to models/food_detection/best.pt for local inference.")
    else:
        logger.warning("Could not find standard best.pt save path. Check your training outputs.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Local YOLO11 training script.")
    parser.add_argument("--epochs", type=int, default=None, help="Number of training epochs")
    parser.add_argument("--batch", type=int, default=None, help="Batch size for training")
    parser.add_argument("--imgsz", type=int, default=None, help="Image size for YOLO model")
    
    args = parser.parse_args()
    
    try:
        run_training(epochs=args.epochs, batch_size=args.batch, imgsz=args.imgsz)
    except Exception as e:
        logger.exception("An error occurred during local training:")
