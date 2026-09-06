import os
import shutil
import tempfile
import unittest
from pathlib import Path
from PIL import Image
import numpy as np

from src.dataset.scanner import DatasetScanner
from src.dataset.validator import ImageValidator
from src.dataset.deduplicator import DatasetDeduplicator
from src.utils.hashing import compute_file_sha256, compute_perceptual_hash, hamming_distance

class TestDatasetManagement(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.raw_dir = self.temp_dir / "raw"
        self.rejected_dir = self.temp_dir / "rejected"
        self.report_dir = self.temp_dir / "reports"
        self.classes_cfg = self.temp_dir / "classes.yaml"

        # Create mock food categories
        (self.raw_dir / "string_hoppers").mkdir(parents=True, exist_ok=True)
        (self.raw_dir / "kottu").mkdir(parents=True, exist_ok=True)

        # Create valid images
        self._create_dummy_image(self.raw_dir / "string_hoppers" / "sh_1.jpg", color=(255, 0, 0))
        self._create_dummy_image(self.raw_dir / "string_hoppers" / "sh_2.jpg", color=(255, 0, 0)) # Duplicate of sh_1
        self._create_dummy_image(self.raw_dir / "kottu" / "kt_1.jpg", color=(0, 255, 0))

        # Create a corrupt (0-byte) image
        corrupt_file = self.raw_dir / "kottu" / "corrupt.jpg"
        corrupt_file.touch()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_dummy_image(self, path: Path, color=(200, 200, 200), size=(100, 100)):
        img = Image.new("RGB", size, color=color)
        img.save(path, "JPEG")

    def test_scanner_discovers_classes_and_files(self):
        scanner = DatasetScanner(raw_dir=self.raw_dir, classes_config_path=self.classes_cfg)
        res = scanner.scan()
        self.assertIn("string_hoppers", res["classes"])
        self.assertIn("kottu", res["classes"])
        self.assertEqual(res["total_images"], 4) # 3 valid + 1 corrupt file

    def test_validator_quarantines_corrupt_files(self):
        scanner = DatasetScanner(raw_dir=self.raw_dir, classes_config_path=self.classes_cfg)
        scan_res = scanner.scan()

        validator = ImageValidator(rejected_dir=self.rejected_dir, report_dir=self.report_dir)
        val_res = validator.validate_dataset(scan_res["categories"])

        report = val_res["report"]
        self.assertEqual(report["total_images"], 4)
        self.assertEqual(report["valid_images"], 3)
        self.assertEqual(report["rejected_images"], 1)

        # Check that corrupt file moved to rejected directory
        quarantined_files = list(self.rejected_dir.rglob("*.jpg"))
        self.assertEqual(len(quarantined_files), 1)
        self.assertEqual(quarantined_files[0].name, "corrupt.jpg")

    def test_deduplicator_detects_exact_duplicates(self):
        scanner = DatasetScanner(raw_dir=self.raw_dir, classes_config_path=self.classes_cfg)
        validator = ImageValidator(rejected_dir=self.rejected_dir, report_dir=self.report_dir)
        deduplicator = DatasetDeduplicator(report_dir=self.report_dir)

        scan_res = scanner.scan()
        val_res = validator.validate_dataset(scan_res["categories"])
        dedup_res = deduplicator.process(val_res["valid_items"])

        self.assertEqual(dedup_res["report"]["total_images_analyzed"], 3)
        self.assertEqual(dedup_res["report"]["unique_images"], 2)
        self.assertEqual(dedup_res["report"]["exact_duplicate_groups_count"], 1)

if __name__ == "__main__":
    unittest.main()
