import shutil
import tempfile
import unittest
from pathlib import Path

from src.training.model_manager import ModelManager

class TestModelManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.registry_path = self.temp_dir / "models" / "registry.json"

        # Create dummy weights
        self.dummy_run_weights = self.temp_dir / "runs" / "best.pt"
        self.dummy_run_weights.parent.mkdir(parents=True, exist_ok=True)
        with open(self.dummy_run_weights, "w") as f:
            f.write("mock_model_weights_data")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_register_and_promote_candidate(self):
        prod_path = self.temp_dir / "production" / "best.pt"
        cand_dir = self.temp_dir / "candidates"
        mm = ModelManager(
            registry_path=self.registry_path,
            production_model_path=prod_path,
            candidates_dir=cand_dir
        )
        
        # 1. Register candidate
        cand_record = mm.register_candidate(
            run_name="smoke_test_run",
            weights_path=self.dummy_run_weights,
            metrics={"map50": 0.942, "precision": 0.91}
        )

        self.assertIn("cand_smoke_test_run", cand_record["candidate_id"])
        self.assertEqual(len(mm.registry["candidates"]), 1)

        # 2. Promote candidate
        prod_record = mm.promote_candidate(candidate_id=cand_record["candidate_id"])
        self.assertEqual(prod_record["candidate_id"], cand_record["candidate_id"])
        self.assertTrue(Path(prod_record["production_path"]).exists())
        self.assertIsNotNone(mm.registry["production_model"])

if __name__ == "__main__":
    unittest.main()
