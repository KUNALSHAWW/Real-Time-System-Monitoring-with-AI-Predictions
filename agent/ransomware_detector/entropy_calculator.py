"""
Shannon Entropy Calculator

Computes the information entropy of byte sequences. Encrypted/compressed
data has entropy close to 8.0 bits/byte; plain text is typically 3-5.

Used as a ransomware indicator: files being actively encrypted will
produce high-entropy output.
"""

import math
from collections import Counter
from typing import Optional


def shannon_entropy(data: bytes) -> float:
    """
    Compute Shannon entropy of a byte sequence.

    Returns value between 0.0 (all identical bytes) and 8.0 (uniform random).
    Returns 0.0 for empty data.
    """
    if not data:
        return 0.0

    length = len(data)
    counts = Counter(data)

    entropy = 0.0
    for count in counts.values():
        probability = count / length
        if probability > 0:
            entropy -= probability * math.log2(probability)

    return entropy


def file_entropy(filepath: str, sample_size: int = 65536) -> Optional[float]:
    """
    Compute entropy of a file by reading the first sample_size bytes.

    Returns None if file cannot be read.
    """
    try:
        with open(filepath, "rb") as f:
            data = f.read(sample_size)
        if not data:
            return 0.0
        return shannon_entropy(data)
    except (OSError, PermissionError):
        return None


def is_suspicious_entropy(entropy_value: float, threshold: float = 7.5) -> bool:
    """Return True if entropy exceeds the suspicion threshold."""
    return entropy_value >= threshold
