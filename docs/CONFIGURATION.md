# Configurazione

## Le tre fonti e la loro precedenza

1. I default nel codice, in `hand_gesture_controller/config.py`.
2. Il file JSON delle impostazioni, che sovrascrive i default.
3. Gli argomenti da riga di comando, che sovrascrivono il file.

Un campo assente dal file mantiene il default; un file assente o illeggibile non
e' un errore, si usano i default.

## File impostazioni

```text
hand_gesture_controller/settings.json
```

Non viene creato automaticamente e non e' versionato. Il repository include un
esempio completo con tutti i campi e i valori di default:

```text
hand_gesture_controller/settings.example.json
```

Per partire:

```powershell
copy .\hand_gesture_controller\settings.example.json .\hand_gesture_controller\settings.json
```

Per usare un file diverso: `--settings path\del\file.json`.

Per rigenerare l'esempio dopo aver aggiunto campi al codice:

```powershell
python -m hand_gesture_controller.settings_store
```

## Parametri principali

### pointer

| Campo | Descrizione |
| --- | --- |
| `sensitivity` | Guadagno del puntatore; 1.0 neutro, sotto piu' preciso, sopra piu' rapido |
| `smoothing_alpha` | Smoothing esponenziale; alto segue di piu', basso trema di meno |
| `dead_zone_px` | Micro-movimenti ignorati, in pixel |
| `active_zone_*` | Area utile della webcam, normalizzata 0..1 |

### media_gesture

| Campo | Descrizione |
| --- | --- |
| `hand` | Mano che comanda i media; default `Right` |
| `use_native_media_controls` | Usa la sessione media di Windows invece dei soli tasti |
| `prefer_native_media_context` | Considera media anche una sessione Windows attiva, non solo la finestra in primo piano |
| `native_seek_seconds` | Secondi di salto per ogni seek nativo |
| `swipe_threshold` | Spostamento minimo del pugno per un seek |
| `swipe_max_seconds` | Oltre questa durata il movimento non e' piu' uno swipe |
| `pause_hold_seconds` | Quanto tenere il pugno fermo per play/pausa |
| `still_threshold` | Quanto puo' muoversi il pugno restando "fermo" |
| `seek_repeat_seconds` | Intervallo di ripetizione di avanti/indietro |
| `action_cooldown_seconds` | Attesa minima tra due azioni media |
| `play_pause_key`, `seek_forward_key`, `seek_backward_key` | Tasti usati quando la sessione nativa non risponde |
| `browser_processes`, `player_processes`, `browser_title_keywords` | Come viene riconosciuto un contesto media |

### gesture

| Campo | Descrizione |
| --- | --- |
| `finger_extension_margin` | Margine per considerare un dito esteso |
| `finger_tap_min_seconds` | Durata minima di un tocco perche' valga come click |
| `click_max_seconds` | Oltre questa durata il dito abbassato diventa drag |
| `click_freeze_seconds` | Puntatore bloccato dopo un click, per non trascinare |
| `double_click_seconds` | Finestra per il doppio click |
| `right_click_hold_seconds` | Durata minima del click destro |
| `drag_hold_seconds` | Durata minima per iniziare un trascinamento |
| `copy_hold_seconds`, `paste_hold_seconds` | Durata delle gesture copia e incolla |
| `command_cooldown_seconds` | Attesa minima tra due comandi |
| `pinch_threshold` | Distanza sotto la quale il pinch e' chiuso |

### camera

| Campo | Descrizione |
| --- | --- |
| `index` | Camera preferita |
| `fallback_indices` | Indici provati se quella preferita non da' frame validi |
| `backend` | Backend OpenCV |
| `mirror` | Immagine specchiata |
| `release_on_pause` | Rilascia la webcam in pausa |

Restano `virtual_camera`, `tracker` e `runtime`: i campi e i default sono tutti
in `settings.example.json`.

## Profili gesture e azioni

Sono file separati dalle impostazioni:

- `hand_gesture_controller/profiles/default_actions.json`: quale gesture esegue quale azione.
- `hand_gesture_controller/profiles/custom_gestures.json`: le pose statiche registrate con `r`, `1`, `2`, `3`.

Si possono sostituire con `--action-profile` e `--gesture-profile`.
