# Decisions

## 2026-07-05

- Creata struttura portfolio locale.
- Repository GitHub privato creato: `https://github.com/carminegallina/GestureTracker`.
- Push iniziale su `origin/main` completato.
- Importata la sorgente da una cartella di lavoro locale esterna al portfolio.
- Lo scaffold precedente e' stato copiato in un backup locale fuori dal repository.
- La sorgente aveva Git inizializzato ma senza commit; il repository autorevole diventa quello nel portfolio.
- Log e cache non sono stati importati.
- `hand_gesture_controller/models/hand_landmarker.task` resta ignorato da Git.

## 2026-11-14

- Scelta la versione in questo repository come base per la pubblicazione: 39 test passati
  contro gli 8 della vecchia repository pubblica `hand-gesture-desktop-controller`.
- Rimossi i path personali da README, DECISIONS e PROJECT_BRIEF: il repository andra' pubblico
  e i percorsi locali non devono comparire.
- I path personali restano nei commit fino a `8062690`; la pubblicazione partira' da una
  storia nuova, perche' i commit attuali coprono solo scaffold e migrazione.
- Nome pubblico confermato: `GestureTracker`.
- Licenza scelta: MIT.
- `CLAUDE.md` e `AGENTS.md` esclusi dal repository: sono istruzioni di processo, non
  documentazione del progetto. Restano in locale e sono ignorati da Git.
- La vecchia repository pubblica `hand-gesture-desktop-controller` viene eliminata:
  0 star, 0 fork, nessun riferimento esterno.
- Prima dell'eliminazione, la vecchia repository pubblica e' stata salvata come mirror Git
  in `_archive/hand-gesture-desktop-controller.git` (ignorato da Git): la fase 3 recupera
  i file da li', non da GitHub.

## 2026-11-14 (fase 3)

- Recuperato `media_control.py` dal mirror: i comandi media passano dalla sessione
  media di Windows (WinRT) e ricadono sui tasti solo se non risponde. Prima l'app
  mandava solo tasti, quindi richiedeva il player in primo piano.
- `MediaGestureController` riceve ora un `HybridMediaController` invece della tastiera:
  la scelta nativo/tasti sta in un posto solo. `MediaGestureUpdate.action` porta
  l'etichetta della strada usata, utile nella finestra di debug.
- Reintrodotta la configurazione su file con `settings_store.py`. I default del parser
  argomenti arrivano dal file caricato, non da `DEFAULT_CONFIG`: cosi' la precedenza e'
  default del codice, file, riga di comando. Senza questo accorgimento gli argomenti,
  che hanno sempre un valore, avrebbero sovrascritto il file a ogni avvio.
- `settings.example.json` viene generato dal codice con
  `python -m hand_gesture_controller.settings_store`, non scritto a mano: non puo'
  divergere dalle dataclass.
- `SettingsStore.load` non crea il file al primo avvio, al contrario della versione
  vecchia: l'esempio si copia a mano quando serve.
- Non sono stati recuperati `tray_app.py`, `hotkeys.py`, `runtime_state.py` e
  `debug_settings_panel.py`: la versione attuale non ha tray ne' scorciatoie globali,
  e il pannello richiede `runtime_state`. Restano nel mirror.
- I 6 documenti del mirror sono stati riscritti sul codice attuale invece di essere
  copiati: descrivevano tray, scorciatoie globali e pannello impostazioni che qui non
  esistono. `PORTFOLIO_SUMMARY.md` non e' stato ripreso, perche' README e
  PROJECT_BRIEF coprono gia' quel contenuto.
- Aggiunto `requirements-dev.txt` con pytest, e i pacchetti `winrt-*` ai requirements:
  senza di essi i comandi media funzionano, ma solo via tasti.

## 2026-11-14 (correzione)

- Quando le gesture media consumano il frame, ai binding viene ora sottratta solo la
  mano che i media usano, non l'intera lista di osservazioni. Prima il binding engine
  riceveva una lista vuota, quindi il toggle del mouse con la mano sinistra non
  arrivava mai: il blocco era li', non nell'ampiezza del contesto media.
- Un primo tentativo aveva ristretto il contesto alla finestra in primo piano
  (`prefer_native_media_context` a `false`) e richiesto una sessione in riproduzione.
  Era sbagliato su entrambi i punti: mentre si usa il tracker la finestra davanti e'
  la sua, non quella del player, quindi le gesture media non si armavano mai; e con il
  requisito "in riproduzione" il pugno avrebbe messo in pausa senza poter piu' far
  ripartire. Entrambe le condizioni sono state tolte.
- `PhysicalMouseGuard` non blocca piu' il mouse fisico sopra le finestre dell'app.
  Trascinare la finestra del tracker apre un loop modale di Windows che ferma il loop
  principale, e con gli eventi fisici ingoiati il trascinamento non poteva terminare:
  l'app si piantava e veniva chiusa come non rispondente.
- La X della finestra di debug ora chiude l'app. OpenCV non ferma il programma quando
  si chiude una finestra: il loop proseguiva e il successivo `imshow` la ricreava,
  percio' sembrava che l'app si riavviasse. Il loop controlla `WND_PROP_VISIBLE`,
  verificato su opencv 5.0: 1.0 con la finestra aperta, 0.0 dopo la chiusura.
- Aggiunto `pyproject.toml` con l'entry point `gesturetracker`. Le dipendenze restano
  nel requirements e vengono lette da `[tool.setuptools.dynamic]`, per non tenerle
  allineate in due posti.
- `DEFAULT_SETTINGS_PATH` era relativo alla cartella di lavoro, mentre profili e modello
  erano gia' relativi al package. Avviando l'app da un'altra cartella il file delle
  impostazioni non veniva trovato, in silenzio: ora segue la stessa regola degli altri.
- Consigliata l'installazione modificabile (`pip install -e .`): l'app scrive i propri
  profili dentro il package, che con un'installazione normale starebbe in site-packages.
