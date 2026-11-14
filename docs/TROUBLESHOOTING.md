# Troubleshooting

## La webcam non si apre

Cause tipiche: un'altra applicazione la sta usando, l'indice non e' quello
giusto, oppure il backend OpenCV non restituisce frame validi.

La finestra di debug mostra sempre lo stato della camera nella prima riga. Con
la camera non disponibile, `SPACE` forza un nuovo tentativo invece di mettere in
pausa.

```powershell
python -m hand_gesture_controller.main --camera-index 1
python -m hand_gesture_controller.main --camera-fallback-indices 0,1,2,3,4
```

In pausa la webcam viene rilasciata, quindi si puo' cederla a un'altra app senza
chiudere il controller.

## OBS Virtual Camera non parte

Verificare che OBS Studio sia installato e che OBS Virtual Camera sia registrata
nel sistema, poi avviare con `--virtual-camera-backend obs`. Lo stato compare
nella seconda riga della finestra di debug.

Se un altro processo riesce ad aprire OBS Virtual Camera mentre l'app e' attiva,
il relay non e' partito.

## Il puntatore non si muove

Il mouse mode e' probabilmente spento: tenere chiuso il pugno sinistro per 0.8
secondi. Lo stato si legge nella finestra di debug alla riga `mouse`.

Se l'app e' avviata con `--dry-run` non invia nulla al sistema per scelta.

## Il mouse fisico non risponde piu'

Con il mouse mode acceso l'app blocca il mouse fisico per dare priorita' all'air
mouse. Spegnere il mouse mode, oppure avviare con `--no-pointer-lock`.

## Il mouse si muove troppo o troppo poco

```powershell
python -m hand_gesture_controller.main --pointer-sensitivity 0.7 --smoothing-alpha 0.4 --dead-zone 3
```

Con piu' monitor, controllare la mappatura dello schermo: `--screen all`,
`--screen primary`, `--screen 2`, oppure `--screen-rect left,top,width,height`.

## Il puntatore si ferma mentre guardo un video

E' voluto: finche' tieni il pugno destro chiuso in un contesto media, quel pugno
appartiene alle gesture video. Riapri la mano e il puntatore riparte. I comandi
della mano sinistra, toggle del mouse compreso, restano sempre attivi.

Se da' fastidio, le gesture media si spengono con `--no-media-gestures`, oppure
si limitano al player in primo piano mettendo `prefer_native_media_context` a
`false` nelle impostazioni.

## Chiudo la finestra e l'app sembra riavviarsi

Era il comportamento prima della correzione: OpenCV non ferma il programma
quando si chiude una finestra, e il frame dopo la ricreava. Ora la X chiude
l'app come `ESC`. Se succede ancora, la finestra chiusa non e' quella di debug
ma l'overlay: quello si spegne togliendo `--overlay`.

## Non riesco a spostare la finestra del tracker

Con il mouse mode acceso il mouse fisico viene bloccato, ma non sopra le
finestre dell'app: li' deve passare, altrimenti il trascinamento della finestra
non puo' terminare e l'app si pianta.

Se succede ancora, avviare con `--no-pointer-lock`, che disattiva del tutto il
blocco del mouse fisico.

## Le gesture video non partono

Verificare, in ordine:

- la mano usata e' la destra (campo `hand`);
- la riga `media` della finestra di debug dice `on`, non `off`: se dice `off` l'app
  non ha riconosciuto un contesto media;
- il player e' tra quelli riconosciuti, altrimenti aggiungerlo a
  `player_processes` o `browser_title_keywords`.

## Il video va avanti ma di troppo o troppo poco

Con la sessione media nativa il salto e' esattamente `native_seek_seconds`
secondi. Se invece l'app sta usando i tasti, il salto dipende dal player: la
riga `action` della finestra di debug distingue i due casi, `native seek forward`
oppure `key seek forward`.

Per forzare i soli tasti: `--no-native-media`.

## Il pugno viene riconosciuto a sprazzi

Alzare `pause_hold_seconds` e `swipe_threshold` nella sezione `media_gesture`.
Per le pose discrete agire invece su `hold_seconds` della singola associazione in
`profiles/default_actions.json`. Valori piu' alti riducono i falsi positivi e
aumentano la latenza.

## Le impostazioni del file JSON vengono ignorate

Controllare che il file sia `hand_gesture_controller/settings.json`, o che il
percorso passato a `--settings` sia corretto: un file assente o con JSON non
valido viene ignorato in silenzio e si usano i default.

Ricordare la precedenza: gli argomenti da riga di comando vincono sempre sul file.
