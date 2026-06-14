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

## Design e contenuti

- Palette geometrica/Bauhaus; ogni fase ha un colore-accento dedicato.
- Font **Archivo** + **Inter** via Google Fonts, con fallback di sistema: il sito resta
  leggibile anche se i font non caricano.
- Mobile-first, responsive, rispetta `prefers-reduced-motion`.
- Nessun uso di `localStorage`/`sessionStorage`.
- Il tedesco degli esempi in `course.json` è verificato: aggiornalo lì, mai a mano negli HTML.

## Licenza / uso

Materiale didattico libero. Buono studio — **viel Erfolg!** 🇩🇪
