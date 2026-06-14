# Tedesco in 60 giorni

Sito statico (HTML/CSS/JS puro, **nessun framework, nessun build step**) che ospita un
corso di tedesco di **60 giorni** per principianti italiani, fino al livello **A1**.
Il corso è diviso in **6 fasi da 10 giorni**.

🔗 Funziona sia pubblicato su **GitHub Pages** sia aperto in locale con doppio clic su
`index.html` (tutti i link sono relativi).

## Struttura del sito

| File | Cosa contiene |
|------|---------------|
| `index.html` | Copertina con le 6 fasi |
| `tedesco-fase-1.html` … `tedesco-fase-6.html` | Una pagina per fase (elenco giorni + mini-quiz) |
| `tedesco-giorno-01.html` … `tedesco-giorno-60.html` | Una pagina per giorno (spiegazione, esempi, trucco, esercizio) |

In totale **67 file HTML** (1 + 6 + 60). Mappa giorni → fase:
1–10 → Fase 1, 11–20 → Fase 2, 21–30 → Fase 3, 31–40 → Fase 4, 41–50 → Fase 5, 51–60 → Fase 6.

## Come funziona (sorgenti vs. output)

Le pagine HTML sono **generate** da uno script, così il corso resta facile da aggiornare:

- **`course.json`** — la fonte di verità: titoli, fasi, giorni, esempi e quiz.
- **`generate.py`** — legge `course.json` e scrive i 67 file HTML applicando due template
  (pagina di fase e pagina di giorno) più l'`index.html`.

Ogni pagina è **autosufficiente**: CSS e JS sono inline nel file. La duplicazione del CSS
è voluta — è la scelta più robusta per pagine statiche apribili anche singolarmente.

### Rigenerare il sito

```bash
python3 generate.py
```

Lo script è **idempotente**: rilanciarlo riscrive gli stessi 67 file. Richiede solo
Python 3 (nessuna dipendenza esterna). Dopo aver modificato `course.json`, rigenera e
committa sia i sorgenti sia gli HTML.

## Pubblicare su GitHub Pages

Tutti i file sono nella **root** del repository. Per pubblicare:

1. Vai su **Settings → Pages** del repository.
2. In **Build and deployment → Source** scegli **Deploy from a branch**.
3. Seleziona il branch `main` e la cartella **`/ (root)`**, poi **Save**.
4. Dopo qualche minuto il sito sarà online all'indirizzo
   `https://<utente>.github.io/<repository>/`.

> Se preferisci pubblicare da `/docs`, sposta i 67 file HTML nella cartella `docs/`,
> imposta in `generate.py` la cartella di output su `docs/` e scegli **`/docs`** come
> source in Settings → Pages.

## Ascolto in tedesco (audio)

Le pagine di giorno e di fase includono l'ascolto delle frasi tedesche tramite la
**Web Speech API** del browser (nessun file audio, nessuna dipendenza, nessuna API key):

- 🔊 su ogni frase tedesca + **"Ascolta tutto"** per leggerle in sequenza.
- **Velocità** selezionabile: *Normale* / *Lenta 🐢*.
- **Voce** selezionabile tra le voci tedesche installate sul dispositivo (con etichetta
  *(f)*/*(m)* quando il nome è riconoscibile); il menu appare solo se c'è più di una voce.
- Le preferenze di velocità e voce si conservano tra le pagine via **parametri URL**
  (`?rate=...&voice=...`), senza usare `localStorage`: i link interni le propagano da soli.
- Tutti i controlli audio **spariscono** se il browser non supporta la sintesi vocale.

> La qualità della voce dipende dal dispositivo. **Nota su iPad/Safari:** iOS espone alla
> Web Speech API solo una voce di sistema (di solito "Anna"), quindi lì non si possono
> scegliere voci diverse. Per audio uniforme e di qualità ovunque, usa gli MP3 pre-generati
> (sotto): le pagine li riproducono automaticamente quando presenti — iPad compreso — e
> ripiegano sulla voce del browser quando mancano.

### Audio MP3 pre-generati (opzionale, consigliato per iPad)

Per avere voci neural identiche su ogni dispositivo (e funzionanti su iPad), genera i file
audio con **`generate_audio.py`** (usa [`edge-tts`](https://github.com/rany2/edge-tts):
gratuito, **senza API key**):

```bash
pip install edge-tts
python3 generate_audio.py                       # voce femminile (de-DE-KatjaNeural)
# python3 generate_audio.py --voice de-DE-ConradNeural   # voce maschile
git add audio/ && git commit -m "Audio MP3" && git push origin main
```

- I file finiscono in `audio/` con nomi `de-<hash>.mp3` calcolati dallo stesso hash usato da
  `generate.py`, quindi le pagine li trovano senza configurazione.
- È **idempotente**: rilanciandolo genera solo i file mancanti (`--force` per rifarli tutti).
- Serve solo una macchina con Python, Internet e orologio di sistema corretto.

> **Rigenera gli HTML dopo gli MP3.** Quando tutte le frasi di una pagina hanno già il loro
> MP3, il menu di scelta voce del browser non avrebbe effetto (l'MP3 neural vince sempre),
> quindi `generate.py` lo nasconde su quelle pagine. Questo controllo guarda i file presenti
> in `audio/`, perciò l'ordine consigliato è: `generate_audio.py` → poi `python3 generate.py`.
> Se un MP3 manca, su quella pagina il menu resta visibile come fallback.

## Design e contenuti

- Palette geometrica/Bauhaus; ogni fase ha un colore-accento dedicato.
- Font **Archivo** + **Inter** via Google Fonts, con fallback di sistema: il sito resta
  leggibile anche se i font non caricano.
- Mobile-first, responsive, rispetta `prefers-reduced-motion`.
- Nessun uso di `localStorage`/`sessionStorage`.
- Il tedesco degli esempi in `course.json` è verificato: aggiornalo lì, mai a mano negli HTML.

## Licenza / uso

Materiale didattico libero. Buono studio — **viel Erfolg!** 🇩🇪
