import hashlib
from pathlib import Path
from typing import Union, List, Dict, Any
from PIL import Image

def compute_file_sha256(file_path: Union[str, Path]) -> str:
    """
    Computes the SHA256 hex digest of a file in binary chunks.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def compute_perceptual_hash(file_path: Union[str, Path], hash_size: int = 8) -> str:
    """
    Computes a Difference Hash (dHash) for visual perceptual similarity.
    1. Converts image to grayscale.
    2. Resizes to (hash_size + 1, hash_size) -> e.g. (9, 8).
    3. Compares adjacent horizontal pixels to form a (hash_size * hash_size) bit array.
    4. Returns a 16-character hexadecimal string.
    """
    path = Path(file_path)
    with Image.open(path) as img:
        # Convert to grayscale and resize to (width=9, height=8)
        img = img.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.BILINEAR)
        pixels = list(img.getdata())
        
        # Grid of (hash_size, hash_size+1)
        width = hash_size + 1
        diff = []
        for row in range(hash_size):
            row_pixels = pixels[row * width : (row + 1) * width]
            for col in range(hash_size):
                diff.append(row_pixels[col] > row_pixels[col + 1])
                
        # Convert boolean list to hexadecimal string
        decimal_val = 0
        hex_str = []
        for index, value in enumerate(diff):
            if value:
                decimal_val += 2 ** (index % 4)
            if (index % 4) == 3:
                hex_str.append(hex(decimal_val)[2:])
                decimal_val = 0
        return "".join(hex_str)

def hamming_distance(hash1: str, hash2: str) -> int:
    """
    Calculates the Hamming distance between two hex hash strings.
    A distance <= 5 usually indicates near-duplicate or visually identical images.
    """
    if len(hash1) != len(hash2):
        raise ValueError("Hash strings must have identical lengths for Hamming distance.")
    
    # Convert hex strings to integer bitfields and count set bits of XOR
    val1 = int(hash1, 16)
    val2 = int(hash2, 16)
    xor_val = val1 ^ val2
    return bin(xor_val).count("1")

def compute_dataset_fingerprint(
    image_hashes: List[str],
    classes: List[str],
    config_dict: Dict[str, Any]
) -> str:
    """
    Generates a deterministic SHA256 fingerprint for a dataset version.
    """
    hasher = hashlib.sha256()
    for h in sorted(image_hashes):
        hasher.update(h.encode("utf-8"))
    for c in sorted(classes):
        hasher.update(c.encode("utf-8"))
    hasher.update(str(sorted(config_dict.items())).encode("utf-8"))
    return hasher.hexdigest()
