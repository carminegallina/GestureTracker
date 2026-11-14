# Guida utente

## Principio operativo

Il tracking delle mani resta sempre attivo, ma i comandi al sistema partono solo
quando il mouse mode e' acceso. Cosi' la webcam puo' restare aperta senza
rischiare movimenti o click involontari.

Il mouse mode si accende e si spegne con il pugno sinistro mantenuto, oppure con
una gesture personalizzata associata all'azione `toggle_mouse`.

## Tasti della finestra di debug

I tasti funzionano solo quando la finestra della camera e' in primo piano: non
sono scorciatoie globali.

| Tasto | Azione |
| --- | --- |
| `SPACE` | Pausa / ripresa; se la webcam non e' disponibile forza un nuovo tentativo |
| `ESC` | Chiude l'applicazione, come la X della finestra |
| `r` | Registra una posa statica generica |
| `1` `2` `3` | Registrano le pose `custom_copy`, `custom_paste`, `custom_toggle_mouse` |

In pausa la webcam viene rilasciata, cosi' altre applicazioni possono usarla.
Per avviare l'app gia' in pausa: `--paused`. Per nascondere la finestra di
debug: `--no-debug`.

## Mouse con la mano destra

La mano destra e' riservata al puntatore.

| Gesture | Azione |
| --- | --- |
| Indice visibile o mano aperta | Muove il puntatore |
| Medio abbassato una volta | Click sinistro |
| Medio abbassato due volte | Doppio click |
| Medio tenuto abbassato | Trascina o seleziona |
| Anulare abbassato | Click destro |

Con il mouse mode acceso, su Windows l'app installa un hook temporaneo che
blocca il mouse fisico e lascia passare solo gli eventi generati dall'app, cosi'
i due puntatori non si contendono il cursore. Per disattivarlo: `--no-pointer-lock`.

## Comandi con la mano sinistra

| Gesture | Durata | Azione |
| --- | --- | --- |
| Pugno mantenuto | 0.8 s | Accende/spegne il mouse mode |
| Pollice su | 0.45 s | Ctrl+C |
| Segno V | 0.45 s | Ctrl+V |
| Due pugni | 0.5 s | Ctrl+C |
| Due segni V | 0.5 s | Ctrl+V |

Le associazioni stanno in `hand_gesture_controller/profiles/default_actions.json`
e si possono cambiare senza toccare il codice.

## Gesture video

Funzionano solo con la mano destra e solo quando l'app rileva un contesto media:
una finestra di player o browser riconosciuta, oppure una sessione media di
Windows attiva. Il secondo caso serve davvero, perche' mentre usi il tracker la
finestra davanti e' quasi sempre la sua, non quella del player.

Finche' le gesture media sono armate il pugno destro appartiene a loro, quindi
il puntatore resta sospeso mentre lo tieni chiuso. La mano sinistra continua a
funzionare normalmente, toggle del mouse compreso.

| Gesture | Azione |
| --- | --- |
| Pugno fermo | Play / pausa |
| Pugno trascinato a destra | Avanzamento, ripetuto finche' il pugno resta chiuso |
| Pugno trascinato a sinistra | Riavvolgimento, ripetuto finche' il pugno resta chiuso |

Play/pausa parte una sola volta: per inviarlo di nuovo bisogna riaprire la mano.

I comandi passano prima dalla sessione media di Windows, che agisce sul player
reale anche se non e' in primo piano e sposta la riproduzione di
`native_seek_seconds` secondi invece di affidarsi a quanto salta il player con
la freccia. Se il player non espone una sessione media, l'app
ricade sui tasti: `space`, `right`, `left`, e su YouTube `k`, `l`, `j`.

Per usare solo i tasti: `--no-native-media`. Per spegnere del tutto le gesture
video: `--no-media-gestures`.

## Overlay

L'HUD trasparente sul desktop e' disattivato di default. Si accende con
`--overlay`.
