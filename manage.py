#!/usr/bin/env python
"""
Smart Canteen Food Recognition Subsystem — Master CLI Entrypoint
Unified manager for data preparation, interactive annotation review,
training, evaluation, candidate promotion, inference, and web application.
"""

import sys
import os
import argparse
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.paths import ensure_project_structure, APPLICATION_CONFIG_PATH
from src.utils.logging import app_logger

def cmd_status(args):
    """Displays dataset status, registered classes, and production model info."""
    from tools.dataset_report import generate_report
    from src.training.trainer import YOLO11Trainer
    from src.training.model_manager import ModelManager

    ensure_project_structure()
    generate_report()

    # Hardware Info
    trainer = YOLO11Trainer()
    hw = trainer.detect_hardware()
    print("[+] System Hardware:")
    print(f"   * Device: {hw['device_name']}")
    print(f"   * Recommended Batch: {hw['recommended_batch']} | Workers: {hw['recommended_workers']}\n")

    # Model Info
    mm = ModelManager()
    prod = mm.registry.get("production_model")
    print("[+] Production Model Status:")
    if prod:
        print(f"   * Candidate ID : {prod.get('candidate_id')}")
        print(f"   * Promoted At  : {prod.get('promoted_at')}")
        print(f"   * Classes      : {len(prod.get('classes', []))} categories")
        print(f"   * Path         : {prod.get('production_path')}")
    else:
        print("   * No active production model promoted yet.")
        print("   * Train a model with: python manage.py train --mode smoke")
    print("=" * 65 + "\n")

def cmd_prepare_data(args):
    """Scans, validates, deduplicates, and splits dataset into YOLO format."""
    from src.dataset import DatasetPipeline
    ensure_project_structure()
    print("\n[+] Running Automated Dataset Preparation Pipeline...")
    pipeline = DatasetPipeline()
    result = pipeline.run(auto_approve_unreviewed=not args.require_manual_review)
    if result.get("success"):
        print("\n[SUCCESS] Dataset Preparation Completed Successfully!")
        print(f"   * Total Images Validated : {result.get('valid_images')}")
        print(f"   * Unique Images          : {result.get('unique_images')}")
        print(f"   * Approved & Exported    : {result.get('approved_images')}")
        print(f"   * Splits (Train/Val/Test): {result.get('splits', {}).get('train')}/{result.get('splits', {}).get('valid')}/{result.get('splits', {}).get('test')}")
        print(f"   * data.yaml Location     : {result.get('data_yaml')}\n")
    else:
        print(f"\n[WARNING] Dataset Preparation: {result.get('message')}\n")

def cmd_review(args):
    """Launches the interactive annotation review GUI."""
    from tools.review_annotations import review_cli
    ensure_project_structure()
    review_cli()

def cmd_train(args):
    """Trains the YOLO11 food detection model."""
    from src.training.trainer import YOLO11Trainer
    from src.training.model_manager import ModelManager
    from src.training.evaluator import ModelEvaluator

    ensure_project_structure()
    trainer = YOLO11Trainer()
    res = trainer.train(
        mode=args.mode,
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        resume=args.resume,
        resume_weights=args.weights
    )

    if res.get("success"):
        print("\n[SUCCESS] Training completed successfully!")
        best_pt = Path(res["best_weights"])

        # Auto-register candidate
        if best_pt.exists():
            mm = ModelManager()
            evaluator = ModelEvaluator()
            try:
                metrics = evaluator.evaluate(model_path=best_pt, split="val")
            except Exception:
                metrics = {}
            cand = mm.register_candidate(res["run_name"], best_pt, metrics=metrics)
            print(f"[*] Registered Candidate: {cand['candidate_id']}")
            print(f"[*] Run 'python manage.py promote-model' to make this the active production model.\n")

def cmd_evaluate(args):
    """Evaluates a model checkpoint against validation/test dataset."""
    from src.training.evaluator import ModelEvaluator
    ensure_project_structure()
    evaluator = ModelEvaluator()
    results = evaluator.evaluate(model_path=args.model, split=args.split)
    print("\n[+] Evaluation Summary:")
    print(f"   * mAP @ 0.50     : {results['map50']:.4f}")
    print(f"   * mAP @ 0.5:0.95 : {results['map50_95']:.4f}")
    print(f"   * Precision      : {results['precision']:.4f}")
    print(f"   * Recall         : {results['recall']:.4f}")
    print(f"   * F1 Score       : {results['f1_score']:.4f}")
    print(f"\n[*] View full HTML dashboard at: reports/model_evaluation.html\n")

def cmd_promote_model(args):
    """Promotes candidate model to models/production/best.pt."""
    from src.training.model_manager import ModelManager
    ensure_project_structure()
    mm = ModelManager()
    try:
        record = mm.promote_candidate(candidate_id=args.candidate)
        print("\n[SUCCESS] Model Promotion Successful!")
        print(f"   * Promoted Candidate : {record['candidate_id']}")
        print(f"   * Production Path    : {record['production_path']}\n")
    except Exception as e:
        print(f"\n[ERROR] Error during model promotion: {e}\n")

def cmd_predict(args):
    """Predicts food items in a single image."""
    from src.inference.image_predictor import predict_single_image
    ensure_project_structure()
    res = predict_single_image(
        image_path=args.image,
        model_path=args.model,
        conf_threshold=args.conf
    )
    print("\n[+] Food Detection Result:")
    print("=" * 40)
    if not res["detections"]:
        print("No registered food items detected above threshold.")
    else:
        for d in res["detections"]:
            print(f"* {d['food_name'].replace('_', ' ').title():<20} : {d['confidence'] * 100:.1f}% confidence")
    print("=" * 40)
    print(f"Annotated Image Saved: {res['output_image']}\n")

def cmd_predict_folder(args):
    """Batch predicts all images in a folder."""
    from src.inference.image_predictor import predict_folder
    ensure_project_structure()
    res = predict_folder(
        folder_path=args.folder,
        model_path=args.model,
        conf_threshold=args.conf
    )
    print("\n[+] Batch Prediction Completed:")
    print(f"   * Images Processed : {res['total_images']}")
    print(f"   * Total Detections : {res['total_detections']}")
    print(f"   * Results Summary  : {res['results_csv']}")
    print(f"   * Output Directory : {res['output_dir']}\n")

def cmd_camera(args):
    """Runs real-time webcam detection."""
    from src.inference.camera_predictor import run_camera_stream
    ensure_project_structure()
    run_camera_stream(
        camera_index=args.camera,
        model_path=args.model,
        conf_threshold=args.conf
    )

def cmd_app(args):
    """Starts the FastAPI web application server."""
    import uvicorn
    import yaml
    ensure_project_structure()

    host = "127.0.0.1"
    port = 8000
    if APPLICATION_CONFIG_PATH.exists():
        try:
            with open(APPLICATION_CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = (yaml.safe_load(f) or {}).get("server", {})
                host = args.host or cfg.get("host", host)
                port = args.port or cfg.get("port", port)
        except Exception:
            pass

    print(f"\n🍱 Starting Smart Canteen Food Detection UI on http://{host}:{port}")
    print("Press CTRL+C to stop the server.\n")
    uvicorn.run("src.application.app:app", host=host, port=port, reload=True)

def cmd_export_colab(args):
    """Packages processed dataset into dataset_colab.zip for seamless Google Colab GPU training."""
    import zipfile
    import yaml
    from src.dataset import DatasetPipeline
    from src.utils.paths import PROCESSED_DATA_DIR, DATA_DIR

    ensure_project_structure()
    print("\n[+] Preparing dataset for Google Colab GPU training...")
    pipeline = DatasetPipeline()
    pipeline.run(auto_approve_unreviewed=True)

    colab_zip_path = DATA_DIR / "dataset_colab.zip"
    print(f"[*] Packaging dataset into {colab_zip_path}...")

    # Load exact class mapping from data/processed/data.yaml
    processed_yaml_path = PROCESSED_DATA_DIR / "data.yaml"
    if processed_yaml_path.exists():
        with open(processed_yaml_path, "r", encoding="utf-8") as f:
            base_cfg = yaml.safe_load(f) or {}
            colab_yaml = dict(base_cfg)
            colab_yaml["path"] = "/content/dataset"
    else:
        colab_yaml = {
            "path": "/content/dataset",
            "train": "train/images",
            "val": "valid/images",
            "test": "test/images",
            "names": {0: "food"}
        }

    with zipfile.ZipFile(colab_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Write custom Colab data.yaml
        zf.writestr("data.yaml", yaml.dump(colab_yaml, sort_keys=False))
        # Add all train, valid, test images and labels
        for split in ["train", "valid", "test"]:
            for folder in ["images", "labels"]:
                dir_to_zip = PROCESSED_DATA_DIR / split / folder
                if dir_to_zip.exists():
                    for file_p in dir_to_zip.glob("*.*"):
                        arcname = f"{split}/{folder}/{file_p.name}"
                        zf.write(file_p, arcname)

    size_mb = colab_zip_path.stat().st_size / (1024 * 1024)
    names_dict = colab_yaml.get("names", {})
    print(f"\n[SUCCESS] Google Colab Dataset Bundle Created!")
    print(f"   * Location : {colab_zip_path}")
def cmd_db_init(args):
    """Initializes the SQLite database tables and schema."""
    from database.connection import init_database
    ensure_project_structure()
    init_database()
    print("\n[SUCCESS] SQLite Database Schema & Tables Initialized!")


def cmd_db_seed(args):
    """Seeds the SQLite database with standardized Sri Lankan food nutrition and pricing."""
    from database.seed.seed_runner import seed_database_if_empty
    ensure_project_structure()
    count = seed_database_if_empty()
    print(f"\n[SUCCESS] Database Seed Complete: {count} food items ready.")


def main():
    parser = argparse.ArgumentParser(
        description="Smart Canteen AI — Food Recognition, Nutrition & Billing Subsystem Master CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # db-init
    p_dbinit = subparsers.add_parser("db-init", help="Initialize SQLite database schema and tables")
    p_dbinit.set_defaults(func=cmd_db_init)

    # db-seed
    p_dbseed = subparsers.add_parser("db-seed", help="Seed database with Sri Lankan food nutrition & pricing records")
    p_dbseed.set_defaults(func=cmd_db_seed)

    # export-colab
    p_colab = subparsers.add_parser("export-colab", help="Bundle processed dataset into dataset_colab.zip for Google Colab GPU training")
    p_colab.set_defaults(func=cmd_export_colab)

    # status
    p_status = subparsers.add_parser("status", help="Show dataset, model, and system hardware status")
    p_status.set_defaults(func=cmd_status)

    # prepare-data
    p_prep = subparsers.add_parser("prepare-data", help="Scan, validate, deduplicate, and split dataset into YOLO format")
    p_prep.add_argument("--require-manual-review", action="store_true", help="Do not auto-approve auto-suggested boxes")
    p_prep.set_defaults(func=cmd_prepare_data)

    # review
    p_rev = subparsers.add_parser("review", help="Launch interactive annotation review GUI")
    p_rev.set_defaults(func=cmd_review)

    # train
    p_train = subparsers.add_parser("train", help="Train YOLO11 model locally")
    p_train.add_argument("--mode", choices=["smoke", "baseline", "final"], default="baseline", help="Training mode")
    p_train.add_argument("--epochs", type=int, default=None, help="Override epoch count")
    p_train.add_argument("--batch", type=int, default=None, help="Override batch size")
    p_train.add_argument("--imgsz", type=int, default=640, help="Input image size (default: 640)")
    p_train.add_argument("--resume", action="store_true", help="Resume interrupted training")
    p_train.add_argument("--weights", type=str, default=None, help="Weights to resume from (default: last.pt)")
    p_train.set_defaults(func=cmd_train)

    # evaluate
    p_eval = subparsers.add_parser("evaluate", help="Evaluate model checkpoint against validation or test split")
    p_eval.add_argument("--model", type=str, default=None, help="Model checkpoint path (defaults to production)")
    p_eval.add_argument("--split", choices=["val", "test"], default="val", help="Split to evaluate on")
    p_eval.set_defaults(func=cmd_evaluate)

    # promote-model
    p_prom = subparsers.add_parser("promote-model", help="Promote candidate model to models/production/best.pt")
    p_prom.add_argument("--candidate", type=str, default=None, help="Candidate ID to promote (default: latest)")
    p_prom.set_defaults(func=cmd_promote_model)

    # predict
    p_pred = subparsers.add_parser("predict", help="Run food recognition on a single image")
    p_pred.add_argument("image", type=str, help="Path to input image file")
    p_pred.add_argument("--model", type=str, default=None, help="Custom model weights path")
    p_pred.add_argument("--conf", type=float, default=None, help="Confidence threshold")
    p_pred.set_defaults(func=cmd_predict)

    # predict-folder
    p_pred_f = subparsers.add_parser("predict-folder", help="Batch predict all images in a folder")
    p_pred_f.add_argument("folder", type=str, help="Path to folder containing test images")
    p_pred_f.add_argument("--model", type=str, default=None, help="Custom model weights path")
    p_pred_f.add_argument("--conf", type=float, default=None, help="Confidence threshold")
    p_pred_f.set_defaults(func=cmd_predict_folder)

    # camera
    p_cam = subparsers.add_parser("camera", help="Run real-time webcam food recognition")
    p_cam.add_argument("--camera", type=int, default=0, help="Webcam device index (default: 0)")
    p_cam.add_argument("--model", type=str, default=None, help="Custom model weights path")
    p_cam.add_argument("--conf", type=float, default=None, help="Confidence threshold")
    p_cam.set_defaults(func=cmd_camera)

    # app
    p_app = subparsers.add_parser("app", help="Start the Smart Canteen Web UI")
    p_app.add_argument("--host", type=str, default=None, help="Host IP address")
    p_app.add_argument("--port", type=int, default=None, help="Port number (default: 8000)")
    p_app.set_defaults(func=cmd_app)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n[INFO] Operation interrupted by user.")
    except Exception as e:
        app_logger.exception("Command execution error:")
        print(f"\n[ERROR] {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
