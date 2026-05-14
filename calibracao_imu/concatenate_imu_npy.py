from pathlib import Path

import numpy as np


INPUT_DIR = Path("imu_measurements/imu_measurements")
OUTPUT_FILE = Path("dados_imu_concatenated.npy")


def main() -> None:
    npy_files = sorted(INPUT_DIR.glob("*.npy"))

    if not npy_files:
        raise FileNotFoundError(f"No .npy files found in {INPUT_DIR}")

    arrays = [np.load(path, allow_pickle=False) for path in npy_files]
    concatenated = np.concatenate(arrays, axis=0)
    np.save(OUTPUT_FILE, concatenated)

    print(f"Loaded {len(npy_files)} files")
    print(f"Concatenated shape: {concatenated.shape}")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
