# GestureTracker

Tool desktop Python per controllare il PC con gesture della mano via webcam.

## Problema risolto

Il progetto permette interazioni hands-free con il desktop: puntatore, click, selezione testo, scorciatoie copia/incolla e controlli video con gesture. Gestisce anche scenari pratici come webcam occupata, camera virtuale OBS e fallback degli indici camera.

## Funzionalita principali

- Tracking mano con MediaPipe.
- Input webcam con fallback automatico degli indici camera.
- Controllo puntatore, click e gesture configurabili.
- Profili azione e profili gesture in JSON.
- Controlli video per player/browser: play/pausa e seek con pugno destro.
- Overlay desktop opzionale.
- Supporto OBS Virtual Camera via `pyvirtualcam`.
- Test unitari per gesture, camera, mouse, media gestures e virtual camera.

## Tech stack

- Python.
- MediaPipe.
- OpenCV.
- NumPy.
- PyAutoGUI.
- pyvirtualcam / OBS Virtual Camera.
- unittest.

## Setup

```powershell
cd GestureTracker
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r .\hand_gesture_controller\requirements.txt
python -m hand_gesture_controller.download_model
```

Il modello `hand_gesture_controller\models\hand_landmarker.task` puo' restare locale ed e' ignorato da Git.

## Esecuzione

```powershell
python -m hand_gesture_controller.main --dry-run
python -m hand_gesture_controller.main
python -m hand_gesture_controller.main --overlay
python -m hand_gesture_controller.main --no-virtual-camera
python -m hand_gesture_controller.main --virtual-camera-backend obs
```

## Test

```powershell
python -m unittest discover tests
```

## Screenshot/demo

Placeholder:

- aggiungere screenshot UI o GIF demo;
- aggiungere breve video dimostrativo se disponibile;
- verificare che non compaiano dati personali nello schermo registrato.

## Roadmap

- Verificare il run completo dal nuovo percorso portfolio.
- Preparare una demo breve per CV/portfolio.
- Valutare packaging o script di avvio.
- Documentare meglio tutte le gesture supportate.
- Valutare repository pubblico dopo revisione.

## Privacy e sicurezza

- Non committare credenziali, token, path personali o configurazioni sensibili.
- Non committare log, catture schermo o video demo non revisionati.
- Non committare il modello scaricato senza decisione esplicita.
- Documentare chiaramente l'uso della webcam.
