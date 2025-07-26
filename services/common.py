# common.py - Common variables and utilities for plot digitization

# Global variables needed by plotdigitizer
img_ = None
locations_ = []
params_ = {}
WindowName_ = "GT7 Plot Digitizer"

# Function to compute a hash from data for caching
def data_to_hash(data):
    import hashlib
    import numpy as np
    if isinstance(data, np.ndarray):
        return hashlib.md5(data.tobytes()).hexdigest()
    return hashlib.md5(str(data).encode()).hexdigest()

# Function to get/create cache directory
def cache():
    import os
    from pathlib import Path
    cache_dir = Path("cache")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir