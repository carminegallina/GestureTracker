# Architecture

## Stato attuale

Codice importato nel portfolio. L'architettura e' organizzata come package Python `hand_gesture_controller` con test in `tests`.

## Architettura target

- Camera input: acquisizione frame e gestione errori webcam.
- Hand tracking: rilevamento mano, landmark e confidenza.
- Gesture engine: mapping tra landmark e gesture.
- Desktop actions: puntatore, click, selezione testo e scorciatoie.
- State manager: modalita attiva, cooldown e prevenzione input accidentali.
- UI/logging: feedback visivo e diagnostica.

## File principali

- `main.py`: CLI e loop applicativo.
- `config.py`: configurazione runtime.
- `camera_manager.py`: gestione webcam e fallback indici.
- `hand_tracker.py`: integrazione MediaPipe.
- `gesture_detector.py`: riconoscimento gesture.
- `binding_engine.py` e `action_runner.py`: mapping gesture/azioni.
- `mouse_controller.py` e `right_hand_mouse.py`: controllo puntatore.
- `media_gestures.py` e `screen_context.py`: gesture media per player/browser.
- `virtual_camera.py`: output OBS Virtual Camera.
- `profiles`: profili JSON per azioni e gesture.

## Note tecniche

- Mantenere separata la logica di riconoscimento dalla logica di automazione desktop.
- Centralizzare configurazione e soglie.
- Evitare path locali hardcodati.
- Trattare input webcam e automazione desktop come componenti testabili separatamente.
