# GestureTracker

[![tests](https://github.com/carminegallina/GestureTracker/actions/workflows/tests.yml/badge.svg)](https://github.com/carminegallina/GestureTracker/actions/workflows/tests.yml)

Tool desktop Python per controllare il PC con gesture della mano via webcam.

## Problema risolto

Il progetto permette interazioni hands-free con il desktop: puntatore, click, selezione testo, scorciatoie copia/incolla e controlli video con gesture. Gestisce anche scenari pratici come webcam occupata, camera virtuale OBS e fallback degli indici camera.

## Funzionalita principali

- Tracking mano con MediaPipe.
- Input webcam con fallback automatico degli indici camera.
- Controllo puntatore, click e gesture configurabili.
- Profili azione e profili gesture in JSON.
- Controlli video per player/browser: play/pausa e seek con pugno destro,
  via sessione media di Windows con fallback sui tasti.
- Impostazioni su file JSON, con precedenza default, file, riga di comando.
- Overlay desktop opzionale.
- Supporto OBS Virtual Camera via `pyvirtualcam`.
- 51 test unitari, eseguibili senza webcam ne' hardware.

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
python -m pip install -r .
equirements-dev.txt
python -m pytest tests
```

## Documentazione

- [Installazione](docs/INSTALLATION.md)
- [Guida utente](docs/USER_GUIDE.md): gesture, tasti e comandi video
- [Configurazione](docs/CONFIGURATION.md): impostazioni JSON e profili
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Sviluppo](docs/DEVELOPMENT.md)
- [Architettura](docs/ARCHITECTURE.md), [decisioni](docs/DECISIONS.md), [roadmap](docs/ROADMAP.md)

## Screenshot/demo

Da aggiungere: una GIF che mostri puntatore e comandi video. Verificare che
nella registrazione non compaiano dati personali.

## Roadmap

- Aggiungere una GIF demo delle gesture.
- Valutare packaging o script di avvio.

## Privacy e sicurezza

- Non committare credenziali, token, path personali o configurazioni sensibili.
- Non committare log, catture schermo o video demo non revisionati.
- Non committare il modello scaricato senza decisione esplicita.
- Documentare chiaramente l'uso della webcam.

## Licenza

MIT, vedere [LICENSE](LICENSE).
