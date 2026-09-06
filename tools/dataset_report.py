import sys
import json
from pathlib import Path
from typing import Dict, Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.utils.paths import MANIFEST_PATH, REPORTS_DIR, REJECTED_DATA_DIR
from src.dataset.manifest import ManifestManager

def generate_report():
    manifest = ManifestManager()
    items = manifest.get_all_items()

    print("\n" + "=" * 65)
    print("      SMART CANTEEN DATASET STATUS & HEALTH REPORT")
    print("=" * 65)

    total_images = len(items)
    print(f"\n[+] Overview:")
    print(f"   * Total Tracked Images: {total_images}")

    # Validation Report
    val_report_path = REPORTS_DIR / "dataset_validation.json"
    if val_report_path.exists():
        try:
            with open(val_report_path, "r", encoding="utf-8") as f:
                val_data = json.load(f)
            print(f"   * Valid Images:         {val_data.get('valid_images', 0)}")
            print(f"   * Quarantined/Rejected: {val_data.get('rejected_images', 0)}")
        except Exception:
            pass

    # Duplicate Report
    dup_report_path = REPORTS_DIR / "duplicates.json"
    if dup_report_path.exists():
        try:
            with open(dup_report_path, "r", encoding="utf-8") as f:
                dup_data = json.load(f)
            print(f"   * Exact Duplicate Groups:      {dup_data.get('exact_duplicate_groups_count', 0)}")
            print(f"   * Perceptual Duplicate Groups: {dup_data.get('perceptual_duplicate_groups_count', 0)}")
        except Exception:
            pass

    # Status Breakdown
    status_counts: Dict[str, int] = {}
    split_counts: Dict[str, int] = {}
    class_counts: Dict[str, int] = {}

    for it in items.values():
        st = it.get("status", "needs_review")
        status_counts[st] = status_counts.get(st, 0) + 1

        sp = it.get("split", "unassigned")
        split_counts[sp] = split_counts.get(sp, 0) + 1

        cls_name = it.get("class", "unknown")
        class_counts[cls_name] = class_counts.get(cls_name, 0) + 1

    print("\n[+] Annotation Status Breakdown:")
    print(f"   * Approved:     {status_counts.get('approved', 0):>4}  (ready for training)")
    print(f"   * Needs Review: {status_counts.get('needs_review', 0):>4}")
    print(f"   * Rejected:     {status_counts.get('rejected', 0):>4}")

    print("\n[+] Dataset Split Allocation:")
    print(f"   * Train:        {split_counts.get('train', 0):>4}")
    print(f"   * Validation:   {split_counts.get('valid', 0):>4}")
    print(f"   * Test:         {split_counts.get('test', 0):>4}")

    print("\n[+] Class Distribution (Images per Category):")
    if class_counts:
        for cls_name, count in sorted(class_counts.items()):
            print(f"   * {cls_name:<20}: {count} images")
    else:
        print("   (No classes found. Add raw images to data/raw/<category>/)")

    print("\n" + "=" * 65 + "\n")

if __name__ == "__main__":
    generate_report()
