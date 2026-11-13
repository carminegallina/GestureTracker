# GestureTracker

MVP desktop locale per Windows 10/11 che usa la webcam per controllare mouse,
drag/selezione, copia e incolla con gesture della mano.

## Gesture

| Gesture | Azione |
| --- | --- |
| Mano destra, indice visibile / mano aperta | Muove il puntatore |
| Mano destra, abbassa una volta il medio | Click sinistro |
| Mano destra, abbassa due volte il medio | Doppio click sinistro |
| Mano destra, tieni abbassato il medio | Trascina / seleziona |
| Mano destra, abbassa una volta l'anulare | Click destro |
| Mano sinistra, pugno mantenuto | Attiva/disattiva mouse mode |
| Mano sinistra, pollice su | Ctrl+C |
| Mano sinistra, segno V | Ctrl+V |
| Due pugni mantenuti | Ctrl+C |
| Due segni V mantenuti | Ctrl+V |
| SPAZIO | Pausa / riprendi |
| ESC | Esci |

## Setup

Dalla cartella del progetto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r .\hand_gesture_controller\requirements.txt
python -m hand_gesture_controller.download_model
```

## Avvio consigliato

Prima prova senza controllare davvero il sistema operativo:

```powershell
python -m hand_gesture_controller.main --dry-run
```

Quando il riconoscimento e' soddisfacente:

```powershell
python -m hand_gesture_controller.main
```

Opzioni utili:

```powershell
python -m hand_gesture_controller.main --paused
python -m hand_gesture_controller.main --camera-index 1
python -m hand_gesture_controller.main --camera-retry-interval 2.5
python -m hand_gesture_controller.main --keep-camera-on-pause
python -m hand_gesture_controller.main --camera-backend 700
python -m hand_gesture_controller.main --no-camera-fallback
python -m hand_gesture_controller.main --camera-fallback-indices 0,1,2,3,4
python -m hand_gesture_controller.main --no-virtual-camera
python -m hand_gesture_controller.main --virtual-camera-device "OBS Virtual Camera"
python -m hand_gesture_controller.main --virtual-camera-backend obs
python -m hand_gesture_controller.main --virtual-camera-mirror
python -m hand_gesture_controller.main --virtual-camera-width 1280 --virtual-camera-height 720
python -m hand_gesture_controller.main --virtual-camera-fps 30
python -m hand_gesture_controller.main --width 640 --height 480
python -m hand_gesture_controller.main --max-hands 1
python -m hand_gesture_controller.main --detection-confidence 0.50
python -m hand_gesture_controller.main --tracking-confidence 0.45
python -m hand_gesture_controller.main --lost-hand-grace 0.50
python -m hand_gesture_controller.main --mouse-off
python -m hand_gesture_controller.main --no-pointer-lock
python -m hand_gesture_controller.main --action-profile .\my_actions.json
python -m hand_gesture_controller.main --gesture-profile .\my_gestures.json
python -m hand_gesture_controller.main --screen all
python -m hand_gesture_controller.main --screen primary
python -m hand_gesture_controller.main --screen 2
python -m hand_gesture_controller.main --screen-rect 0,0,1920,1080
python -m hand_gesture_controller.main --pointer-sensitivity 0.75
python -m hand_gesture_controller.main --smoothing-alpha 0.20
python -m hand_gesture_controller.main --dead-zone 6
python -m hand_gesture_controller.main --active-zone 0.20,0.15,0.80,0.85
python -m hand_gesture_controller.main --no-media-gestures
python -m hand_gesture_controller.main --media-swipe-threshold 0.18
python -m hand_gesture_controller.main --media-pause-hold 0.65
python -m hand_gesture_controller.main --media-seek-repeat 0.30
python -m hand_gesture_controller.main --overlay
python -m hand_gesture_controller.main --model-path C:\path\to\hand_landmarker.task
```

Nota MediaPipe: le versioni recenti per Python 3.13 usano la Tasks API e
richiedono il file `hand_landmarker.task`. Il comando
`python -m hand_gesture_controller.download_model` lo scarica nella cartella
`hand_gesture_controller\models`.

## Sicurezza

- PyAutoGUI ha il fail-safe attivo: spostando il mouse in un angolo dello
  schermo l'automazione viene interrotta.
- Usa `--dry-run` o `--paused` finche' le soglie non sono comode.
- In pausa la webcam viene rilasciata di default, cosi' altre app possono
  usarla. Usa `--keep-camera-on-pause` solo se vuoi mantenerla aperta.
- ESC chiude l'app solo quando la finestra di debug e' attiva.
- Con `--no-debug`, usa Ctrl+C nel terminale per fermare il programma.

## Webcam occupata

Su Windows molte webcam fisiche non possono essere usate da piu' app insieme.
Se Discord, browser, Meet, Teams o OBS stanno usando la camera, questa app non
crasha: mostra una schermata informativa, stampa un messaggio in console e
riprova automaticamente ogni pochi secondi.

Quando la camera non e' disponibile, la finestra debug mostra:

- `Camera unavailable`
- `Close other apps using the webcam`
- `Press SPACE to retry/resume`
- `Press ESC to exit`

Comportamento:

- se la webcam non si apre, viene subito rilasciata;
- se non produce frame validi, viene rilasciata e ritentata;
- `SPACE` in stato di errore forza un retry immediato;
- `SPACE` in stato normale mette in pausa e rilascia la webcam;
- un secondo `SPACE` prova a riaprire la webcam;
- `--camera-index N` seleziona un'altra camera;
- `--camera-retry-interval 2.5` cambia l'intervallo di retry;
- `--camera-backend 700` permette di passare un backend OpenCV, per esempio
  `700` corrisponde a `cv2.CAP_DSHOW` su Windows ed e' il default del progetto.
- se l'indice scelto non produce frame validi, l'app prova automaticamente gli
  indici `0,1,2,3,4`. Questo evita di usare per errore `OBS Virtual Camera`
  come input quando la webcam fisica e' finita sull'indice successivo.
- `--no-camera-fallback` disattiva questa ricerca automatica.
- `--camera-fallback-indices 1,2,3` personalizza gli indici da provare.

## Virtual camera

Il controller puo' pubblicare automaticamente il feed della webcam fisica su
una webcam virtuale. Il flusso corretto e':

```text
webcam fisica -> GestureTracker -> virtual camera -> Discord/browser/Meet/Teams
```

Questo permette a Discord o al browser di usare la camera virtuale mentre il
controller resta proprietario della webcam fisica per il tracking. Non permette
pero' di leggere una webcam fisica gia' occupata da Discord: in quel caso bisogna
chiudere Discord, avviare il controller e poi scegliere la virtual camera dentro
Discord.

La pubblicazione virtuale e' attiva di default. Per disattivarla:

```powershell
python -m hand_gesture_controller.main --no-virtual-camera
```

Prerequisito Windows: deve esistere un driver/device virtuale supportato da
`pyvirtualcam`, per esempio OBS Virtual Camera o Unity Capture. Per preparare
OBS Virtual Camera nel setup locale, avvia PowerShell come amministratore e
usa:

```powershell
.\scripts\install_virtual_camera.ps1
```

Lo script installa OBS Studio, registra i moduli DirectShow OBS Virtual Camera
a 64 bit e 32 bit, e installa `pyvirtualcam`. Da quel momento l'app puo'
scrivere nel device virtuale e le altre applicazioni possono selezionare
`OBS Virtual Camera`.

Opzioni utili:

- `--virtual-camera-device "OBS Virtual Camera"`: seleziona il device virtuale.
- `--virtual-camera-backend obs`: forza il backend `pyvirtualcam`.
- di default la finestra debug resta specchiata, ma `OBS Virtual Camera` esce
  non specchiata. Usa `--virtual-camera-mirror` solo se vuoi specchiare anche
  l'output virtuale.
- `--virtual-camera-width 1280 --virtual-camera-height 720`: forza la
  risoluzione del feed virtuale.
- `--virtual-camera-fps 30`: imposta il frame rate target.

Il relay usa una coda lunga un solo frame: se una app esterna rallenta, il
controller scarta frame vecchi e mantiene il tracking reattivo.

## Regole anti-falsi positivi

- Ctrl+C e Ctrl+V richiedono una durata minima della gesture.
- Copia e incolla hanno cooldown dedicato.
- La stessa gesture non viene ripetuta mentre resta mantenuta.
- Il puntatore usa zona attiva centrale, smoothing esponenziale e dead zone.
- La finestra di debug mostra gesture, stato, mano rilevata e ultima azione.
- Di default vengono rilevate fino a 2 mani. La mano che fa pinch o movimento
  diventa la mano primaria per il puntatore, mentre le combo a due mani hanno
  priorita' sui comandi singoli.
- Se la webcam e' in modalita' mirror, le etichette Left/Right vengono invertite
  per mostrare la destra/sinistra reali dell'utente.
- Quando una mano sparisce per pochi frame mentre l'altra resta visibile, viene
  mantenuta temporaneamente come `hold` per evitare lampeggi nelle gesture a
  due mani. Se le mani si coprono completamente, il modello puo' comunque
  vederle come una sola mano.

## Mouse mode e azioni

La mano destra e' riservata al mouse. La mano sinistra e le combo a due mani
sono usate per controlli e macro. Il mouse mode puo' essere spento/acceso con
il pugno sinistro mantenuto oppure con una gesture custom assegnata all'azione
`toggle_mouse`.

Su Windows, in modalita' reale, quando il mouse mode e' acceso l'app installa
un hook temporaneo che blocca gli eventi del mouse fisico e lascia passare gli
eventi generati dall'app. In questo modo l'air mouse prende priorita' rispetto
al mouse collegato. Per disattivare questo comportamento:

```powershell
python -m hand_gesture_controller.main --no-pointer-lock
```

Il puntatore viene mappato sul desktop virtuale completo di Windows, quindi
funziona anche con piu' monitor e con schermi posizionati a sinistra/sopra il
monitor principale.

Mappatura schermo:

- `--screen all`: usa tutto il desktop virtuale.
- `--screen primary`: usa solo il monitor principale.
- `--screen 1`, `--screen 2`, ...: usa un monitor specifico.
- `--screen-rect left,top,width,height`: imposta un rettangolo manuale.

Sensibilita':

- `--pointer-sensitivity 1.0`: neutra.
- `--pointer-sensitivity 0.7`: piu' lenta e precisa vicino al centro, ma
  raggiunge comunque tutti i bordi dello schermo.
- `--pointer-sensitivity 1.3`: piu' rapida.
- `--smoothing-alpha`: piu' alto = segue piu' veloce, piu' basso = meno tremolio.
- `--dead-zone`: ignora micro-movimenti in pixel.
- `--active-zone`: restringe o allarga l'area utile della webcam.

## Overlay e click stabile

L'HUD trasparente e click-through sul desktop e' disattivato di default. Per
mostrarlo:

```powershell
python -m hand_gesture_controller.main --overlay
```

Durante click sinistro, doppio click e click destro il puntatore viene
temporaneamente ancorato per circa 120 ms. Questo evita che il click scappi
mentre abbassi medio o anulare. Se il medio resta abbassato abbastanza da
iniziare un drag, l'ancoraggio viene rilasciato e il puntatore torna a muoversi
normalmente per selezionare o trascinare.

Le azioni sono configurate in:

```text
hand_gesture_controller/profiles/default_actions.json
```

Esempio binding:

```json
{
  "name": "left_v_paste",
  "enabled": true,
  "gesture": "v_sign",
  "hands": ["Left"],
  "hold_seconds": 0.45,
  "cooldown_seconds": 1.0,
  "priority": 60,
  "action": { "type": "hotkey", "keys": ["ctrl", "v"] }
}
```

Azioni supportate:

- `hotkey`: invia una combinazione, per esempio `["ctrl", "c"]`.
- `key`: preme un singolo tasto.
- `text`: scrive testo.
- `toggle_mouse`, `mouse_on`, `mouse_off`: gestiscono il mouse mode.
- `macro`: esegue una lista di azioni in sequenza.

## Registrazione pose statiche

Con la finestra debug attiva:

| Tasto | Effetto |
| --- | --- |
| R | Registra la posa corrente come `custom_001`, `custom_002`, ... |
| 1 | Registra la posa corrente come `custom_copy` e la collega a Ctrl+C |
| 2 | Registra la posa corrente come `custom_paste` e la collega a Ctrl+V |
| 3 | Registra la posa corrente come `custom_toggle_mouse` |

La mano sinistra viene preferita per la registrazione; se non e' presente, viene
usata la prima mano tracciata. Le pose custom vengono salvate in:

```text
hand_gesture_controller/profiles/custom_gestures.json
```

Quando una posa custom viene riconosciuta, compare nella label debug tra
parentesi quadre, per esempio `[custom_copy]`.

## Struttura

```text
hand_gesture_controller/
|-- main.py                   # avvio, parsing argomenti, loop principale
|-- config.py                 # dataclass di configurazione e default
|-- settings_store.py         # impostazioni da settings.json
|-- camera.py                 # apertura webcam e riprova
|-- camera_manager.py         # indici di fallback
|-- virtual_camera.py         # relay verso OBS Virtual Camera
|-- hand_tracker.py           # MediaPipe hand landmarker
|-- gesture_detector.py       # dita estese, pinch, pose discrete
|-- pose_templates.py         # pose statiche registrate a runtime
|-- smoothing.py              # smoothing esponenziale
|-- pointer_stabilizer.py     # blocco puntatore durante i click
|-- binding_engine.py         # gesture -> evento azione
|-- action_profile.py         # profili azione da JSON
|-- action_runner.py          # esecuzione delle azioni
|-- state_machine.py          # pausa, mouse mode
|-- mouse_controller.py       # movimento e click reali
|-- right_hand_mouse.py       # logica mouse della mano destra
|-- physical_mouse_guard.py   # priorita' sull'air mouse
|-- keyboard_controller.py    # tasti e scorciatoie
|-- media_control.py          # sessione media Windows + fallback tasti
|-- media_gestures.py         # gesture del pugno per i media
|-- screen_context.py         # riconoscimento contesto media
|-- desktop_overlay.py        # HUD click-through opzionale
|-- download_model.py         # scarica hand_landmarker.task
|-- profiles/                 # azioni e gesture personalizzate
|-- requirements.txt
`-- README.md
```

Le soglie principali sono in `config.py`: modifica prima quelle se il pinch,
il pugno o la gesture di incolla risultano troppo sensibili.

## Gesture media player

Quando l'app rileva un contesto media, le gesture con il pugno destro
prendono priorita' rispetto ai binding normali. Il contesto e' una finestra in
primo piano che sembra un player, oppure una sessione media di Windows attiva:
in questo secondo caso i comandi funzionano anche con il player in background.

| Gesture | Azione |
| --- | --- |
| Pugno destro fermo mantenuto | Play / pausa |
| Pugno destro che scorre verso destra | Avanti, ripetuto finche' il pugno resta chiuso |
| Pugno destro che scorre verso sinistra | Indietro, ripetuto finche' il pugno resta chiuso |

Funziona con player desktop riconosciuti dal processo, per esempio VLC/mpv, e
con browser quando il titolo della scheda contiene parole video come YouTube,
Netflix, Twitch, Vimeo, Prime Video, player, video, watch o stream.
I comandi passano prima dalla sessione media di Windows (Windows Media
Transport Controls via WinRT): play/pausa agisce sul player reale e il seek
sposta la riproduzione di `native_seek_seconds` secondi, 10 per default, anche
se la finestra non e' in primo piano.

Se il player non espone una sessione media, l'app ricade sui tasti: su YouTube
usa le scorciatoie `J/K/L`, altrove `Freccia sinistra`, `Spazio`,
`Freccia destra`. La riga `action` della finestra di debug dice quale strada e'
stata usata, `native seek forward` oppure `key seek forward`.

Comandi utili:

```powershell
python -m hand_gesture_controller.main --no-media-gestures
python -m hand_gesture_controller.main --no-native-media
python -m hand_gesture_controller.main --media-swipe-threshold 0.18
python -m hand_gesture_controller.main --media-pause-hold 0.65
python -m hand_gesture_controller.main --media-seek-repeat 0.30
python -m hand_gesture_controller.main --media-window-check-interval 0.25
```

Per avanti/indietro il comando continua a ripetersi finche' tieni il pugno
destro chiuso. Per play/pausa devi invece rilasciare il pugno prima di inviare
un altro play/pausa, cosi' non rimbalza tra i due stati.
