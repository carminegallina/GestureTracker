# Installazione

## Requisiti

- Windows 10 o 11.
- Python 3.13.
- Webcam compatibile con OpenCV.
- OBS Studio con OBS Virtual Camera, solo se si vuole esporre il feed come camera virtuale.

I controlli media nativi usano le API Windows Media Transport Controls: su altri
sistemi operativi il progetto non e' supportato.

## Dipendenze

Dalla cartella del progetto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r .\hand_gesture_controller\requirements.txt
```

## Modello MediaPipe

```powershell
python -m hand_gesture_controller.download_model
```

Il modello viene scaricato in `hand_gesture_controller/models/hand_landmarker.task`
ed e' escluso dal controllo versione: e' un asset binario scaricabile.

Per usare un modello gia' presente altrove:

```powershell
python -m hand_gesture_controller.main --model-path C:\path\to\hand_landmarker.task
```

## Primo avvio

Prova senza toccare il sistema, utile per verificare webcam e tracking:

```powershell
python -m hand_gesture_controller.main --dry-run --no-virtual-camera
```

Avvio normale:

```powershell
python -m hand_gesture_controller.main
```

Con la camera virtuale OBS:

```powershell
python -m hand_gesture_controller.main --virtual-camera-backend obs
```

Se la camera virtuale non e' disponibile il controller continua a funzionare e
mostra lo stato nella finestra di debug.

## Impostazioni

Il file delle impostazioni non viene creato automaticamente. Per partire da un
file modificabile:

```powershell
copy .\hand_gesture_controller\settings.example.json .\hand_gesture_controller\settings.json
```

Dettagli in [CONFIGURATION.md](CONFIGURATION.md).

## Test

```powershell
python -m pytest tests
```
