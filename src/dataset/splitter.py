import random
from typing import Dict, List, Any
from src.utils.logging import dataset_logger

DEFAULT_TRAIN_RATIO = 0.80
DEFAULT_VAL_RATIO = 0.10
DEFAULT_TEST_RATIO = 0.10
RANDOM_SEED = 42

class DatasetSplitter:
    """
    Performs deterministic, stratified dataset splitting per class.
    Preserves existing split assignments in the manifest to avoid data reshuffling.
    """
    def __init__(
        self,
        train_ratio: float = DEFAULT_TRAIN_RATIO,
        val_ratio: float = DEFAULT_VAL_RATIO,
        test_ratio: float = DEFAULT_TEST_RATIO,
        seed: int = RANDOM_SEED
    ):
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.seed = seed

    def assign_splits(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Assigns 'train', 'valid', or 'test' to each item while keeping class balances.
        Preserves existing valid split assignments.
        """
        rng = random.Random(self.seed)

        # Group items by class
        by_class: Dict[str, List[Dict[str, Any]]] = {}
        for item in items:
            cat = item["class"]
            if cat not in by_class:
                by_class[cat] = []
            by_class[cat].append(item)

        split_counts = {"train": 0, "valid": 0, "test": 0}

        for cat, cat_items in by_class.items():
            # Separate items that already have a split assigned from new unassigned items
            unassigned = []
            for item in cat_items:
                current_split = item.get("split")
                if current_split in {"train", "valid", "test"}:
                    split_counts[current_split] += 1
                else:
                    unassigned.append(item)

            if not unassigned:
                continue

            # Deterministically shuffle unassigned items for this class
            # Sort first by ID so order is independent of OS filesystem differences
            unassigned.sort(key=lambda x: x["id"])
            rng.shuffle(unassigned)

            n = len(unassigned)
            if n == 1:
                # If only 1 unassigned, assign to train
                unassigned[0]["split"] = "train"
                split_counts["train"] += 1
            elif n == 2:
                unassigned[0]["split"] = "train"
                unassigned[1]["split"] = "valid"
                split_counts["train"] += 1
                split_counts["valid"] += 1
            else:
                n_train = max(1, int(round(n * self.train_ratio)))
                n_val = max(1, int(round(n * self.val_ratio)))
                # Remaining to test
                for idx, item in enumerate(unassigned):
                    if idx < n_train:
                        item["split"] = "train"
                        split_counts["train"] += 1
                    elif idx < n_train + n_val:
                        item["split"] = "valid"
                        split_counts["valid"] += 1
                    else:
                        item["split"] = "test"
                        split_counts["test"] += 1

        dataset_logger.info(
            f"Dataset splits assigned: {split_counts['train']} train, "
            f"{split_counts['valid']} valid, {split_counts['test']} test."
        )
        return items
