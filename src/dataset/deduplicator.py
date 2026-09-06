import json
from pathlib import Path
from typing import Dict, List, Any

from src.utils.hashing import compute_file_sha256, compute_perceptual_hash, hamming_distance
from src.utils.paths import REPORTS_DIR, ensure_dir
from src.utils.logging import dataset_logger

PERCEPTUAL_DISTANCE_THRESHOLD = 5

class DatasetDeduplicator:
    """
    Detects exact duplicate files (via SHA256) and visual perceptual duplicates (via dHash).
    Generates reports/duplicates.json and flags duplicates to prevent data leakage between splits.
    """
    def __init__(self, report_dir: Path = REPORTS_DIR):
        self.report_dir = Path(report_dir)

    def process(self, valid_items: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Processes valid items, computes hashes, and detects duplicate clusters.
        Returns:
            {
                "hashed_items": List[Dict[str, Any]],
                "exact_duplicates": List[List[Dict[str, Any]]],
                "perceptual_duplicates": List[List[Dict[str, Any]]],
                "clean_items": List[Dict[str, Any]]
            }
        """
        all_items: List[Dict[str, Any]] = []
        sha_map: Dict[str, List[Dict[str, Any]]] = {}

        # 1. Compute Hashes
        for cat, items in valid_items.items():
            for item in items:
                path = item["path"]
                try:
                    sha256_val = compute_file_sha256(path)
                    phash_val = compute_perceptual_hash(path)
                    item_record = {
                        "id": sha256_val,
                        "path": str(path),
                        "filename": path.name,
                        "class": cat,
                        "width": item["width"],
                        "height": item["height"],
                        "sha256": sha256_val,
                        "phash": phash_val,
                        "is_duplicate": False,
                        "duplicate_of": None
                    }
                    all_items.append(item_record)

                    if sha256_val not in sha_map:
                        sha_map[sha256_val] = []
                    sha_map[sha256_val].append(item_record)
                except Exception as e:
                    dataset_logger.error(f"Error computing hash for {path}: {e}")

        # 2. Exact Duplicates
        exact_duplicate_groups = []
        clean_unique_items: List[Dict[str, Any]] = []

        for sha, group in sha_map.items():
            if len(group) > 1:
                exact_duplicate_groups.append([
                    {"path": x["path"], "class": x["class"], "sha256": sha} for x in group
                ])
                # Primary item
                clean_unique_items.append(group[0])
                # Mark secondary duplicates
                for dup in group[1:]:
                    dup["is_duplicate"] = True
                    dup["duplicate_of"] = group[0]["id"]
            else:
                clean_unique_items.append(group[0])

        # 3. Perceptual Duplicates check on unique items
        perceptual_duplicate_groups = []
        visited = set()
        for i in range(len(clean_unique_items)):
            if i in visited:
                continue
            group = [clean_unique_items[i]]
            for j in range(i + 1, len(clean_unique_items)):
                if j in visited:
                    continue
                # Compare within same class or across classes
                dist = hamming_distance(
                    clean_unique_items[i]["phash"], clean_unique_items[j]["phash"]
                )
                if dist <= PERCEPTUAL_DISTANCE_THRESHOLD:
                    group.append(clean_unique_items[j])
                    visited.add(j)
            if len(group) > 1:
                perceptual_duplicate_groups.append([
                    {"path": x["path"], "class": x["class"], "phash": x["phash"]} for x in group
                ])

        # Write Report
        ensure_dir(self.report_dir)
        report = {
            "total_images_analyzed": len(all_items),
            "unique_images": len(clean_unique_items),
            "exact_duplicate_groups_count": len(exact_duplicate_groups),
            "exact_duplicates": exact_duplicate_groups,
            "perceptual_duplicate_groups_count": len(perceptual_duplicate_groups),
            "perceptual_duplicates": perceptual_duplicate_groups
        }

        report_path = self.report_dir / "duplicates.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        dataset_logger.info(
            f"Deduplication complete: {len(all_items)} analyzed, "
            f"{len(exact_duplicate_groups)} exact duplicate groups, "
            f"{len(perceptual_duplicate_groups)} perceptual duplicate groups."
        )

        return {
            "hashed_items": all_items,
            "clean_items": clean_unique_items,
            "report": report
        }
