import numpy as np

from src.core.features.universal import compute_entropy, compute_windowed_entropy_variance

FEATURE_NAMES = [
    'global_entropy',
    'windowed_variance',
    'null_byte_ratio',
    'high_byte_ratio',
    'printable_ratio',
    'q1_entropy',
    'q2_entropy',
    'q3_entropy',
    'q4_entropy',
    'chi2_uniform',
]


def extract_features(data: bytes) -> list[float]:
    arr = np.frombuffer(data, dtype=np.uint8)
    n = len(arr)

    global_entropy = compute_entropy(data)
    windowed_variance = compute_windowed_entropy_variance(data)

    null_byte_ratio   = float(np.sum(arr == 0)) / n if n > 0 else 0.0
    high_byte_ratio   = float(np.sum(arr > 127)) / n if n > 0 else 0.0
    printable_ratio   = float(np.sum((arr >= 32) & (arr <= 126))) / n if n > 0 else 0.0

    q = n // 4
    q1_entropy = compute_entropy(bytes(arr[:q]))         if q > 0 else 0.0
    q2_entropy = compute_entropy(bytes(arr[q:2*q]))      if q > 0 else 0.0
    q3_entropy = compute_entropy(bytes(arr[2*q:3*q]))    if q > 0 else 0.0
    q4_entropy = compute_entropy(bytes(arr[3*q:]))       if q > 0 else 0.0

    counts = np.bincount(arr, minlength=256).astype(float)
    expected = n / 256.0
    chi2_normalized = float(np.sum((counts - expected) ** 2) / expected) / (n + 1e-9) if expected > 0 else 0.0

    return [
        global_entropy,
        windowed_variance,
        null_byte_ratio,
        high_byte_ratio,
        printable_ratio,
        q1_entropy,
        q2_entropy,
        q3_entropy,
        q4_entropy,
        chi2_normalized,
    ]
