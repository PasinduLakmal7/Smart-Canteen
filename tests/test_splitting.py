import shutil
import tempfile
import unittest
import yaml
from pathlib import Path
from PIL import Image

from src.dataset.splitter import DatasetSplitter
from src.dataset.exporter import YOLOExporter

class TestDatasetSplittingAndExport(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.processed_dir = self.temp_dir / "processed"
        self.classes_cfg = self.temp_dir / "classes.yaml"

        # Create classes configuration
        with open(self.classes_cfg, "w", encoding="utf-8") as f:
            yaml.dump({"classes": ["kottu", "string_hoppers"]}, f)

        # Create mock dummy images
        self.mock_items = []
        for i in range(10):
            p = self.temp_dir / f"sh_{i}.jpg"
            img = Image.new("RGB", (640, 480), color=(100, 100, 100))
            img.save(p)
            self.mock_items.append({
                "id": f"sh_hash_{i}",
                "path": str(p),
                "filename": f"sh_{i}.jpg",
                "class": "string_hoppers",
                "width": 640,
                "height": 480,
                "status": "approved"
            })

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_splitter_distribution_and_stability(self):
        splitter = DatasetSplitter(train_ratio=0.8, val_ratio=0.1, test_ratio=0.1, seed=42)
        split_items = splitter.assign_splits(self.mock_items)

        splits = [it["split"] for it in split_items]
        self.assertEqual(splits.count("train"), 8)
        self.assertEqual(splits.count("valid"), 1)
        self.assertEqual(splits.count("test"), 1)

        # Test stability: when run again with existing assignments, assignments do not change
        split_items_2 = splitter.assign_splits(split_items)
        splits_2 = [it["split"] for it in split_items_2]
        self.assertEqual(splits, splits_2)

    def test_yolo_exporter_generates_correct_labels(self):
        splitter = DatasetSplitter(seed=42)
        split_items = splitter.assign_splits(self.mock_items)

        # Prepare annotations map
        annotations_map = {}
        for it in split_items:
            annotations_map[it["id"]] = {
                "image_id": it["id"],
                "class": it["class"],
                "objects": [
                    {
                        "class": "string_hoppers",
                        "bbox": [64, 48, 576, 432]  # Centered box: 10% margins -> xc=0.5, yc=0.5, w=0.8, h=0.8
                    }
                ]
            }

        exporter = YOLOExporter(processed_dir=self.processed_dir, classes_config_path=self.classes_cfg)
        res = exporter.export(split_items, annotations_map)

        self.assertTrue((self.processed_dir / "data.yaml").exists())
        self.assertEqual(res["counts"]["train"] + res["counts"]["valid"] + res["counts"]["test"], 10)

        # Check a sample exported label file
        label_files = list(self.processed_dir.rglob("*.txt"))
        self.assertGreater(len(label_files), 0)
        with open(label_files[0], "r", encoding="utf-8") as f:
            line = f.readline().strip()
        
        # string_hoppers is index 1 in classes.yaml
        cls_id, xc, yc, w, h = line.split()
        self.assertEqual(cls_id, "1")
        self.assertAlmostEqual(float(xc), 0.5, places=3)
        self.assertAlmostEqual(float(yc), 0.5, places=3)
        self.assertAlmostEqual(float(w), 0.8, places=3)
        self.assertAlmostEqual(float(h), 0.8, places=3)

if __name__ == "__main__":
    unittest.main()
