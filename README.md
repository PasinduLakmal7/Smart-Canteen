# Sri Lankan Smart Canteen Food Recognition Subsystem

Research-oriented title:
> *"An Intelligent Multi-Modal AI Framework for Automated Food Recognition, Nutrition Assessment and Personalized Meal Recommendation in Smart Canteen Environments"*

---

## 🎯 1. Overview & Single-Command Workflow

The Food Recognition subsystem is designed to be **fully automated and modular**. As a developer or canteen administrator, your primary workflow is:

```text
1. Add food photos into category folders:
   data/raw/string_hoppers/
   data/raw/kottu/
   data/raw/pittu/
   ...
2. Run data preparation:
   python manage.py prepare-data

3. (Optional) Review/adjust annotations:
   python manage.py review

4. Train YOLO11 locally:
   python manage.py train --mode smoke     # (or --mode baseline / --mode final)

5. Evaluate candidate model:
   python manage.py evaluate

6. Promote to production:
   python manage.py promote-model

7. Launch Web Application or Webcam:
   python manage.py app
   # or
   python manage.py camera
```

You **never need to manually manage**:
* Class IDs or mapping configurations
* Creating train/valid/test folders
* Writing YOLO normalized bounding box coordinates
* Crafting `data.yaml`
* Retraining checks (handled via dataset fingerprinting)
* Moving `.pt` checkpoints manually

---

## 📂 2. Project Folder Structure

```text
smart-canteen-food/
│
├── README.md                           # Documentation & user guide
├── requirements.txt                    # Project dependencies
├── pyproject.toml                      # Package specifications
├── .gitignore                          # Excludes datasets, model weights, runs, and caches
├── .env.example / .env                 # Environment configurations
├── manage.py                           # Master CLI Entrypoint
│
├── configs/
│   ├── classes.yaml                    # Deterministic registered food classes
│   ├── training.yaml                   # YOLO hyperparameters & CPU resource controls
│   └── application.yaml                # Web UI & inference settings
│
├── data/
│   ├── raw/                            # Raw images organized by category (<food_class>/img_xxx.jpg)
│   ├── annotations/                    # JSON annotation files (<image_id>.json)
│   ├── processed/                      # Auto-generated YOLO training splits
│   │   ├── train/ (images, labels)
│   │   ├── valid/ (images, labels)
│   │   ├── test/  (images, labels)
│   │   └── data.yaml                   # Dataset descriptor for YOLO11
│   ├── rejected/                       # Quarantined corrupted or unreadable images
│   └── manifest.json                   # Central dataset state tracking manifest
│
├── models/
│   ├── candidates/                     # Checkpoints from previous training runs
│   ├── production/
│   │   └── best.pt                     # Active production YOLO model
│   └── registry.json                   # Model lineage, mAP metrics, and versioning
│
├── src/
│   ├── dataset/
│   │   ├── scanner.py                  # Dynamic folder and category discovery
│   │   ├── validator.py                # Image integrity & dimension checks
│   │   ├── deduplicator.py             # Exact (SHA256) & visual (dHash) duplicate detection
│   │   ├── annotator.py                # Auto-bounding box suggestion & review tracking
│   │   ├── splitter.py                 # Stratified train/val/test split with fixed random seeds
│   │   ├── exporter.py                 # Exports normalized YOLO format labels & data.yaml
│   │   └── manifest.py                 # Central manifest manager
│   │
│   ├── training/
│   │   ├── trainer.py                  # Adaptive CPU/GPU training (smoke/baseline/final modes)
│   │   ├── evaluator.py                # Model evaluation, per-class metrics & HTML reporting
│   │   └── model_manager.py            # Candidate registration & production promotion
│   │
│   ├── inference/
│   │   ├── detector.py                 # Reusable decoupled FoodDetector class
│   │   ├── image_predictor.py          # Single image & folder batch prediction
│   │   └── camera_predictor.py         # Real-time webcam feed with live FPS overlay
│   │
│   ├── application/
│   │   └── app.py                      # Modern Web Application (FastAPI backend + Glassmorphism UI)
│   │
│   └── utils/
│       ├── logging.py                  # Rotating structured file & console logger
│       ├── hashing.py                  # SHA256 & Perceptual dHash utilities
│       └── paths.py                    # Path resolution & directory manager
│
├── tools/
│   ├── review_annotations.py           # Interactive annotation review GUI
│   └── dataset_report.py               # Dataset summary and health report
│
├── outputs/
│   ├── predictions/                    # Output images and predictions CSV
│   └── logs/                           # System and training log files
│
├── runs/
│   └── food_detection/                 # Timestamped YOLO training outputs
│
├── reports/
│   ├── dataset_validation.json         # Image validation statistics
│   ├── duplicates.json                 # Duplicate image groups report
│   ├── model_evaluation.html           # HTML evaluation report
│   └── evaluations/                    # Historical evaluation JSON metrics
│
└── tests/
    ├── test_dataset.py                 # Tests scanning, validation, deduplication
    ├── test_splitting.py               # Tests stratification & YOLO label math
    ├── test_detector.py                # Tests decoupled FoodDetector service
    └── test_model_manager.py           # Tests model candidate registration & promotion
```

---

## 🚀 3. Quickstart & Installation

### Step 1: Create Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 2: Install Dependencies
```powershell
pip install -r requirements.txt
```

---

## 🛠️ 4. Master CLI Reference (`manage.py`)

| Command | Description |
| :--- | :--- |
| `python manage.py status` | Shows complete dataset health, class counts, hardware specs, and active production model. |
| `python manage.py prepare-data` | Scans `data/raw/`, isolates corrupted images, detects duplicates, auto-suggests boxes, splits data (80/10/10), and exports to `data/processed/`. |
| `python manage.py review` | Opens interactive OpenCV tool to inspect, draw, approve, or reject bounding boxes. |
| `python manage.py train --mode smoke` | Runs a 2-epoch sanity check to verify pipeline end-to-end. |
| `python manage.py train --mode baseline` | Trains a baseline model (15 epochs) with adaptive CPU batch/worker throttling. |
| `python manage.py train --mode final` | Runs full training with early stopping patience. |
| `python manage.py train --resume` | Automatically resumes interrupted training from the latest checkpoint. |
| `python manage.py evaluate` | Evaluates model on validation/test split and generates `reports/model_evaluation.html`. |
| `python manage.py promote-model` | Promotes candidate model to `models/production/best.pt` and updates `models/registry.json`. |
| `python manage.py predict <image_path>` | Runs inference on an image and saves the annotated bounding box image to `outputs/predictions/`. |
| `python manage.py predict-folder <dir>` | Batch processes a directory of images and exports `outputs/predictions/results.csv`. |
| `python manage.py camera` | Launches real-time webcam food recognition. |
| `python manage.py app` | Launches the local Web UI at `http://127.0.0.1:8000`. |

---

## 🧪 5. Running Automated Tests

Run the full test suite with:
```powershell
python -m unittest discover -s tests -p "test_*.py"
```

All 12 automated test cases verify:
* Dynamic category discovery and class registry synchronization.
* Image corruption isolation to `data/rejected/`.
* SHA256 and visual perceptual deduplication.
* Stratified dataset splitting with seed repeatability.
* Accurate mathematical coordinate normalization for YOLO label files.
* Decoupled `FoodDetector` structured output schema.
* Model candidate registration and promotion to `models/production/best.pt`.
