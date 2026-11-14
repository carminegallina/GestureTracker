# Sviluppo

## Test

```powershell
python -m pytest tests
```

I test non usano webcam, mouse o tastiera reali: le dipendenze di sistema sono
sostituite da fake nei test stessi. Girano quindi anche senza hardware.

La GitHub Action in `.github/workflows/tests.yml` li esegue a ogni push su
`main` e su ogni pull request. Gira su `windows-latest`: i pacchetti `winrt-*`
esistono solo per Windows, quindi su Linux l'installazione fallirebbe.

## Pacchetto e comando

`pyproject.toml` dichiara il package e l'entry point `gesturetracker`, che punta
a `hand_gesture_controller.main:main`. Le dipendenze non sono elencate la': il
campo e' dinamico e legge `hand_gesture_controller/requirements.txt`, cosi' non
vanno tenute allineate in due posti.

I path dei file di dati, profili, impostazioni e modello, si risolvono tutti
rispetto alla cartella del package e non a quella di lavoro: altrimenti il
comando installato, avviato da altrove, non li troverebbe.

## Separazione dei moduli

Tre livelli tenuti distinti, come chiede il progetto:

- riconoscimento: `hand_tracker`, `gesture_detector`, `pose_templates`, `smoothing`, `pointer_stabilizer`;
- input desktop: `mouse_controller`, `keyboard_controller`, `right_hand_mouse`, `physical_mouse_guard`, `media_control`;
- configurazione e UI: `config`, `settings_store`, `action_profile`, `desktop_overlay`, `main`.

`binding_engine` e `state_machine` stanno in mezzo: traducono gesture in azioni
senza sapere come queste vengono eseguite.

## Aggiungere una gesture

1. Se e' una posa statica, registrarla a runtime con `r`, `1`, `2` o `3`: finisce in `profiles/custom_gestures.json`.
2. Se serve una logica nuova, aggiungerla a `gesture_detector`.
3. Associarla a un'azione in `profiles/default_actions.json`.
4. Aggiungere un test in `tests/test_action_bindings.py`.

## Aggiungere un campo di configurazione

1. Aggiungere il campo alla dataclass in `config.py`.
2. Rigenerare l'esempio: `python -m hand_gesture_controller.settings_store`.
3. Se serve anche da riga di comando, aggiungere l'argomento in `build_parser` e passarlo in `config_from_args`.

I default del parser arrivano dal file impostazioni, non da `DEFAULT_CONFIG`:
questo tiene la precedenza default, file, riga di comando.

## Controlli media

`media_control.HybridMediaController` prova prima la sessione media di Windows
via WinRT e ricade sui tasti. Nei test si passa un finto controller nativo,
oppure si costruisce la configurazione con `use_native_media_controls=False`:
in quel caso WinRT non viene nemmeno importato.
