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
