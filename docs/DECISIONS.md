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
