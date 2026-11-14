# Architecture

## Impianto

Package Python `hand_gesture_controller`, test in `tests`. Il riconoscimento
delle gesture, l'input desktop e la configurazione restano separati: il motore
che traduce gesture in azioni non sa come queste vengono eseguite.

## Livelli

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
- `media_control.py`: sessione media di Windows con fallback sui tasti.
- `settings_store.py`: impostazioni da `settings.json`.
- `physical_mouse_guard.py`: priorita' dell'air mouse sul mouse fisico.
- `virtual_camera.py`: output OBS Virtual Camera.
- `profiles`: profili JSON per azioni e gesture.

L'albero completo dei moduli, con una riga di descrizione per ciascuno, e' nel
README del package.

## Note tecniche

- Mantenere separata la logica di riconoscimento dalla logica di automazione desktop.
- Centralizzare configurazione e soglie.
- Evitare path locali hardcodati.
- Trattare input webcam e automazione desktop come componenti testabili separatamente.
