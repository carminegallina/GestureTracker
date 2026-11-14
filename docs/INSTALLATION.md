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
python -m pip install -e .
```

L'installazione in modalita' modificabile (`-e`) e' quella consigliata: l'app
scrive i propri profili gesture e azioni dentro il package, e con
un'installazione normale finirebbero in `site-packages`.

Da qui in avanti il comando `gesturetracker` e' disponibile da qualunque
cartella. Senza installare il pacchetto resta valido
`python -m hand_gesture_controller.main`, con gli stessi argomenti.

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
gesturetracker --dry-run --no-virtual-camera
```

Avvio normale:

```powershell
gesturetracker
```

Con la camera virtuale OBS:

```powershell
gesturetracker --virtual-camera-backend obs
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
