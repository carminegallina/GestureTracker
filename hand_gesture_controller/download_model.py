from __future__ import annotations

import urllib.request

from .model_assets import HAND_LANDMARKER_MODEL, HAND_LANDMARKER_URL, MODEL_DIR


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    if HAND_LANDMARKER_MODEL.exists():
        print(f"Model already exists: {HAND_LANDMARKER_MODEL}")
        return

    print(f"Downloading MediaPipe Hand Landmarker model to {HAND_LANDMARKER_MODEL}")
    urllib.request.urlretrieve(HAND_LANDMARKER_URL, HAND_LANDMARKER_MODEL)
    print("Done.")


if __name__ == "__main__":
    main()

