import numpy as np

def compute_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = np.bincount(np.frombuffer(data, dtype=np.uint8), minlength=256)
    probs = counts / len(data)
    probs = probs[probs > 0]
    return float(-np.sum(probs * np.log2(probs)))

def compute_windowed_entropy(data: bytes, window_size: int = 256) -> list[float]:
    if not data:
        return []
    arr = np.frombuffer(data, dtype=np.uint8)
    entropies = []
    for i in range(0, len(arr), window_size):
        window = arr[i:i + window_size]
        counts = np.bincount(window, minlength=256)
        probs = counts / len(window)
        probs = probs[probs > 0]
        entropies.append(float(-np.sum(probs * np.log2(probs))))
    return entropies

def compute_windowed_entropy_variance(data: bytes, window_size: int = 256) -> float:
    entropies = compute_windowed_entropy(data, window_size)
    if not entropies:
        return 0.0
    return float(np.var(entropies))