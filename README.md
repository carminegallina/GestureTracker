# GestureTracker

[![tests](https://github.com/carminegallina/GestureTracker/actions/workflows/tests.yml/badge.svg)](https://github.com/carminegallina/GestureTracker/actions/workflows/tests.yml)

**English** · [Italiano](README.it.md)

A Python desktop tool for driving Windows with hand gestures through a webcam.

## What it solves

Hands-free interaction with the desktop: pointer, clicks, text selection, copy and paste
shortcuts, and video controls. It also handles the awkward real-world cases — a webcam
already in use by another application, an OBS virtual camera, and camera indexes that
move around between reboots.

## Main features

- Hand tracking with MediaPipe.
- Webcam input that falls back automatically across camera indexes.
- Pointer movement, clicks and configurable gestures.
- Action profiles and gesture profiles, both as JSON.
- Video controls for players and browsers: play/pause and seek with a right-hand fist,
  through the Windows media session, falling back to key presses.
- Settings in a JSON file, resolved in order: defaults, then file, then command line.
- Optional desktop overlay.
- OBS Virtual Camera support through `pyvirtualcam`.
- A unit-test suite that runs without a webcam or any other hardware.

## Stack

Python · MediaPipe · OpenCV · NumPy · PyAutoGUI · pyvirtualcam / OBS Virtual Camera · unittest

## Setup

```powershell
cd GestureTracker
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m hand_gesture_controller.download_model
```

The model file `hand_gesture_controller\models\hand_landmarker.task` can stay local; it
is ignored by Git.

## Running

```powershell
gesturetracker --dry-run
gesturetracker
gesturetracker --overlay
gesturetracker --no-virtual-camera
gesturetracker --virtual-camera-backend obs
```

The command works from any directory. Without installing the package,
`python -m hand_gesture_controller.main` still works with the same arguments.

## Tests

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest tests
```

## Documentation

- [Installation](docs/INSTALLATION.md)
- [User guide](docs/USER_GUIDE.md): gestures, keys and video commands
- [Configuration](docs/CONFIGURATION.md): JSON settings and profiles
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Development](docs/DEVELOPMENT.md)
- [Architecture](docs/ARCHITECTURE.md), [decisions](docs/DECISIONS.md), [roadmap](docs/ROADMAP.md)

## Privacy

The camera feed is processed on the machine and never leaves it: the only network access
in the project is `download_model.py`, which fetches the MediaPipe hand landmarker once.
Nothing is recorded to disk unless you ask for it.

## Roadmap

- A demo GIF of the gestures, checked for personal data before publishing.
- Packaging, or a launcher script.

## Licence

MIT — see [LICENSE](LICENSE).
