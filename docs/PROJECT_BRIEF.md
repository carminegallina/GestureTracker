# Project Brief

## Nome

GestureTracker

## Visione

Creare un controller desktop dimostrabile via webcam che trasformi gesture della mano in azioni utili sul PC.

## Utenti target

- Utenti interessati ad accessibilita, automazione e computer vision.
- Sviluppatore del progetto durante test e demo.

## Ambito

- Riconoscere gesture della mano.
- Convertire gesture in azioni desktop.
- Mostrare stato e feedback durante l'uso.
- Gestire webcam occupata o non disponibile.

## Fuori ambito iniziale

- Supporto multiutente.
- Pubblicazione su store.
- Automazioni per operazioni distruttive di sistema.

## Asset e dati

Il modello MediaPipe `hand_landmarker.task` si scarica con
`python -m hand_gesture_controller.download_model` e resta ignorato da Git: e'
un binario rigenerabile, non codice.

Le impostazioni locali (`settings.json`), i log e le catture restano fuori dal
repository. Nessuna immagine dalla webcam viene salvata su disco.
